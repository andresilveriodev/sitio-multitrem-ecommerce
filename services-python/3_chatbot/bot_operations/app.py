"""
Configuração da aplicação FastAPI para o chatbot_service
"""

from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import time

from config import settings
from routes import chat_router, analytics_router, ai_router, telegram_router
from services.cache_service import cache_service
from services.context_service import context_service
from services.ai_integration import ai_integration
from services.market_service import market_service
from services.database_service import database_service

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logar todas as requisições HTTP"""
    
    async def dispatch(self, request: Request, call_next):
        # Log da requisição recebida
        start_time = time.time()
        
        logger.info(
            "🌐 REQUISIÇÃO HTTP RECEBIDA",
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
            client_port=request.client.port if request.client else None,
            headers_keys=[k for k in request.headers.keys() if k.lower() not in ['authorization', 'cookie']]
        )
        
        # Processar requisição
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            logger.info(
                "✅ REQUISIÇÃO PROCESSADA",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s"
            )
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "❌ ERRO AO PROCESSAR REQUISIÇÃO",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=f"{process_time:.3f}s",
                exc_info=True
            )
            raise

def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI"""
    
    app = FastAPI(
        title="B3-Trader Chatbot Operations Service",
        description="Chatbot Operations Service - Intelligent middleware between frontend and AI Service",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # Middleware de logging (deve ser o primeiro para capturar todas as requisições)
    app.add_middleware(LoggingMiddleware)
    
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
            
            # Database Service - necessário para CRUD de produtos
            try:
                await database_service.connect()
            except Exception as e:
                logger.warning(f"Database Service not available (non-critical): {e}")
            
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
            await database_service.disconnect()
            await market_service.disconnect()
            
            logger.info("Chatbot Operations Service shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down services: {e}")
    
    # Inclui routers
    app.include_router(chat_router)
    app.include_router(analytics_router)
    app.include_router(ai_router)
    app.include_router(telegram_router)
    
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
