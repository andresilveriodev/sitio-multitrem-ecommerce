"""
Ponto de entrada principal do Commerce Service
"""

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
import structlog
import sys
import json

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
    
    # Middleware para capturar body das requisições (para logging de erros)
    @app.middleware("http")
    async def capture_body_middleware(request: Request, call_next):
        """Middleware para capturar body da requisição para logging de erros"""
        # Apenas para POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                # Armazenar body no state da requisição
                request.state.body = body_bytes
                # Recriar o stream para que o FastAPI possa ler novamente
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except Exception:
                request.state.body = None
        else:
            request.state.body = None
        
        response = await call_next(request)
        return response
    
    # Incluir rotas
    app.include_router(products_router, prefix="/api/v1")
    app.include_router(customers_router, prefix="/api/v1")
    app.include_router(orders_router, prefix="/api/v1")
    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(deliveries_router, prefix="/api/v1")
    app.include_router(shipping_router, prefix="/api/v1")
    # Rotas de chatbot com autenticação Keycloak
    app.include_router(chatbot_router, prefix="/api/v1")
    
    # Exception handler para erros de validação (422)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handler para erros de validação - exibe JSON recebido e detalhes do erro"""
        # Tentar ler o body da requisição (capturado pelo middleware)
        body = None
        try:
            # Tentar obter do state (capturado pelo middleware)
            if hasattr(request.state, 'body') and request.state.body:
                body_bytes = request.state.body
                try:
                    body = json.loads(body_bytes.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    body = body_bytes.decode('utf-8', errors='replace')[:2000]  # Limitar tamanho
            else:
                # Fallback: tentar ler diretamente (pode falhar se já foi consumido)
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        try:
                            body = json.loads(body_bytes.decode('utf-8'))
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            body = body_bytes.decode('utf-8', errors='replace')[:2000]
                except Exception:
                    body = "Body não disponível (já foi consumido)"
        except Exception as e:
            body = f"Erro ao ler body: {str(e)}"
        
        # Formatar erros de validação
        errors = exc.errors()
        error_details = []
        for error in errors:
            error_details.append({
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "type": error.get("type"),
                "ctx": error.get("ctx")
            })
        
        error_msg = (
            f"[VALIDATION ERROR 422] Erro de validação no endpoint {request.method} {request.url.path}\n"
            f"JSON Recebido: {json.dumps(body, indent=2, ensure_ascii=False)}\n"
            f"Erros de Validação: {json.dumps(error_details, indent=2, ensure_ascii=False)}"
        )
        print(error_msg, file=sys.stderr, flush=True)
        
        logger.error(
            "Erro 422 Validation Error",
            path=request.url.path,
            method=request.method,
            body=body,
            validation_errors=error_details,
            headers=dict(request.headers)
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "detail": error_details,
                "body_received": body
            }
        )
    
    # Exception handler global para capturar erros 401 e logar detalhes
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handler global para exceções HTTP, especialmente 401"""
        if exc.status_code == 401:
            # Log detalhado do erro 401
            auth_header = request.headers.get("Authorization", "N/A")
            token_preview = "N/A"
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                token_preview = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else "***"
            
            error_msg = (
                f"[AUTH ERROR 401] Unauthorized - Path: {request.url.path}, "
                f"Method: {request.method}, Detail: {exc.detail}, "
                f"Token preview: {token_preview}"
            )
            print(error_msg, file=sys.stderr, flush=True)
            logger.error(
                "Erro 401 Unauthorized",
                path=request.url.path,
                method=request.method,
                detail=exc.detail,
                token_preview=token_preview,
                headers=dict(request.headers)
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
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
