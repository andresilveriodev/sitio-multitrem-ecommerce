"""
Orquestra envio das listas (colheita, pedidos, compras, rota) via WhatsApp Gateway.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import settings
from db_session import get_db_session
from models.commerce import Collaborator
from routes.colaboradores import _ensure, _roles_from_storage

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/cadastro/whatsapp", tags=["whatsapp-envio"])


class ListaEnvio(BaseModel):
    text: str = ""
    colaborador_ids: List[int] = Field(default_factory=list)


class EnviarListasIn(BaseModel):
    colheita: ListaEnvio = Field(default_factory=ListaEnvio)
    pedidos: ListaEnvio = Field(default_factory=ListaEnvio)
    compras: ListaEnvio = Field(default_factory=ListaEnvio)
    rota: ListaEnvio = Field(default_factory=ListaEnvio)


def _gateway_configured() -> bool:
    return bool(
        (settings.WHATSAPP_GATEWAY_URL or "").strip()
        and (settings.WHATSAPP_GATEWAY_TOKEN or "").strip()
    )


async def _send_one(number: str, text: str) -> Dict[str, Any]:
    base = settings.WHATSAPP_GATEWAY_URL.rstrip("/")
    token = settings.WHATSAPP_GATEWAY_TOKEN.strip()
    url = f"{base}/api/messages/send"
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.WHATSAPP_GATEWAY_TIMEOUT)
        ) as client:
            response = await client.post(
                url,
                params={"token": token},
                json={"number": number, "text": text},
            )
            data = response.json() if response.content else {}
            if response.status_code >= 400:
                return {
                    "success": False,
                    "number": number,
                    "error": data.get("detail") or data.get("error") or response.text[:200],
                }
            return {
                "success": bool(data.get("success")),
                "number": data.get("number") or number,
                "error": data.get("error"),
            }
    except httpx.HTTPError as e:
        return {"success": False, "number": number, "error": str(e)}


async def _enviar_bloco(
    *,
    nome: str,
    bloco: ListaEnvio,
    db: Session,
) -> Dict[str, Any]:
    texto = (bloco.text or "").strip()
    ids = [int(i) for i in (bloco.colaborador_ids or []) if i]
    if not ids:
        return {"lista": nome, "skipped": True, "reason": "sem destinatários", "envios": []}
    if not texto:
        return {"lista": nome, "skipped": True, "reason": "texto vazio", "envios": []}

    rows = (
        db.query(Collaborator)
        .filter(Collaborator.id.in_(ids), Collaborator.active.is_(True))
        .all()
    )
    por_id = {row.id: row for row in rows}
    envios: List[Dict[str, Any]] = []
    for cid in ids:
        row = por_id.get(cid)
        if not row:
            envios.append(
                {
                    "colaborador_id": cid,
                    "success": False,
                    "error": "colaborador não encontrado ou inativo",
                }
            )
            continue
        result = await _send_one(row.phone_e164, texto)
        envios.append(
            {
                "colaborador_id": cid,
                "name": row.name,
                "phone_e164": row.phone_e164,
                "roles": _roles_from_storage(row.role),
                "success": result.get("success"),
                "error": result.get("error"),
            }
        )
    ok = sum(1 for e in envios if e.get("success"))
    return {
        "lista": nome,
        "skipped": False,
        "enviados": ok,
        "falhas": len(envios) - ok,
        "envios": envios,
    }


class AvisoAdministradorIn(BaseModel):
    texto: str = ""


@router.post("/avisar-administrador")
async def avisar_administrador(
    body: AvisoAdministradorIn,
    db: Session = Depends(get_db_session),
):
    """Avisa quem tem a função dono de que o interpretador de conversa caiu."""
    if not _gateway_configured():
        raise HTTPException(
            status_code=503,
            detail="WhatsApp Gateway não configurado (WHATSAPP_GATEWAY_URL / TOKEN)",
        )
    _ensure(db)
    texto = (body.texto or "").strip() or (
        "O interpretador de conversa está indisponível. O operador pediu para avisar."
    )
    donos = [
        row
        for row in db.query(Collaborator).filter(Collaborator.active.is_(True)).all()
        if "dono" in _roles_from_storage(row.role) and (row.phone_e164 or "").strip()
    ]
    if not donos:
        raise HTTPException(status_code=404, detail="Não achei administrador com celular para avisar")
    enviados = 0
    for row in donos:
        result = await _send_one(row.phone_e164, texto)
        if result.get("success"):
            enviados += 1
    if enviados == 0:
        raise HTTPException(status_code=502, detail="Não consegui avisar o administrador")
    logger.info("Aviso ao administrador", enviados=enviados)
    return {"enviados": enviados}


@router.post("/enviar-listas")
async def enviar_listas(
    body: EnviarListasIn,
    db: Session = Depends(get_db_session),
):
    """
    Envia mensagens (colheita, pedidos, compras, rota) para os colaboradores escolhidos.
    Cada destinatário recebe só o texto da lista correspondente.
    """
    if not _gateway_configured():
        raise HTTPException(
            status_code=503,
            detail="WhatsApp Gateway não configurado (WHATSAPP_GATEWAY_URL / TOKEN)",
        )
    _ensure(db)

    resultados = [
        await _enviar_bloco(nome="colheita", bloco=body.colheita, db=db),
        await _enviar_bloco(nome="pedidos", bloco=body.pedidos, db=db),
        await _enviar_bloco(nome="compras", bloco=body.compras, db=db),
        await _enviar_bloco(nome="rota", bloco=body.rota, db=db),
    ]
    total_ok = sum(int(r.get("enviados") or 0) for r in resultados if not r.get("skipped"))
    total_fail = sum(int(r.get("falhas") or 0) for r in resultados if not r.get("skipped"))
    logger.info(
        "Envio listas WhatsApp",
        enviados=total_ok,
        falhas=total_fail,
    )
    return {
        "success": total_fail == 0 and total_ok > 0,
        "enviados": total_ok,
        "falhas": total_fail,
        "resultados": resultados,
    }
