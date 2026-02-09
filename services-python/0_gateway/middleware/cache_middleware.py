"""
Middleware de Cache
Responsável por cachear respostas de requisições
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any
import logging
import redis.asyncio as redis

from ..config import settings

logger = logging.getLogger(__name__)


class CacheMiddleware:
    """Middleware para cache de respostas"""
    
    def __init__(self, app):
        self.app = app
        self.redis_client = None
        
        # Configurações de cache
        self.default_ttl = settings.CACHE_TTL
        
        # Endpoints que devem ser cacheados
        self.cacheable_endpoints = {
            "/api/v1/users/profile": {"ttl": 600},  # 10 minutos para perfil
            "/api/v1/reports": {"ttl": 1800},  # 30 minutos para relatórios
        }
        
        # Headers que invalidam cache
        self.cache_busting_headers = {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = scope.get("request")
        if not request:
            # Criar request se não existir
            from fastapi import Request
            request = Request(scope, receive)
            scope["request"] = request
        
        # Verificar se o endpoint é cacheável
        if not self._is_cacheable_endpoint(request.url.path):
            await self.app(scope, receive, send)
            return
        
        # Verificar se há headers que invalidam cache
        if self._has_cache_busting_headers(request):
            await self.app(scope, receive, send)
            return
        
        # Gerar chave do cache
        cache_key = self._generate_cache_key(request)
        
        # Tentar obter do cache
        cached_response = await self._get_from_cache(cache_key)
        if cached_response:
            await self._send_cached_response(send, cached_response)
            return
        
        # Se não estiver em cache, processar normalmente
        await self.app(scope, receive, send)
    
    def _is_cacheable_endpoint(self, path: str) -> bool:
        """Verifica se o endpoint deve ser cacheado"""
        return any(path.startswith(endpoint) for endpoint in self.cacheable_endpoints.keys())
    
    def _has_cache_busting_headers(self, request) -> bool:
        """Verifica se há headers que invalidam cache"""
        for header_name, header_value in self.cache_busting_headers.items():
            if request.headers.get(header_name) == header_value:
                return True
        return False
    
    def _generate_cache_key(self, request) -> str:
        """Gera chave única para o cache"""
        # Incluir path, query params e headers relevantes
        key_parts = [
            request.url.path,
            str(sorted(request.query_params.items())),
            request.headers.get("authorization", ""),
            request.headers.get("accept", "")
        ]
        
        # Adicionar ID do usuário se autenticado
        user = request.scope.get("user")
        if user:
            key_parts.append(str(user.get("id", "")))
        
        key_string = "|".join(key_parts)
        return f"gateway:cache:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Obtém resposta do cache"""
        try:
            if not self.redis_client:
                self.redis_client = redis.from_url(settings.REDIS_URL)
            
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            
        except Exception as e:
            logger.warning(f"Erro ao acessar cache: {e}")
        
        return None
    
    async def _set_cache(self, cache_key: str, response_data: Dict[str, Any], ttl: int):
        """Armazena resposta no cache"""
        try:
            if not self.redis_client:
                self.redis_client = redis.from_url(settings.REDIS_URL)
            
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(response_data)
            )
            
        except Exception as e:
            logger.warning(f"Erro ao armazenar no cache: {e}")
    
    async def _send_cached_response(self, send, cached_response: Dict[str, Any]):
        """Envia resposta cacheadada"""
        from fastapi.responses import JSONResponse
        
        response = JSONResponse(
            status_code=cached_response["status_code"],
            content=cached_response["content"],
            headers=cached_response.get("headers", {})
        )
        
        await response(scope, receive, send)
    
    def _get_cache_ttl(self, path: str) -> int:
        """Obtém TTL para um endpoint específico"""
        for endpoint, config in self.cacheable_endpoints.items():
            if path.startswith(endpoint):
                return config["ttl"]
        
        return self.default_ttl


class CacheManager:
    """Gerenciador de cache para operações manuais"""
    
    def __init__(self):
        self.redis_client = None
    
    async def get_client(self):
        """Obtém cliente Redis"""
        if not self.redis_client:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        return self.redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache"""
        try:
            client = await self.get_client()
            data = await client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Erro ao obter cache: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None):
        """Define valor no cache"""
        try:
            client = await self.get_client()
            if ttl:
                await client.setex(key, ttl, json.dumps(value))
            else:
                await client.set(key, json.dumps(value))
        except Exception as e:
            logger.error(f"Erro ao definir cache: {e}")
    
    async def delete(self, key: str):
        """Remove valor do cache"""
        try:
            client = await self.get_client()
            await client.delete(key)
        except Exception as e:
            logger.error(f"Erro ao deletar cache: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalida cache por padrão"""
        try:
            client = await self.get_client()
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
        except Exception as e:
            logger.error(f"Erro ao invalidar cache por padrão: {e}")
    
    async def clear_all(self):
        """Limpa todo o cache"""
        try:
            client = await self.get_client()
            await client.flushdb()
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")


# Instância global do gerenciador de cache
cache_manager = CacheManager()
