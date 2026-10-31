"""
Endpoint WhatsApp — contrato próprio (não reutiliza Telegram/process-message).
Nesta fase: só confirma recebimento. Sem resposta ao usuário / sem CRM.
"""

from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chatbot", tags=["whatsapp"])


class WhatsAppInboundRequest(BaseModel):
    """Payload do gateway WhatsApp (Evolution)."""

    channel: str = Field(default="whatsapp")
    user_id: str = Field(..., description="Telefone (dígitos)")
    message: str = Field(..., description="Texto da mensagem")
    message_id: Optional[str] = None
    instance: Optional[str] = None
    remote_jid: Optional[str] = None
    push_name: Optional[str] = None
    raw_event_type: Optional[str] = None


@router.post("/whatsapp")
async def receive_whatsapp_message(body: WhatsAppInboundRequest):
    """
    Recebe mensagem IN do canal WhatsApp.
    Por enquanto apenas valida e registra — não responde no WhatsApp.
    """
    if body.channel and body.channel != "whatsapp":
        raise HTTPException(status_code=400, detail="channel deve ser 'whatsapp'")

    user_id = (body.user_id or "").strip()
    message = (body.message or "").strip()
    if not user_id or not message:
        raise HTTPException(status_code=400, detail="user_id e message são obrigatórios")

    received_at = datetime.now(timezone.utc).isoformat()

    logger.info(
        "WhatsApp mensagem recebida",
        user_id=user_id,
        push_name=body.push_name,
        message_id=body.message_id,
        instance=body.instance,
        message_preview=message[:80],
    )

    return {
        "success": True,
        "accepted": True,
        "channel": "whatsapp",
        "user_id": user_id,
        "message_id": body.message_id,
        "received_at": received_at,
    }
