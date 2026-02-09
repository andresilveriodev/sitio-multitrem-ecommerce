"""
Serviço de cache para otimização de respostas
"""

import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
import structlog
from cachetools import TTLCache

from config import settings

logger = structlog.get_logger(__name__)


class CacheService:
    """Serviço de cache para otimizar respostas"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.memory_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutos
        self.cache_hits = 0
        self.cache_misses = 0
        
    async def connect(self):
        """Conecta ao Redis"""
        try:
            self.redis = redis.from_url(settings.REDIS_URL)
            await self.redis.ping()
            logger.info("Conectado ao Redis com sucesso")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Desconecta do Redis"""
        if self.redis:
            await self.redis.close()
    
    def _generate_cache_key(self, user_id: str, message: str, context_hash: str = "") -> str:
        """Gera chave única para cache"""
        content = f"{user_id}:{message}:{context_hash}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_cached_response(self, user_id: str, message: str, context_hash: str = "") -> Optional[Dict]:
        """Busca resposta em cache"""
        cache_key = self._generate_cache_key(user_id, message, context_hash)
        
        # Primeiro tenta cache em memória
        if cache_key in self.memory_cache:
            self.cache_hits += 1
            logger.debug(f"Cache hit em memória para chave: {cache_key}")
            return self.memory_cache[cache_key]
        
        # Depois tenta Redis
        if self.redis:
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    response = json.loads(cached_data)
                    # Adiciona ao cache em memória
                    self.memory_cache[cache_key] = response
                    self.cache_hits += 1
                    logger.debug(f"Cache hit no Redis para chave: {cache_key}")
                    return response
            except Exception as e:
                logger.error(f"Erro ao buscar no Redis: {e}")
        
        self.cache_misses += 1
        return None
    
    async def cache_response(self, user_id: str, message: str, response: Dict, 
                           context_hash: str = "", ttl: int = 3600) -> bool:
        """Armazena resposta em cache"""
        cache_key = self._generate_cache_key(user_id, message, context_hash)
        
        # Adiciona metadados de cache
        cache_data = {
            **response,
            "cached_at": datetime.utcnow().isoformat(),
            "cache_key": cache_key,
            "ttl": ttl
        }
        
        # Cache em memória
        self.memory_cache[cache_key] = cache_data
        
        # Cache no Redis
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key,
                    ttl,
                    json.dumps(cache_data, ensure_ascii=False)
                )
                logger.debug(f"Resposta cacheada com chave: {cache_key}")
                return True
            except Exception as e:
                logger.error(f"Erro ao cachear no Redis: {e}")
                return False
        
        return True
    
    async def invalidate_user_cache(self, user_id: str) -> bool:
        """Invalida cache de um usuário específico"""
        if self.redis:
            try:
                pattern = f"*{user_id}:*"
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
                    logger.info(f"Cache invalidado para usuário {user_id}: {len(keys)} chaves")
                return True
            except Exception as e:
                logger.error(f"Erro ao invalidar cache: {e}")
                return False
        return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            "memory_cache_size": len(self.memory_cache),
            "redis_connected": self.redis is not None
        }
    
    async def clear_cache(self) -> bool:
        """Limpa todo o cache"""
        # Limpa cache em memória
        self.memory_cache.clear()
        
        # Limpa Redis
        if self.redis:
            try:
                await self.redis.flushdb()
                logger.info("Cache limpo com sucesso")
                return True
            except Exception as e:
                logger.error(f"Erro ao limpar cache: {e}")
                return False
        
        return True


# Instância global do serviço de cache
cache_service = CacheService()
