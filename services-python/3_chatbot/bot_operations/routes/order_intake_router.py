"""
Entrada da tela de operação. Mesmo bot e o mesmo AI Service do Telegram.
Sem Keycloak nesta etapa: a tela local ainda não autentica.
"""

import sys

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.conversation_order_intake import CATALOG, convert_conversation

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/chatbot/orders", tags=["order-intake"])


class ConversationIn(BaseModel):
    conversation: str = Field(..., min_length=1)


def _log(message: str) -> None:
    print(f"[order-intake] {message}", file=sys.stderr, flush=True)
    logger.info(message)


@router.get("/catalog")
async def order_catalog():
    return {"catalog": CATALOG}


@router.post("/from-conversation")
async def orders_from_conversation(body: ConversationIn, request: Request):
    text = body.conversation.strip()
    origin = request.headers.get("origin") or "-"
    _log(f"POST /from-conversation origin={origin} chars={len(text)}")
    if not text:
        _log("recusado: conversa vazia")
        raise HTTPException(status_code=400, detail="Cole a conversa do pedido")
    try:
        orders = await convert_conversation(text)
    except ValueError as exc:
        _log(f"conversa sem pedido legível: {exc}")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        _log(f"AI Service falhou: {exc}")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        _log(f"erro inesperado: {exc}")
        logger.exception("erro ao converter conversa")
        raise HTTPException(status_code=502, detail=f"Falha ao converter a conversa: {exc}") from exc
    if not orders:
        _log("IA respondeu sem pedidos")
        raise HTTPException(status_code=422, detail="Nenhum pedido encontrado na conversa")
    _log(f"ok pedidos={len(orders)}")
    return {"orders": orders, "catalog": CATALOG}
