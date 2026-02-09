"""
Middleware de Autenticação
Responsável por validar tokens JWT e autorização
"""

import jwt
import httpx
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import logging
import time

from ..config import settings

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """Middleware para autenticação e autorização"""
    
    def __init__(self, app):
        self.app = app
        self.public_paths = {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/status",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/verify"
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Verificar se é um caminho público
        if self._is_public_path(request.url.path):
            await self.app(scope, receive, send)
            return
        
        # Extrair token do header
        token = self._extract_token(request)
        if not token:
            await self._send_unauthorized_response(send, "Token não fornecido")
            return
        
        # Validar token
        try:
            user_info = await self._validate_token(token)
            if not user_info:
                await self._send_unauthorized_response(send, "Token inválido")
                return
            
            # Adicionar informações do usuário ao scope
            scope["user"] = user_info
            
            await self.app(scope, receive, send)
            
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            await self._send_unauthorized_response(send, "Erro na autenticação")
    
    def _is_public_path(self, path: str) -> bool:
        """Verifica se o caminho é público"""
        return path in self.public_paths or path.startswith("/static/")
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extrai o token do header Authorization"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer "
        
        return None
    
    async def _validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida o token JWT"""
        try:
            # Decodificar token
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Verificar se o token não expirou
            if payload.get("exp") and payload["exp"] < time.time():
                return None
            
            # Verificar com o serviço de usuário (user_service na porta 8001)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.USER_SERVICE_URL}/api/v1/auth/verify",
                    json={"token": token},
                    timeout=settings.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Erro ao validar token: {e}")
            return None
    
    async def _send_unauthorized_response(self, send, message: str):
        """Envia resposta de não autorizado"""
        response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "Unauthorized",
                "message": message,
                "timestamp": time.time()
            }
        )
        
        await response(scope, receive, send)


def get_current_user(request: Request) -> Dict[str, Any]:
    """Dependency para obter usuário atual"""
    user = request.scope.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado"
        )
    return user


def require_permission(permission: str):
    """Decorator para verificar permissões"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request não encontrado"
                )
            
            user = get_current_user(request)
            user_permissions = user.get("permissions", [])
            
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permissão '{permission}' requerida"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
