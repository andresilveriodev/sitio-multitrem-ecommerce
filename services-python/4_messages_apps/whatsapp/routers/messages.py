"""
Envio de mensagens WhatsApp (outbound Evolution).
"""

from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from config import settings
from services.evolution_client import EvolutionClient

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])

evolution_client: Optional[EvolutionClient] = None


class SendTextIn(BaseModel):
    number: str = Field(..., min_length=8, max_length=30)
    text: str = Field(..., min_length=1, max_length=4096)


def _verify_secret(
    token: Optional[str],
    x_webhook_secret: Optional[str],
) -> None:
    expected = (settings.EVOLUTION_WEBHOOK_SECRET or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    provided = (token or x_webhook_secret or "").strip()
    if not provided or provided != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/send")
async def send_text(
    body: SendTextIn,
    token: Optional[str] = Query(default=None),
    x_webhook_secret: Optional[str] = Header(default=None, alias="X-Webhook-Secret"),
):
    """Envia uma mensagem de texto via Evolution (sendText)."""
    _verify_secret(token, x_webhook_secret)
    if not evolution_client:
        raise HTTPException(status_code=503, detail="Evolution client not ready")
    result = await evolution_client.send_text(body.number, body.text)
    if not result.get("success"):
        return {
            "success": False,
            "number": result.get("number"),
            "error": result.get("error", "send failed"),
        }
    return {
        "success": True,
        "number": result.get("number"),
        "result": result.get("result"),
    }
