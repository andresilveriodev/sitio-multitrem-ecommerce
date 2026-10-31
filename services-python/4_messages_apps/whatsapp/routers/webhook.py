"""
Webhook Evolution — gateway puro (auth, ack, forward).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from config import settings
from services.chatbot_client import ChatbotClient
from services.dedupe_cache import DedupeCache, RecentEventsBuffer
from services.evolution_parser import (
    ACCEPTED_EVENTS,
    mask_phone,
    normalize_event_name,
    parse_envelope,
    parse_inbound_message,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/webhooks/evolution", tags=["evolution-webhook"])

# Injetados em app.py no startup
chatbot_client: Optional[ChatbotClient] = None
dedupe_cache: Optional[DedupeCache] = None
recent_events: Optional[RecentEventsBuffer] = None


def _verify_secret(
    token: Optional[str],
    x_webhook_secret: Optional[str],
) -> None:
    expected = (settings.EVOLUTION_WEBHOOK_SECRET or "").strip()
    if not expected:
        logger.error("EVOLUTION_WEBHOOK_SECRET não configurado")
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    provided = (token or x_webhook_secret or "").strip()
    if not provided or provided != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _human_status(status: str, detail: str = "") -> str:
    """Traduz status técnico para leitura humana."""
    detail_l = (detail or "").lower()
    if status == "queued":
        return "recebida — aguardando encaminhar ao chatbot"
    if status == "forwarded":
        return "ok — chegou no chatbot"
    if status == "forward_failed":
        if "connection" in detail_l or "connect" in detail_l:
            return "chegou no gateway, mas o chatbot está offline (porta 8010)"
        if "client not ready" in detail_l:
            return "chegou no gateway, mas o cliente do chatbot não iniciou"
        return f"chegou no gateway, falha ao enviar ao chatbot ({detail[:80]})" if detail else (
            "chegou no gateway, falha ao enviar ao chatbot"
        )
    if status == "duplicate":
        return "duplicada — já tinha sido recebida"
    if status == "ignored":
        return f"ignorada ({detail})" if detail else "ignorada"
    if status == "acked":
        return "evento recebido, sem texto para encaminhar"
    if status == "failed":
        return f"erro ao processar ({detail})" if detail else "erro ao processar"
    return status


def _format_horario_br(iso_utc: str) -> str:
    """UTC ISO → horário Brasil (UTC-3) legível."""
    try:
        dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
        # America/Sao_Paulo ≈ UTC-3 (sem depender de zoneinfo no Windows antigo)
        from datetime import timedelta

        local = dt.astimezone(timezone(timedelta(hours=-3)))
        return local.strftime("%d/%m %H:%M:%S")
    except Exception:
        return iso_utc


def _record(
    *,
    event_type: str,
    instance: str,
    status: str,
    message_id: str = "",
    user_masked: str = "",
    detail: str = "",
    msg: str = "",
    push_name: str = "",
) -> None:
    if not recent_events:
        return
    at = datetime.now(timezone.utc).isoformat()
    recent_events.add(
        {
            "at": at,
            "event_type": event_type,
            "instance": instance,
            "status": status,
            "message_id": message_id[:64] if message_id else "",
            "user": user_masked,
            "push_name": (push_name or "")[:80],
            "msg": (msg or "")[:300],
            "detail": detail[:200] if detail else "",
            # linha humana: Horário | Usuário | Msg | situação
            "linha": (
                f"{_format_horario_br(at)} | "
                f"{(push_name + ' · ') if push_name else ''}{user_masked or '—'} | "
                f"{(msg[:120] if msg else '—')} | "
                f"{_human_status(status, detail)}"
            ),
        }
    )


async def _forward_to_chatbot(
    user_id: str,
    text: str,
    metadata: dict[str, Any],
    dedupe_key: str,
) -> None:
    push_name = str(metadata.get("push_name") or "")
    if not chatbot_client:
        logger.error("chatbot_client não inicializado")
        _record(
            event_type=str(metadata.get("raw_event_type", "")),
            instance=str(metadata.get("instance", "")),
            status="forward_failed",
            message_id=str(metadata.get("message_id", "")),
            user_masked=mask_phone(user_id),
            detail="client not ready",
            msg=text,
            push_name=push_name,
        )
        return
    result = await chatbot_client.process_message(
        user_id=user_id,
        message=text,
        metadata=metadata,
    )
    ok = (
        result is not None
        and result.get("success") is not False
        and not result.get("error")
    )
    _record(
        event_type=str(metadata.get("raw_event_type", "")),
        instance=str(metadata.get("instance", "")),
        status="forwarded" if ok else "forward_failed",
        message_id=str(metadata.get("message_id", "")),
        user_masked=mask_phone(user_id),
        detail="" if ok else str((result or {}).get("error", "unknown"))[:200],
        msg=text,
        push_name=push_name,
    )


@router.post("")
@router.post("/")
async def evolution_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    token: Optional[str] = Query(default=None),
    x_webhook_secret: Optional[str] = Header(default=None, alias="X-Webhook-Secret"),
):
    """Recebe eventos Evolution, responde 200 e encaminha mensagens IN ao chatbot."""
    _verify_secret(token, x_webhook_secret)

    try:
        payload = await request.json()
    except Exception:
        _record(event_type="", instance="", status="failed", detail="invalid json")
        return JSONResponse(
            status_code=200,
            content={"accepted": False, "error": "invalid json"},
        )

    if not isinstance(payload, dict):
        _record(event_type="", instance="", status="failed", detail="payload not object")
        return JSONResponse(
            status_code=200,
            content={"accepted": False, "error": "payload must be object"},
        )

    event_type, instance, data = parse_envelope(payload)

    if settings.EVOLUTION_INSTANCE_NAME and instance:
        if instance != settings.EVOLUTION_INSTANCE_NAME:
            _record(
                event_type=event_type,
                instance=instance,
                status="ignored",
                detail="instance mismatch",
            )
            return {"accepted": True, "ignored": True, "reason": "instance mismatch"}

    if event_type and event_type not in ACCEPTED_EVENTS:
        # ainda assim ack — Evolution pode enviar extras
        _record(
            event_type=event_type or normalize_event_name(str(payload.get("event", ""))),
            instance=instance,
            status="ignored",
            detail="event not in allowlist",
        )
        return {"accepted": True, "ignored": True, "reason": "event not handled"}

    if not event_type:
        _record(event_type="", instance=instance, status="failed", detail="missing event")
        return JSONResponse(
            status_code=200,
            content={"accepted": False, "error": "missing event"},
        )

    inbound = parse_inbound_message(event_type, instance, data)

    if not inbound:
        _record(
            event_type=event_type,
            instance=instance,
            status="acked",
            detail="no inbound text to forward",
        )
        return {"accepted": True, "forwarded": False}

    dedupe_key = f"{instance}:{inbound.message_id}" if inbound.message_id else ""
    if dedupe_key and dedupe_cache and dedupe_cache.seen_or_add(dedupe_key):
        _record(
            event_type=event_type,
            instance=instance,
            status="duplicate",
            message_id=inbound.message_id,
            user_masked=mask_phone(inbound.user_id),
            msg=inbound.text,
            push_name=inbound.push_name or "",
        )
        return {"accepted": True, "duplicate": True}

    metadata = {
        "channel": "whatsapp",
        "instance": instance or inbound.instance,
        "message_id": inbound.message_id,
        "raw_event_type": event_type,
        "remote_jid": inbound.remote_jid,
        "push_name": inbound.push_name,
    }

    _record(
        event_type=event_type,
        instance=instance,
        status="queued",
        message_id=inbound.message_id,
        user_masked=mask_phone(inbound.user_id),
        msg=inbound.text,
        push_name=inbound.push_name or "",
    )

    background_tasks.add_task(
        _forward_to_chatbot,
        inbound.user_id,
        inbound.text,
        metadata,
        dedupe_key,
    )

    return {"accepted": True, "forwarded": True}


@router.get("/recent")
async def list_recent(
    token: Optional[str] = Query(default=None),
    x_webhook_secret: Optional[str] = Header(default=None, alias="X-Webhook-Secret"),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Últimos eventos no buffer do gateway (ops / validar túnel)."""
    _verify_secret(token, x_webhook_secret)
    events = recent_events.list(limit) if recent_events else []
    # resumo humano: Horário | Usuário | Msg | situação
    linhas = [e.get("linha") for e in events if e.get("linha")]
    return {
        "count": len(events),
        "resumo": linhas,
        "events": events,
    }
