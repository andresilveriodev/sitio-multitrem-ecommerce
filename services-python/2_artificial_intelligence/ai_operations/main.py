from app.socketio_instance import app, sio_app
from fastapi.middleware.cors import CORSMiddleware
from app.config import CORS_ORIGINS
from app.routers.chatbot_resource import router as chatbot_router
from app.routers.ai_resource import router as ai_router
from app.routers.analytics_resource import router as analytics_router
from app.routers.ai_management_resource import router as ai_management_router
from middleware.tracking_middleware import AITrackingMiddleware
from app.logger import configure_logging
from app.db import init_db
import logging

# Configura o sistema de logging
logger = configure_logging()

# Adiciona middleware de tracking de IA
app.add_middleware(AITrackingMiddleware)

# Adiciona middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Inclui os roteadores
app.include_router(chatbot_router, prefix="/chatbot", tags=["Chatbot"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])
app.include_router(analytics_router, tags=["Analytics"])
app.include_router(ai_management_router, prefix="/api/v1", tags=["AI Management"])

# Endpoint raiz
@app.get("/")
def hello():
    """
    Endpoint de boas-vindas
    """
    return {
        "message": "ChatBot com IA pronto para uso",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chatbot": "/chatbot",
            "ai": "/ai",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
def health_check():
    """
    Endpoint de verificação de saúde geral
    """
    return {
        "status": "healthy",
        "service": "chatbot_middleware",
        "version": "1.0.0"
    }

# Event handlers do Socket.IO
@app.on_event("startup")
async def startup_event():
    """
    Evento executado na inicialização da aplicação
    """
    logger.info("Iniciando Chatbot Middleware API...")
    
    # Log da versão do OpenAI
    try:
        import openai
        logger.info(f"Versão do openai: {openai.__version__}")
        print(f"[INFO] Versão do openai: {openai.__version__}")
    except Exception as e:
        logger.warning(f"Não foi possível obter versão do openai: {e}")
    
    # Inicializar banco de dados
    try:
        init_db()
        logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
    
    logger.info("Chatbot Middleware API iniciada com sucesso!")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento executado no encerramento da aplicação
    """
    logger.info("Encerrando Chatbot Middleware API...")

# Aplicação ASGI principal (com Socket.IO)
application = sio_app

if __name__ == "__main__":
    import uvicorn
    from app.config import HTTP_PORT
    
    logger.info(f"Iniciando servidor na porta {HTTP_PORT}")
    uvicorn.run(
        "main:application",
        host="0.0.0.0",
        port=HTTP_PORT,
        reload=True,
        log_level="info"
    )