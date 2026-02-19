"""
Ponto de entrada principal do Commerce Service
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from config import settings
from routes import (
    products_router,
    customers_router,
    orders_router,
    payments_router,
    deliveries_router,
    shipping_router,
    chatbot_router
)

logger = structlog.get_logger()

def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI"""
    
    app = FastAPI(
        title="E-commerce Commerce Service",
        description="Serviço de processamento de pedidos do e-commerce Sítio Multitrem",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # Configurar Trusted Hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.DEBUG else ["localhost", "127.0.0.1"]
    )
    
    # Incluir rotas
    app.include_router(products_router, prefix="/api/v1")
    app.include_router(customers_router, prefix="/api/v1")
    app.include_router(orders_router, prefix="/api/v1")
    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(deliveries_router, prefix="/api/v1")
    app.include_router(shipping_router, prefix="/api/v1")
    # Rotas de chatbot com autenticação Keycloak
    app.include_router(chatbot_router, prefix="/api/v1")
    
    @app.get("/health")
    async def health_check():
        """Endpoint de verificação de saúde"""
        return {
            "status": "healthy",
            "service": "commerce_service",
            "version": "1.0.0"
        }
    
    @app.on_event("startup")
    async def startup_event():
        """Evento executado na inicialização da aplicação"""
        logger.info("Commerce Service iniciando", 
                   version="1.0.0",
                   port=settings.PORT)
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Evento executado no encerramento da aplicação"""
        logger.info("Commerce Service encerrando")
    
    return app

# Criar instância da aplicação
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
