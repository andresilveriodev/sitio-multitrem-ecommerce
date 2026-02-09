"""
Router base genérico para microserviços
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import httpx
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from ..config import settings
from ..middleware import get_current_user

logger = logging.getLogger(__name__)


class BaseServiceRouter:
    """Router base para todos os microserviços"""
    
    def __init__(self, service_url: str, service_name: str, require_auth: bool = True):
        self.service_url = service_url
        self.service_name = service_name
        self.require_auth = require_auth
        self.router = APIRouter()
        
        # Registrar rotas dinamicamente
        self._register_routes()
    
    def _register_routes(self):
        """Registra todas as rotas HTTP"""
        
        @self.router.api_route("/{path:path}", methods=["GET"])
        async def get_route(request: Request, path: str, current_user: Optional[Dict[str, Any]] = Depends(self._get_user_dependency())):
            """Rota GET genérica"""
            return await self._forward_request(request, "GET", path)
        
        @self.router.api_route("/{path:path}", methods=["POST"])
        async def post_route(request: Request, path: str, current_user: Optional[Dict[str, Any]] = Depends(self._get_user_dependency())):
            """Rota POST genérica"""
            return await self._forward_request(request, "POST", path)
        
        @self.router.api_route("/{path:path}", methods=["PUT"])
        async def put_route(request: Request, path: str, current_user: Optional[Dict[str, Any]] = Depends(self._get_user_dependency())):
            """Rota PUT genérica"""
            return await self._forward_request(request, "PUT", path)
        
        @self.router.api_route("/{path:path}", methods=["DELETE"])
        async def delete_route(request: Request, path: str, current_user: Optional[Dict[str, Any]] = Depends(self._get_user_dependency())):
            """Rota DELETE genérica"""
            return await self._forward_request(request, "DELETE", path)
        
        @self.router.api_route("/{path:path}", methods=["PATCH"])
        async def patch_route(request: Request, path: str, current_user: Optional[Dict[str, Any]] = Depends(self._get_user_dependency())):
            """Rota PATCH genérica"""
            return await self._forward_request(request, "PATCH", path)
    
    def _get_user_dependency(self):
        """Retorna dependency de usuário baseado na configuração"""
        if self.require_auth:
            return get_current_user
        else:
            return lambda: None
    
    async def _forward_request(self, request: Request, method: str, path: str):
        """Encaminha requisição para o microserviço"""
        try:
            # Construir URL completa
            full_url = urljoin(self.service_url, path)
            
            # Preparar headers
            headers = dict(request.headers)
            
            # Remover headers que não devem ser encaminhados
            headers_to_remove = [
                "host", "content-length", "transfer-encoding"
            ]
            for header in headers_to_remove:
                headers.pop(header.lower(), None)
            
            # Preparar query params
            query_params = dict(request.query_params)
            
            # Preparar body para métodos que suportam
            body = None
            if method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.json()
                except:
                    body = await request.body()
            
            # Fazer requisição para o microserviço
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=full_url,
                    params=query_params,
                    json=body if isinstance(body, dict) else None,
                    content=body if not isinstance(body, dict) else None,
                    headers=headers,
                    timeout=settings.REQUEST_TIMEOUT
                )
                
                # Retornar resposta
                return JSONResponse(
                    status_code=response.status_code,
                    content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                    headers=dict(response.headers)
                )
                
        except httpx.TimeoutException:
            logger.error(f"Timeout ao acessar {self.service_name}: {path}")
            raise HTTPException(status_code=504, detail=f"Timeout ao acessar {self.service_name}")
            
        except httpx.ConnectError:
            logger.error(f"Erro de conexão com {self.service_name}: {path}")
            raise HTTPException(status_code=503, detail=f"Serviço {self.service_name} indisponível")
            
        except Exception as e:
            logger.error(f"Erro ao acessar {self.service_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Erro interno ao acessar {self.service_name}")


def create_service_router(service_url: str, service_name: str, require_auth: bool = True) -> APIRouter:
    """Factory para criar router de serviço"""
    router_instance = BaseServiceRouter(service_url, service_name, require_auth)
    return router_instance.router
