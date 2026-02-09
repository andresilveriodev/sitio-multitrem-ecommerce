"""
Router para o endpoint genérico de dispatch
Endpoint genérico no gateway que roteia requisições para qualquer serviço backend
"""

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any
import httpx
import logging
import re
import time
from urllib.parse import urlencode

from config import settings
from auth.jwt_validator import verify_bearer_token_or_401

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/gateway", tags=["Gateway"])

# Mapeamento de serviços conforme especificação (ordenado por porta)
SERVICE_MAPPING = {
    "user": {
        "host": "localhost",
        "port": 8001,
        "base_path": "/api/v1"
    },
    "import": {
        "host": "localhost",
        "port": 8002,
        "base_path": "/api/v1"
    },
    "report": {
        "host": "localhost",
        "port": 8007,
        "base_path": "/api/v1"
    },
    "chatbot": {
        "host": "localhost",
        "port": 8002,
        "base_path": "/api/v1"
    },
    "alert": {
        "host": "localhost",
        "port": 8009,
        "base_path": "/api/v1"
    },
    "ai": {
        "host": "localhost",
        "port": 8003,
        "base_path": "/api/v1"
    },
}

# Fallback para URLs completas do config (caso existam)
# Usa getattr para acessar configurações opcionais sem erro
FALLBACK_SERVICES = {
    "user": getattr(settings, "USER_SERVICE_URL", None),
    "alert": getattr(settings, "ALERT_SERVICE_URL", None),
    "report": getattr(settings, "REPORT_SERVICE_URL", None),
    "import": getattr(settings, "IMPORT_SERVICE_URL", None),
    "chatbot": getattr(settings, "CHATBOT_SERVICE_URL", None),
    "ai": getattr(settings, "AI_SERVICE_URL", None),
}
# Remove entradas None (serviços não configurados)
FALLBACK_SERVICES = {k: v for k, v in FALLBACK_SERVICES.items() if v is not None}


class GatewayRequest(BaseModel):
    """Request model para dispatch genérico"""
    service: str
    endpoint: str
    method: str = "GET"
    params: Optional[Dict[str, Any]] = None
    body: Optional[Any] = None
    headers: Optional[Dict[str, str]] = None

    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if v.upper() not in valid_methods:
            raise ValueError(f"Método '{v}' inválido. Métodos válidos: {', '.join(valid_methods)}")
        return v.upper()

    @field_validator('endpoint')
    @classmethod
    def validate_endpoint(cls, v):
        # Sanitização básica: remover caracteres perigosos
        if not v.startswith('/'):
            v = '/' + v
        # Validar path traversal
        if '..' in v or v.startswith('//'):
            raise ValueError("Endpoint inválido: path traversal detectado")
        return v


def sanitize_endpoint(endpoint: str) -> str:
    """Sanitiza endpoint para evitar path traversal"""
    # Remover barras duplas
    endpoint = re.sub(r'/+', '/', endpoint)
    # Garantir que comece com /
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    # Remover tentativas de path traversal
    endpoint = endpoint.replace('../', '').replace('..\\', '')
    return endpoint


def get_service_url(service_name: str) -> str:
    """Obtém URL base do serviço (apenas host:port, sem path)"""
    from urllib.parse import urlparse, urlunparse
    
    # Tentar usar mapeamento detalhado primeiro
    if service_name in SERVICE_MAPPING:
        config = SERVICE_MAPPING[service_name]
        # Se a URL do config existir, extrair apenas host:port
        if service_name in FALLBACK_SERVICES:
            base_url = FALLBACK_SERVICES[service_name]
            # Remover qualquer path da URL, manter apenas protocolo://host:port
            parsed = urlparse(base_url)
            # Usar port do parsed ou do config como fallback
            port = parsed.port or config.get('port', 8000)
            netloc = f"{parsed.hostname}:{port}" if port else parsed.hostname
            # Reconstruir URL apenas com protocolo, host e port (sem path)
            return urlunparse((parsed.scheme or 'http', netloc, "", "", "", ""))
        else:
            # Retornar apenas host:port sem base_path
            return f"http://{config['host']}:{config['port']}"
    
    # Fallback para URLs completas do config - extrair apenas host:port
    if service_name in FALLBACK_SERVICES:
        base_url = FALLBACK_SERVICES[service_name]
        parsed = urlparse(base_url)
        port = parsed.port or 8000
        netloc = f"{parsed.hostname}:{port}" if port else parsed.hostname
        return urlunparse((parsed.scheme or 'http', netloc, "", "", "", ""))
    
    raise ValueError(f"Serviço '{service_name}' não encontrado no mapeamento")


@router.get("/health")
async def gateway_health():
    """
    Health check do Gateway Service
    
    **Resposta:**
    ```json
    {
        "status": "healthy",
        "service": "gateway",
        "version": "1.0.0"
    }
    ```
    """
    return {
        "status": "healthy",
        "service": "gateway",
        "version": "1.0.0"
    }


@router.get("/status")
async def gateway_status():
    """
    Status do Gateway Service (endpoint simples para verificação de disponibilidade)
    Não requer autenticação - usado pelo frontend para verificar se o gateway está online
    """
    return {
        "online": True,
        "service": "gateway",
        "version": "1.0.0"
    }


@router.options("/dispatch")
async def dispatch_options(request: Request):
    """Endpoint OPTIONS para CORS preflight - compatível com Edge"""
    from fastapi.responses import Response
    from config import settings
    
    origin = request.headers.get("Origin")
    
    # Criar resposta com headers CORS explícitos
    response = Response()
    
    # Headers CORS obrigatórios para Edge
    if origin:
        # Verificar se a origem está permitida (mesma lógica do CORSMiddleware)
        allowed_origins = settings.ALLOWED_ORIGINS
        
        if origin in allowed_origins or "*" in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" not in allowed_origins:
            # Se não estiver permitida, não adicionar o header (Edge será mais rigoroso)
            pass
    
    # Headers adicionais explícitos para Edge (não usar wildcards)
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin, X-Requested-With, X-CSRFToken"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "3600"
    response.headers["Access-Control-Expose-Headers"] = "Content-Type, Authorization, Content-Length"
    
    return response


@router.post("/dispatch")
async def dispatch_request(
    request: GatewayRequest,
    authorization: str = Header(..., alias="Authorization"),
    req: Request = None
):
    """
    Endpoint genérico de dispatch
    
    Roteia requisições para qualquer serviço backend através do gateway.
    
    **Autenticação obrigatória**: Bearer token (Keycloak JWT)
    
    **Exemplo de requisição:**
    ```json
    {
        "service": "user",
        "endpoint": "/api/v1/users",
        "method": "GET",
        "params": {
            "page": 1,
            "size": 10
        }
    }
    ```
    
    **Exemplo com body (POST/PUT/PATCH):**
    ```json
    {
        "service": "user",
        "endpoint": "/api/v1/users",
        "method": "POST",
        "body": {
            "username": "usuario",
            "email": "usuario@example.com",
            "password": "senha123"
        }
    }
    ```
    """
    start_time = time.time()
    
    # 1. Validar autenticação JWT
    try:
        user_claims = verify_bearer_token_or_401(req)
        user_id = user_claims.get('sub', 'unknown')
        username = user_claims.get('preferred_username', 'unknown')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao validar token: {e}")
        raise HTTPException(
            status_code=401,
            detail="Token de autenticação inválido"
        )
    
    # 2. Validar serviço
    if request.service not in SERVICE_MAPPING and request.service not in FALLBACK_SERVICES:
        logger.warning(f"Serviço '{request.service}' não encontrado - usuário: {username}")
        raise HTTPException(
            status_code=400,
            detail=f"Serviço '{request.service}' não encontrado. Serviços disponíveis: {', '.join(set(list(SERVICE_MAPPING.keys()) + list(FALLBACK_SERVICES.keys())))}"
        )
    
    # 3. Sanitizar endpoint
    endpoint = sanitize_endpoint(request.endpoint)
    
    # 4. Obter URL do serviço
    try:
        service_base_url = get_service_url(request.service)
    except ValueError as e:
        logger.error(f"Erro ao obter URL do serviço '{request.service}': {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    # 5. Substituir path parameters no endpoint (ex: {account_id} -> valor)
    path_params = {}
    query_params = {}
    
    if request.params:
        # Separar path params de query params
        # Path params são aqueles que aparecem no endpoint como {param_name}
        path_param_pattern = re.compile(r'\{(\w+)\}')
        path_param_names = set(path_param_pattern.findall(endpoint))
        
        for key, value in request.params.items():
            if key in path_param_names:
                path_params[key] = value
            else:
                query_params[key] = value
        
        # Substituir path parameters no endpoint
        for param_name, param_value in path_params.items():
            endpoint = endpoint.replace(f"{{{param_name}}}", str(param_value))
    
    # 6. Construir URL completa
    # Repassar o endpoint exatamente como vem do frontend, sem adicionar ou remover nada
    # Apenas garantir que não haja barra duplicada entre service_base_url e endpoint
    
    # Remover barra duplicada se necessário (apenas normalização de barras)
    if service_base_url.endswith('/') and endpoint.startswith('/'):
        # Se ambos têm barra, remover uma
        target_url = f"{service_base_url.rstrip('/')}{endpoint}"
    elif not service_base_url.endswith('/') and not endpoint.startswith('/'):
        # Se nenhum tem barra, adicionar uma
        target_url = f"{service_base_url}/{endpoint}"
    else:
        # Um tem barra e outro não, concatenar direto
        target_url = f"{service_base_url}{endpoint}"
    
    # Log da URL construída para debug
    logger.debug(f"URL construída para serviço {request.service}: {target_url}")
    
    # 7. Preparar headers (incluir token de autenticação)
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json",
        **(request.headers or {})
    }
    
    # 8. Preparar query params (apenas para GET e DELETE, ou se houver query params)
    params = None
    if request.method in ["GET", "DELETE"]:
        # Usar query_params (já separados dos path params)
        params = query_params if query_params else None
    elif query_params:
        # Para outros métodos, se houver query params, adicionar à URL
        # (alguns serviços podem aceitar query params em POST/PUT)
        separator = '&' if '?' in target_url else '?'
        target_url = f"{target_url}{separator}{urlencode(query_params)}"
    
    # 9. Preparar body (para POST, PUT, PATCH)
    json_body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        # Priorizar body sobre params (mas params já foram usados para path/query)
        json_body = request.body if request.body is not None else None
    
    # 10. Logging de auditoria
    logger.info(
        f"Dispatch request - service: {request.service}, "
        f"endpoint: {endpoint}, method: {request.method}, "
        f"path_params: {path_params}, query_params: {query_params}, "
        f"user: {username} ({user_id})"
    )
    
    # 11. Fazer requisição ao serviço
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=params,
                json=json_body,
            )
            
            # 12. Calcular tempo de resposta
            response_time = time.time() - start_time
            
            # 13. Logging de resposta
            logger.info(
                f"Dispatch response - service: {request.service}, "
                f"status: {response.status_code}, "
                f"response_time: {response_time:.3f}s, "
                f"user: {username}"
            )
            
            # 14. Filtrar headers sensíveis antes de retornar
            # Remover headers de redirect e outros headers que não devem ser expostos ao frontend
            filtered_headers = {}
            headers_to_remove = [
                'location',  # Header de redirect - não deve ser exposto ao frontend
                'content-encoding',
                'transfer-encoding',
                'connection',
                'server',
            ]
            
            for key, value in response.headers.items():
                if key.lower() not in headers_to_remove:
                    filtered_headers[key] = value
            
            # 15. Verificar se há erro HTTP e propagar corretamente
            status_code = response.status_code
            
            # Extrair dados da resposta
            try:
                response_data = response.json()
            except Exception:
                # Se não for JSON, retornar texto
                response_data = response.text
            
            # Se o status_code indica erro (4xx ou 5xx), propagar o erro HTTP ao invés de encapsular em 200
            if status_code >= 400:
                logger.warning(
                    f"Erro HTTP {status_code} do serviço {request.service} - "
                    f"endpoint: {endpoint}, user: {username}"
                )
                
                # Extrair mensagem de erro do serviço
                error_message = "Erro do serviço"
                if isinstance(response_data, dict):
                    error_message = (
                        response_data.get("detail") or 
                        response_data.get("message") or 
                        response_data.get("error") or 
                        str(response_data)
                    )
                elif isinstance(response_data, str):
                    error_message = response_data[:500]  # Limitar tamanho
                else:
                    error_message = str(response_data)
                
                # Mensagens específicas por código de erro
                if status_code == 401:
                    detail_msg = f"Autenticação falhou no serviço {request.service}. Token inválido ou expirado."
                    if error_message and error_message != "Erro do serviço":
                        detail_msg = error_message
                elif status_code == 403:
                    detail_msg = f"Acesso negado no serviço {request.service}. Você não tem permissão para acessar este recurso."
                    if error_message and error_message != "Erro do serviço":
                        detail_msg = error_message
                elif status_code == 404:
                    detail_msg = f"Endpoint não encontrado no serviço {request.service}: {endpoint}"
                    if error_message and error_message != "Erro do serviço":
                        detail_msg = error_message
                elif status_code == 400:
                    detail_msg = f"Requisição inválida para o serviço {request.service}: {error_message}"
                elif status_code == 500:
                    detail_msg = f"Erro interno no serviço {request.service}: {error_message}"
                elif status_code == 503:
                    detail_msg = f"Serviço {request.service} temporariamente indisponível. Tente novamente em alguns instantes."
                else:
                    detail_msg = f"Erro HTTP {status_code} do serviço {request.service}: {error_message}"
                
                # Propagar o erro HTTP com o mesmo status_code do serviço
                raise HTTPException(
                    status_code=status_code,
                    detail=detail_msg
                )
            
            # Se for sucesso (2xx), retornar normalmente
            return {
                "status": status_code,
                "data": response_data,
                "headers": filtered_headers  # Usar headers filtrados (sem Location)
            }
            
    except httpx.ConnectError as e:
        # Conexão recusada imediatamente - serviço definitivamente offline
        response_time = time.time() - start_time
        error_msg = str(e)
        # Extrair porta da URL de forma mais robusta
        try:
            from urllib.parse import urlparse
            parsed = urlparse(target_url)
            port = parsed.port if parsed.port else 'desconhecida'
        except:
            port = 'desconhecida'
        
        logger.error(
            f"🔌 [DISPATCH] Conexão recusada pelo serviço {request.service} - "
            f"endpoint: {endpoint}, response_time: {response_time:.3f}s, "
            f"user: {username}, error: {error_msg}, URL: {target_url}"
        )
        raise HTTPException(
            status_code=502,
            detail=f"Serviço {request.service} está offline. Conexão recusada na porta {port}. Verifique se o serviço está rodando e acessível."
        )
    except httpx.ConnectTimeout as e:
        # Timeout ao tentar conectar - serviço não responde
        response_time = time.time() - start_time
        error_msg = str(e)
        logger.error(
            f"⏱️ [DISPATCH] Timeout ao conectar com serviço {request.service} - "
            f"endpoint: {endpoint}, response_time: {response_time:.3f}s, "
            f"user: {username}, error: {error_msg}, URL: {target_url}"
        )
        raise HTTPException(
            status_code=502,
            detail=f"Serviço {request.service} não está respondendo. Timeout ao tentar estabelecer conexão. O serviço pode estar offline ou sobrecarregado."
        )
    except httpx.ReadTimeout as e:
        # Timeout ao ler resposta - serviço conectou mas não respondeu
        response_time = time.time() - start_time
        error_msg = str(e)
        logger.error(
            f"⏱️ [DISPATCH] Timeout ao ler resposta do serviço {request.service} - "
            f"endpoint: {endpoint}, response_time: {response_time:.3f}s, "
            f"user: {username}, error: {error_msg}, URL: {target_url}"
        )
        raise HTTPException(
            status_code=504,
            detail=f"Serviço {request.service} conectou mas não respondeu a tempo. Timeout aguardando resposta. O serviço pode estar sobrecarregado ou processando uma operação muito lenta."
        )
    except httpx.TimeoutException as e:
        # Timeout genérico (caso não seja capturado acima)
        response_time = time.time() - start_time
        error_type = type(e).__name__
        logger.error(
            f"⏱️ [DISPATCH] Timeout genérico ao comunicar com serviço {request.service} - "
            f"endpoint: {endpoint}, response_time: {response_time:.3f}s, "
            f"user: {username}, error_type: {error_type}, URL: {target_url}"
        )
        raise HTTPException(
            status_code=504,
            detail=f"Timeout ao comunicar com o serviço {request.service}. A requisição excedeu o tempo limite de espera. O serviço pode estar offline, sobrecarregado ou processando uma operação muito lenta."
        )
    except httpx.HTTPStatusError as e:
        # Erro HTTP do serviço (4xx, 5xx) - serviço respondeu mas com erro
        response_time = time.time() - start_time
        status_code = e.response.status_code
        logger.warning(
            f"⚠️ [DISPATCH] Erro HTTP {status_code} do serviço {request.service} - "
            f"endpoint: {endpoint}, response_time: {response_time:.3f}s, "
            f"user: {username}, URL: {target_url}"
        )
        # Tentar extrair mensagem de erro do serviço
        try:
            error_data = e.response.json()
            if isinstance(error_data, dict) and "detail" in error_data:
                error_message = error_data["detail"]
            elif isinstance(error_data, dict) and "message" in error_data:
                error_message = error_data["message"]
            elif isinstance(error_data, dict) and "error" in error_data:
                error_message = error_data["error"]
            else:
                error_message = str(error_data)
        except:
            error_message = e.response.text[:200] if e.response.text else f"Erro HTTP {status_code}"
        
        # Mapear códigos HTTP comuns para mensagens específicas
        if status_code == 404:
            detail_msg = f"Endpoint não encontrado no serviço {request.service}: {endpoint}. Verifique se o endpoint está correto."
        elif status_code == 401:
            detail_msg = f"Autenticação falhou no serviço {request.service}. Token inválido ou expirado."
        elif status_code == 403:
            detail_msg = f"Acesso negado no serviço {request.service}. Você não tem permissão para acessar este recurso."
        elif status_code == 400:
            detail_msg = f"Requisição inválida para o serviço {request.service}: {error_message}"
        elif status_code == 500:
            detail_msg = f"Erro interno no serviço {request.service}: {error_message}"
        elif status_code == 503:
            detail_msg = f"Serviço {request.service} temporariamente indisponível. Tente novamente em alguns instantes."
        else:
            detail_msg = f"Erro HTTP {status_code} do serviço {request.service}: {error_message}"
        
        raise HTTPException(
            status_code=status_code,
            detail=detail_msg
        )
    except httpx.NetworkError as e:
        # Erro de rede genérico
        response_time = time.time() - start_time
        error_msg = str(e)
        logger.error(
            f"🌐 [DISPATCH] Erro de rede ao acessar serviço {request.service} - "
            f"endpoint: {endpoint}, response_time: {response_time:.3f}s, "
            f"user: {username}, error: {error_msg}, URL: {target_url}"
        )
        raise HTTPException(
            status_code=502,
            detail=f"Erro de rede ao acessar serviço {request.service}. Problema de conectividade de rede ou o serviço está inacessível."
        )
    except httpx.RequestError as e:
        # Outros erros de requisição (catch-all para httpx.RequestError)
        # "All connection attempts failed" cai aqui
        response_time = time.time() - start_time
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(
            f"❌ [DISPATCH] Erro na requisição para serviço {request.service} - "
            f"endpoint: {endpoint}, response_time: {response_time:.3f}s, "
            f"user: {username}, error_type: {error_type}, error: {error_msg}, URL: {target_url}"
        )
        # Mensagem específica para "All connection attempts failed"
        if "All connection attempts failed" in error_msg or "connection" in error_msg.lower():
            raise HTTPException(
                status_code=502,
                detail=f"Serviço {request.service} está offline ou indisponível. Não foi possível estabelecer conexão. Todas as tentativas de conexão falharam."
            )
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao comunicar com o serviço {request.service}: {error_msg}"
        )
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(
            f"Erro inesperado ao acessar serviço {request.service} - "
            f"endpoint: {endpoint}, error: {str(e)}, "
            f"user: {username}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao acessar serviço {request.service}: {str(e)}"
        )


# Router adicional para compatibilidade com URL antiga /api/v1/gateway/dispatch
# Mantém as mesmas rotas mas com prefix diferente
legacy_router = APIRouter(prefix="/api/v1/gateway", tags=["Gateway (Legacy)"])

# Reutilizar as mesmas funções do router principal
legacy_router.get("/health")(gateway_health)
legacy_router.get("/status")(gateway_status)
legacy_router.options("/dispatch")(dispatch_options)
legacy_router.post("/dispatch")(dispatch_request)
