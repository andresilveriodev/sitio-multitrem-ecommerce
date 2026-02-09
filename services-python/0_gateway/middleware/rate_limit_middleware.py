"""
Middleware de Rate Limiting
Responsável por limitar requisições por IP/usuário
"""

import time
import json
from collections import defaultdict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Tuple
import logging
import redis.asyncio as redis

from ..config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """Middleware para rate limiting"""
    
    def __init__(self, app):
        self.app = app
        self.redis_client = None
        self.memory_store = defaultdict(list)  # Fallback para memória
        
        # Configurações de rate limiting
        self.rate_limit_per_minute = settings.RATE_LIMIT_PER_MINUTE
        self.rate_limit_per_hour = settings.RATE_LIMIT_PER_HOUR
        
        # Paths que não precisam de rate limiting
        self.exempt_paths = {
            "/health",
            "/api/v1/status",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Verificar se o path está isento
        if self._is_exempt_path(request.url.path):
            await self.app(scope, receive, send)
            return
        
        # Obter identificador do cliente
        client_id = self._get_client_id(request)
        
        # Verificar rate limit
        if not await self._check_rate_limit(client_id):
            await self._send_rate_limit_response(send, client_id)
            return
        
        await self.app(scope, receive, send)
    
    def _is_exempt_path(self, path: str) -> bool:
        """Verifica se o path está isento de rate limiting"""
        return path in self.exempt_paths
    
    def _get_client_id(self, request: Request) -> str:
        """Obtém identificador único do cliente"""
        # Priorizar IP real se estiver atrás de proxy
        client_ip = request.headers.get("X-Real-IP") or \
                   request.headers.get("X-Forwarded-For") or \
                   request.client.host
        
        # Se houver usuário autenticado, usar como parte do ID
        user_id = request.scope.get("user", {}).get("id", "anonymous")
        
        return f"{client_ip}:{user_id}"
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """Verifica se o cliente está dentro do rate limit"""
        current_time = time.time()
        
        try:
            # Tentar usar Redis primeiro
            if not self.redis_client:
                self.redis_client = redis.from_url(settings.REDIS_URL)
            
            # Verificar rate limit por minuto
            minute_key = f"rate_limit:{client_id}:minute:{int(current_time / 60)}"
            minute_count = await self.redis_client.get(minute_key)
            
            if minute_count and int(minute_count) >= self.rate_limit_per_minute:
                return False
            
            # Verificar rate limit por hora
            hour_key = f"rate_limit:{client_id}:hour:{int(current_time / 3600)}"
            hour_count = await self.redis_client.get(hour_key)
            
            if hour_count and int(hour_count) >= self.rate_limit_per_hour:
                return False
            
            # Incrementar contadores
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)  # Expira em 1 minuto
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)  # Expira em 1 hora
            await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.warning(f"Erro no Redis, usando fallback em memória: {e}")
            return self._check_rate_limit_memory(client_id, current_time)
    
    def _check_rate_limit_memory(self, client_id: str, current_time: float) -> bool:
        """Fallback para rate limiting em memória"""
        if client_id not in self.memory_store:
            self.memory_store[client_id] = []
        
        # Limpar registros antigos
        self.memory_store[client_id] = [
            timestamp for timestamp in self.memory_store[client_id]
            if current_time - timestamp < 3600  # Manter apenas última hora
        ]
        
        # Verificar rate limit por minuto
        minute_ago = current_time - 60
        requests_last_minute = len([
            timestamp for timestamp in self.memory_store[client_id]
            if timestamp > minute_ago
        ])
        
        if requests_last_minute >= self.rate_limit_per_minute:
            return False
        
        # Verificar rate limit por hora
        if len(self.memory_store[client_id]) >= self.rate_limit_per_hour:
            return False
        
        # Adicionar registro atual
        self.memory_store[client_id].append(current_time)
        return True
    
    async def _send_rate_limit_response(self, send, client_id: str):
        """Envia resposta de rate limit excedido"""
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": "Muitas requisições. Tente novamente em alguns minutos.",
                "client_id": client_id,
                "timestamp": time.time(),
                "limits": {
                    "per_minute": self.rate_limit_per_minute,
                    "per_hour": self.rate_limit_per_hour
                }
            }
        )
        
        await response(scope, receive, send)


class RateLimitConfig:
    """Configurações de rate limiting por endpoint"""
    
    def __init__(self):
        self.endpoint_limits = {
            "/api/v1/reports": {"per_minute": 5, "per_hour": 50},
            "/api/v1/ai": {"per_minute": 20, "per_hour": 200},
            "/api/v1/chatbot": {"per_minute": 15, "per_hour": 150}
        }
    
    def get_limits_for_path(self, path: str) -> Dict[str, int]:
        """Obtém limites para um path específico"""
        for endpoint, limits in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return limits
        
        # Limites padrão
        return {
            "per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "per_hour": settings.RATE_LIMIT_PER_HOUR
        }
