"""
Ponto de entrada principal do Auth Service
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from config import settings
from routes import auth_router, acl_router, user_profile_router, users_router

logger = structlog.get_logger()

def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI"""
    
    app = FastAPI(
        title="E-commerce User Service",
        description="Serviço de autenticação e autorização com Keycloak e ACL",
        version="1.0.0",
        docs_url="/docs",  # Sempre habilitar Swagger
        redoc_url="/redoc",  # Sempre habilitar ReDoc
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
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(acl_router, prefix="/api/v1")
    app.include_router(user_profile_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    
    @app.get("/health")
    async def health_check():
        """Endpoint de verificação de saúde"""
        return {
            "status": "healthy",
            "service": "auth_service",
            "version": "1.0.0",
            "keycloak_connected": True
        }
    
    @app.on_event("startup")
    async def startup_event():
        """Evento executado na inicialização da aplicação"""
        logger.info("Auth Service iniciando", 
                   version="1.0.0",
                   keycloak_url=settings.KEYCLOAK_AUTH_SERVER_URL,
                   realm=settings.KEYCLOAK_REALM)
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Evento executado no encerramento da aplicação"""
        logger.info("Auth Service encerrando")
    
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

