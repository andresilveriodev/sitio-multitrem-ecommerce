"""
Router para endpoints relacionados ao AI Service
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

from services.ai_integration import ai_integration
from auth.dependencies import require_colaborador_role
from fastapi import Depends

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


# Modelos Pydantic para validação
class ChatRequest(BaseModel):
    """Request simplificado para chat"""
    message: str


class ChatResponse(BaseModel):
    """Response simplificado para chat"""
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(require_colaborador_role)
):
    """
    Endpoint simplificado para chat com IA.
    Aceita apenas a mensagem e retorna a resposta.
    
    Este endpoint faz uma requisição simplificada para o AI Service
    usando apenas {"message": "..."} e retorna {"reply": "..."}.
    """
    try:
        # Validação básica
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="message é obrigatório e não pode estar vazio")
        
        # Chama o método simplificado que envia apenas a mensagem para o AI Service
        reply = await ai_integration.chat_simple(request.message.strip())
        
        if not reply:
            raise HTTPException(
                status_code=500,
                detail="Erro ao gerar resposta da IA"
            )
        
        return ChatResponse(reply=reply)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no endpoint /ai/chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/providers")
async def get_providers(
    current_user: dict = Depends(require_colaborador_role)
):
    """Lista provedores disponíveis"""
    try:
        providers_data = await ai_integration.get_providers()
        
        if not providers_data:
            # Retorna resposta padrão se o AI Service não responder
            return {
                "providers": [],
                "default_provider": "openai",
                "supported_providers": ["openai", "deepseek", "ollama"]
            }
        
        return providers_data
        
    except Exception as e:
        logger.error(f"Erro ao buscar provedores: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao buscar provedores")

