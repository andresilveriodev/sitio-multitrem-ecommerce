"""
Configuração da aplicação FastAPI para o chatbot_service
"""

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from config import settings
from routes import chat_router, analytics_router, ai_router
from services.cache_service import cache_service
from services.context_service import context_service
from services.ai_integration import ai_integration

logger = structlog.get_logger(__name__)

def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI"""
    
    app = FastAPI(
        title="E-commerce Chatbot Service",
        description="Serviço de Chatbot - Middleware inteligente entre frontend e AI Service",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # Middleware de segurança
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # Event handlers para inicialização e shutdown
    @app.on_event("startup")
    async def startup_event():
        """Inicializa serviços na startup"""
        logger.info("Iniciando Chatbot Service...")
        
        try:
            # Conecta serviços críticos
            await cache_service.connect()
            await context_service.connect()
            await ai_integration.connect()
            
            logger.info("Chatbot Service iniciado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar serviços: {e}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Desconecta serviços no shutdown"""
        logger.info("Desligando Chatbot Service...")
        
        try:
            await cache_service.disconnect()
            await context_service.disconnect()
            await ai_integration.disconnect()
            
            logger.info("Chatbot Service desligado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao desligar serviços: {e}")
    
    # Inclui routers
    app.include_router(chat_router)
    app.include_router(analytics_router)
    app.include_router(ai_router)
    
    @app.get("/health")
    async def health_check():
        """Endpoint de verificação de saúde do serviço"""
        return {
            "status": "healthy", 
            "service": "chatbot_service",
            "version": "1.0.0",
            "port": settings.PORT
        }
    
    @app.get("/")
    async def root():
        """Endpoint raiz"""
        return {
            "message": "E-commerce Chatbot Service",
            "description": "Middleware inteligente para otimização de IA",
            "version": "1.0.0",
            "docs": "/docs" if settings.DEBUG else "Documentação disponível em modo debug"
        }
    
    return app
