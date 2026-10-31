"""
Parser mínimo de eventos Evolution API v2 — só extrai o necessário para o gateway.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

# Eventos aceitos (formas normalizadas)
ACCEPTED_EVENTS = {
    "MESSAGES_UPSERT",
    "MESSAGES_UPDATE",
    "MESSAGES_DELETE",
    "CHATS_UPSERT",
    "CHATS_UPDATE",
    "CONTACTS_UPSERT",
    "CONNECTION_UPDATE",
}


def normalize_event_name(raw: Optional[str]) -> str:
    """messages.upsert / MESSAGES_UPSERT / messages_upsert → MESSAGES_UPSERT."""
    if not raw:
        return ""
    name = str(raw).strip().upper().replace(".", "_").replace("-", "_")
    return name


def normalize_phone(jid: Optional[str]) -> str:
    """Extrai dígitos de remoteJid (ex.: 5511999999999@s.whatsapp.net)."""
    if not jid:
        return ""
    local = str(jid).split("@", 1)[0]
    # remove sufixo de device (:XX)
    local = local.split(":", 1)[0]
    digits = re.sub(r"\D", "", local)
    return digits or local


@dataclass
class ParsedInboundMessage:
    event_type: str
    instance: str
    message_id: str
    remote_jid: str
    user_id: str
    text: str
    from_me: bool
    push_name: Optional[str] = None


def _extract_text(message_obj: Any) -> str:
    if not isinstance(message_obj, dict):
        return ""
    # conversation / extendedTextMessage / caption
    if isinstance(message_obj.get("conversation"), str):
        return message_obj["conversation"].strip()
    ext = message_obj.get("extendedTextMessage")
    if isinstance(ext, dict) and isinstance(ext.get("text"), str):
        return ext["text"].strip()
    for media_key in (
        "imageMessage",
        "videoMessage",
        "documentMessage",
        "audioMessage",
    ):
        media = message_obj.get(media_key)
        if isinstance(media, dict):
            caption = media.get("caption")
            if isinstance(caption, str) and caption.strip():
                return caption.strip()
    # buttons / list response
    btn = message_obj.get("buttonsResponseMessage")
    if isinstance(btn, dict):
        selected = btn.get("selectedDisplayText") or btn.get("selectedButtonId")
        if isinstance(selected, str):
            return selected.strip()
    lst = message_obj.get("listResponseMessage")
    if isinstance(lst, dict):
        title = lst.get("title")
        if isinstance(title, str):
            return title.strip()
    return ""


def parse_envelope(payload: dict) -> tuple[str, str, Any]:
    """Retorna (event_type, instance, data)."""
    event_type = normalize_event_name(
        payload.get("event") or payload.get("type") or ""
    )
    instance = str(
        payload.get("instance")
        or payload.get("instanceName")
        or payload.get("destination")
        or ""
    ).strip()
    data = payload.get("data", payload)
    return event_type, instance, data


def parse_inbound_message(
    event_type: str, instance: str, data: Any
) -> Optional[ParsedInboundMessage]:
    """
    Extrai mensagem IN de MESSAGES_UPSERT.
    Evolution pode enviar data como objeto ou lista.
    """
    if event_type != "MESSAGES_UPSERT":
        return None

    items: list[Any]
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # às vezes messages está aninhado
        if isinstance(data.get("messages"), list):
            items = data["messages"]
        else:
            items = [data]
    else:
        return None

    for item in items:
        if not isinstance(item, dict):
            continue
        key = item.get("key") if isinstance(item.get("key"), dict) else {}
        from_me = bool(key.get("fromMe", False))
        if from_me:
            continue
        remote_jid = str(key.get("remoteJid") or item.get("remoteJid") or "")
        if remote_jid.endswith("@g.us"):
            # grupos: ignorar no gateway nesta fase
            continue
        message_id = str(key.get("id") or item.get("id") or "")
        message_obj = item.get("message")
        text = _extract_text(message_obj)
        if not text:
            continue
        user_id = normalize_phone(remote_jid)
        if not user_id:
            continue
        return ParsedInboundMessage(
            event_type=event_type,
            instance=instance,
            message_id=message_id,
            remote_jid=remote_jid,
            user_id=user_id,
            text=text,
            from_me=False,
            push_name=item.get("pushName") if isinstance(item.get("pushName"), str) else None,
        )
    return None


def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 4:
        return "***"
    return f"{phone[:2]}***{phone[-2:]}"
