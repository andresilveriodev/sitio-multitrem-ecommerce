"""
API Principal do AI-Service com Agno.
Substitui a implementacao NestJS por Python/FastAPI.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

from src.agents.sales_agent import create_sales_agent
from src.tools.ecommerce_tools import set_visitor_id

app = FastAPI(
    title="AI Service - Sitio Multitrem",
    description="Servico de IA com Agno para o assistente de vendas",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    visitorId: str
    message: str
    conversationHistory: Optional[List[dict]] = None
    source: Optional[str] = "web"


class ChatResponse(BaseModel):
    response: str
    actions: List[dict] = []
    cart: Optional[dict] = None
    paymentLink: Optional[str] = None


@app.post("/ai/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Processa uma mensagem do usuario e retorna a resposta do agente.
    """
    try:
        # Definir visitor_id para as tools
        set_visitor_id(request.visitorId)
        
        # Criar agente
        agent = create_sales_agent(request.visitorId)
        
        # Processar mensagem
        result = agent.run(
            request.message,
            user_id=request.visitorId
        )
        
        return ChatResponse(
            response=result.content or "Desculpe, nao consegui processar sua mensagem.",
            actions=[],
            cart=None,
            paymentLink=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ai/conversation/{visitor_id}")
async def get_conversation_history(visitor_id: str):
    """
    Retorna o historico de conversas do visitante.
    """
    try:
        agent = create_sales_agent(visitor_id)
        # TODO: implementar busca de historico do storage
        return {"history": [], "visitorId": visitor_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {"status": "healthy", "service": "ai-service-agno"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3007))
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

