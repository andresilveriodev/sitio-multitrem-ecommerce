"""
Gateway Service - BFF/API Gateway
Estrutura mínima funcional
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time

from config import settings
from routers.auth_router import router as auth_router
from routers.dispatch_router import router as dispatch_router, legacy_router as dispatch_legacy_router

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EdgeCORSFixMiddleware(BaseHTTPMiddleware):
    """Middleware para garantir compatibilidade CORS com MS Edge"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Se for uma requisição OPTIONS ou se tiver Origin header
        origin = request.headers.get("Origin")
        if origin:
            from config import settings
            allowed_origins = settings.ALLOWED_ORIGINS
            
            # Verificar se a origem está permitida
            if origin in allowed_origins or "*" in allowed_origins:
                # Garantir que Access-Control-Allow-Origin está presente
                if "Access-Control-Allow-Origin" not in response.headers:
                    response.headers["Access-Control-Allow-Origin"] = origin
                
                # Garantir outros headers CORS importantes para Edge
                if "Access-Control-Allow-Credentials" not in response.headers:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                
                # Garantir métodos permitidos (Edge precisa disso explicitamente)
                if "Access-Control-Allow-Methods" not in response.headers:
                    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
                
                # Garantir headers permitidos (Edge precisa disso explicitamente)
                if "Access-Control-Allow-Headers" not in response.headers:
                    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin, X-Requested-With"
        
        return response


class CORSLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para detectar e logar bloqueios de CORS"""
    
    def __init__(self, app, allowed_origins: list):
        super().__init__(app)
        self.allowed_origins = allowed_origins
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("Origin")
        # Normalizar path (remover barras duplas)
        path = request.url.path.replace("//", "/")
        method = request.method
        
        # Verificar se é uma requisição CORS (tem Origin header)
        if origin:
            # Verificar se a origem está permitida
            origin_allowed = origin in self.allowed_origins or "*" in self.allowed_origins
            
            if not origin_allowed:
                # ORIGEM BLOQUEADA - logar como WARNING
                logger.warning(
                    f"🚫 [CORS BLOQUEADO] Origin não permitida: {origin} | "
                    f"Path: {path} | Method: {method} | "
                    f"Origens permitidas: {', '.join(self.allowed_origins[:3])}{'...' if len(self.allowed_origins) > 3 else ''}"
                )
            else:
                # Origin permitida - logar como INFO
                logger.info(f"✅ [CORS] Origin permitida: {origin} | Path: {path} | Method: {method}")
        
        # Processar requisição (CORS middleware já processou antes)
        response = await call_next(request)
        
        # Verificar resposta CORS após TODO o processamento (incluindo CORS middleware)
        if origin:
            cors_allow_origin = response.headers.get("Access-Control-Allow-Origin", "N/A")
            cors_allow_methods = response.headers.get("Access-Control-Allow-Methods", "N/A")
            
            if cors_allow_origin == "N/A":
                logger.error(
                    f"❌ [CORS ERRO] Header Access-Control-Allow-Origin AUSENTE na resposta! | "
                    f"Origin: {origin} | Path: {path} | Method: {method} | "
                    f"Status: {response.status_code}"
                )
            elif cors_allow_origin != origin and cors_allow_origin != "*":
                logger.warning(
                    f"⚠️ [CORS] Origin não corresponde - Origin solicitada: {origin} | "
                    f"CORS-Allow-Origin na resposta: {cors_allow_origin} | Path: {path}"
                )
            else:
                logger.debug(
                    f"✅ [CORS] Header CORS correto - Origin: {origin} | "
                    f"CORS-Allow-Origin: {cors_allow_origin} | Methods: {cors_allow_methods} | Path: {path}"
                )
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logar todas as requisições que chegam no gateway"""
    
    async def dispatch(self, request: Request, call_next):
        # Log imediato quando a requisição chega
        path = request.url.path
        method = request.method
        client_ip = request.client.host if request.client else "unknown"
        origin = request.headers.get("Origin", "N/A")
        referer = request.headers.get("Referer", "N/A")
        
        # Log especial para o endpoint dispatch
        if path == "/v1/gateway/dispatch":
            logger.info(f"🚪 [GATEWAY] Requisição chegou no endpoint /v1/gateway/dispatch - Method: {method} | IP: {client_ip} | Origin: {origin}")
        elif path == "/api/v1/gateway/dispatch":
            # URL legacy - suportada para compatibilidade com MS Edge
            logger.info(f"🚪 [GATEWAY] Requisição chegou no endpoint /api/v1/gateway/dispatch (legacy) - Method: {method} | IP: {client_ip} | Origin: {origin}")
        
        # Log geral para todas as requisições
        logger.debug(f"📨 [GATEWAY] Requisição recebida - Path: {path} | Method: {method} | IP: {client_ip} | Origin: {origin}")
        
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.debug(f"✅ [GATEWAY] Requisição processada - Path: {path} | Status: {response.status_code} | Tempo: {process_time:.3f}s")
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"❌ [GATEWAY] Erro ao processar requisição - Path: {path} | Erro: {str(e)} | Tempo: {process_time:.3f}s")
            raise

# Criação da aplicação FastAPI
app = FastAPI(
    title="E-commerce Gateway",
    description="API Gateway para o sistema E-commerce",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS
# Configuração flexível: permite configurar via env ou usa padrão
# Em modo DEBUG, expande a lista para incluir mais portas comuns
cors_origins = settings.ALLOWED_ORIGINS

# Garantir que porta 3000 sempre está permitida (frontend padrão)
if "http://localhost:3000" not in cors_origins:
    cors_origins.append("http://localhost:3000")
if "http://127.0.0.1:3000" not in cors_origins:
    cors_origins.append("http://127.0.0.1:3000")

logger.info(f"🌐 CORS configurado - {len(cors_origins)} origem(ns) permitida(s)")
logger.info(f"   Porta 3000: {'✅' if 'http://localhost:3000' in cors_origins else '❌'}")
logger.info(f"   Origens permitidas: {', '.join(cors_origins[:5])}{'...' if len(cors_origins) > 5 else ''}")

# IMPORTANTE: No FastAPI, middlewares são executados na ORDEM INVERSA de adição
# Então adicionamos na ordem: CORS primeiro, depois logging

# IMPORTANTE: No FastAPI, middlewares são executados na ORDEM INVERSA de adição
# Então adicionamos na ordem: CORS primeiro, depois logging

# 1. CORS Middleware - DEVE ser o ÚLTIMO adicionado (primeiro a executar)
# Isso garante que os headers CORS sejam adicionados antes de qualquer outro processamento
# Headers explícitos para compatibilidade com MS Edge (Edge não aceita wildcards "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRFToken",
        "Cache-Control",
        "Pragma",
        "X-Forwarded-For",
        "X-Real-IP"
    ],  # Headers explícitos em vez de ["*"] para compatibilidade com Edge
    expose_headers=[
        "Content-Type",
        "Authorization",
        "Content-Length",
        "X-Total-Count",
        "X-Request-ID"
    ],  # Headers explícitos em vez de ["*"] para compatibilidade com Edge
    max_age=3600,
)

# 1.5. Edge CORS Fix (após CORS, antes dos outros)
# Garante que headers CORS estejam presentes em todas as respostas (Edge é mais rigoroso)
app.add_middleware(EdgeCORSFixMiddleware)

# 2. Middleware de logging geral
app.add_middleware(RequestLoggingMiddleware)

# 3. Middleware de logging CORS (primeiro adicionado, último a executar)
# Isso permite verificar os headers CORS após todo o processamento
app.add_middleware(CORSLoggingMiddleware, allowed_origins=cors_origins)

# Rotas
app.include_router(auth_router)
app.include_router(dispatch_router)
app.include_router(dispatch_legacy_router)  # Router legacy para compatibilidade com /api/v1/gateway/dispatch

# Rotas básicas
@app.get("/")
async def root():
    """Endpoint raiz do Gateway"""
    return {
        "message": "E-commerce Gateway Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.DEBUG else None
    }

@app.get("/health")
async def health_check():
    """Health check do Gateway"""
    return {
        "status": "healthy",
        "service": "gateway",
        "version": "1.0.0"
    }

@app.get("/v1/status")
async def api_status():
    """Status detalhado da API"""
    import time
    return {
        "gateway": "running",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """Inicializa serviços na startup da aplicação"""
    logger.info("Iniciando Gateway Service...")


@app.on_event("shutdown")
async def shutdown_event():
    """Limpa recursos no shutdown da aplicação"""
    logger.info("Encerrando Gateway Service...")