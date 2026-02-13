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
from services.market_service import market_service

logger = structlog.get_logger(__name__)

def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI"""
    
    app = FastAPI(
        title="B3-Trader Chatbot Operations Service",
        description="Chatbot Operations Service - Intelligent middleware between frontend and AI Service",
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
        logger.info("Starting Chatbot Operations Service...")
        
        try:
            # Conecta serviços críticos
            await cache_service.connect()
            await context_service.connect()
            await ai_integration.connect()
            
            # Market Service é opcional - não falha se não estiver disponível
            try:
                await market_service.connect()
            except Exception as e:
                logger.warning(f"Market Service not available (non-critical): {e}")
            
            logger.info("Chatbot Operations Service started successfully")
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Desconecta serviços no shutdown"""
        logger.info("Shutting down Chatbot Operations Service...")
        
        try:
            await cache_service.disconnect()
            await context_service.disconnect()
            await ai_integration.disconnect()
            await market_service.disconnect()
            
            logger.info("Chatbot Operations Service shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down services: {e}")
    
    # Inclui routers
    app.include_router(chat_router)
    app.include_router(analytics_router)
    app.include_router(ai_router)
    
    @app.get("/health")
    async def health_check():
        """Endpoint de verificação de saúde do serviço"""
        return {
            "status": "healthy", 
            "service": "chatbot_operations_service",
            "version": "1.0.0",
            "port": settings.PORT
        }
    
    @app.get("/")
    async def root():
        """Endpoint raiz"""
        return {
            "message": "B3-Trader Chatbot Operations Service",
            "description": "Intelligent middleware for AI optimization",
            "version": "1.0.0",
            "docs": "/docs" if settings.DEBUG else "Documentation available in debug mode"
        }
    
    return app
