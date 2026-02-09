"""
Router para processamento de mensagens do Telegram
"""

import structlog
from fastapi import APIRouter, Request, HTTPException

from config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()

# Instâncias dos serviços serão injetadas pelo app
telegram_service = None
polling_service = None


@router.get("/polling-status")
async def get_polling_status():
    """
    Obtém status do serviço de polling
    """
    if not polling_service:
        return {
            "success": False,
            "error": "Polling service não está disponível"
        }
    
    status = polling_service.get_status()
    return {
        "success": True,
        "polling_status": status,
        "message": "Serviço usando polling (getUpdates) ao invés de webhook"
    }


@router.post("/send-message")
async def send_message(request: Request):
    """
    Endpoint para enviar mensagem via Telegram (uso administrativo/teste)
    """
    try:
        if not telegram_service:
            raise HTTPException(status_code=503, detail="Telegram service não está disponível")
        
        body = await request.json()
        chat_id = body.get("chat_id")
        text = body.get("text")
        
        if not chat_id or not text:
            raise HTTPException(status_code=400, detail="chat_id e text são obrigatórios")
        
        result = await telegram_service.send_message(chat_id=chat_id, text=text)
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao enviar mensagem: {str(e)}")
