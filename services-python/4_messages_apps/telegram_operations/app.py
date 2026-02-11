"""
Telegram Service - Integração com Telegram Bot
Recebe mensagens do Telegram e encaminha para o Chatbot Service
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx
import structlog
from typing import Optional

from config import settings
from routers import telegram_router
from services.telegram_service import TelegramService
from services.polling_service import PollingService
from services.keycloak_auth_service import keycloak_auth_service

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = structlog.get_logger(__name__)

# Instâncias globais
telegram_service = TelegramService()
polling_service = PollingService(telegram_service)

# Criar aplicação FastAPI
app = FastAPI(
    title="Telegram Service",
    description="Serviço de integração com Telegram Bot para E-commerce",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(telegram_router.router, prefix="/telegram", tags=["telegram"])

# Injetar instâncias nos routers
telegram_router.telegram_service = telegram_service
telegram_router.polling_service = polling_service


@app.get("/")
async def root():
    """Endpoint raiz - status do serviço"""
    return {
        "service": "telegram_service",
        "status": "running",
        "version": "1.0.0",
        "message": "Telegram Service - E-commerce"
    }


@app.get("/health")
async def health_check():
    """Health check do serviço"""
    polling_status = polling_service.get_status()
    return {
        "status": "healthy",
        "service": "telegram_service",
        "polling": polling_status
    }


@app.on_event("startup")
async def startup_event():
    """Evento de inicialização"""
    logger.info("Iniciando Telegram Service...")
    logger.info(f"Chatbot Service URL: {settings.CHATBOT_SERVICE_URL}")
    logger.info(f"Keycloak Auth Server: {settings.KEYCLOAK_AUTH_SERVER_URL}")
    logger.info(f"Keycloak Realm: {settings.KEYCLOAK_REALM}")
    logger.info(f"Keycloak Client ID: {settings.KEYCLOAK_CLIENT_ID}")
    
    # Injetar serviços nos routers (já feito antes, mas garantindo)
    telegram_router.telegram_service = telegram_service
    telegram_router.polling_service = polling_service
    
    # Iniciar serviço de polling
    try:
        await polling_service.start()
        logger.info("Telegram Service iniciado com sucesso (modo polling)")
    except Exception as e:
        logger.error(f"Erro ao iniciar polling: {e}", exc_info=True)
        logger.warning("Servidor continuará rodando mesmo sem polling ativo. Configure o TELEGRAM_BOT_TOKEN no .env")
        # Não lançar exceção para permitir que o servidor inicie mesmo sem token configurado


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de desligamento"""
    logger.info("Desligando Telegram Service...")
    
    # Parar serviço de polling
    try:
        await polling_service.stop()
    except Exception as e:
        logger.error(f"Erro ao parar polling: {e}", exc_info=True)
    
    # Fechar conexões
    try:
        await telegram_service.close()
    except Exception as e:
        logger.error(f"Erro ao fechar conexões: {e}", exc_info=True)
    
    logger.info("Telegram Service desligado com sucesso")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
