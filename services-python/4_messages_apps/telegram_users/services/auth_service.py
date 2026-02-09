"""
Serviço de autenticação para usuários do Telegram
Verifica se o usuário existe no e-commerce e obtém credenciais necessárias
"""

import os
import httpx
import structlog
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from config import settings

logger = structlog.get_logger(__name__)


class TelegramAuthService:
    """Serviço de autenticação para usuários do Telegram"""
    
    def __init__(self):
        # URL do Gateway Service (que roteia para User Service)
        self.gateway_url = os.getenv("GATEWAY_SERVICE_URL", "http://localhost:8000")
        self.user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
        self.client: Optional[httpx.AsyncClient] = None
        # Cache de tokens por telegram_user_id (TTL de 1 hora)
        self._token_cache: Dict[str, Dict[str, Any]] = {}
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtém ou cria cliente HTTP"""
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
            )
        return self.client
    
    async def close(self):
        """Fecha cliente HTTP"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def find_user_by_telegram_id(
        self, 
        telegram_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Busca usuário no e-commerce pelo ID do Telegram
        
        Args:
            telegram_user_id: ID do usuário do Telegram
            
        Returns:
            Dados do usuário se encontrado, None caso contrário
        """
        try:
            client = await self._get_client()
            
            # Tentar buscar via Gateway Service primeiro
            url = f"{self.gateway_url}/api/v1/users/telegram/{telegram_user_id}"
            
            logger.info(
                "Buscando usuário por telegram_id",
                telegram_user_id=telegram_user_id,
                url=url
            )
            
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    user_data = response.json()
                    logger.info(
                        "Usuário encontrado no e-commerce",
                        telegram_user_id=telegram_user_id,
                        user_id=user_data.get("id")
                    )
                    return user_data
                elif response.status_code == 404:
                    logger.info(
                        "Usuário não encontrado no e-commerce",
                        telegram_user_id=telegram_user_id
                    )
                    return None
            except httpx.HTTPError as e:
                logger.warning(
                    "Erro ao buscar usuário via Gateway, tentando User Service diretamente",
                    error=str(e)
                )
                # Fallback: tentar User Service diretamente
                url = f"{self.user_service_url}/api/v1/users/telegram/{telegram_user_id}"
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
            
            return None
            
        except Exception as e:
            logger.error(
                "Erro ao buscar usuário por telegram_id",
                telegram_user_id=telegram_user_id,
                error=str(e),
                exc_info=True
            )
            return None
    
    async def get_user_credentials(
        self,
        telegram_user_id: str,
        username: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém credenciais do usuário (token JWT) se autenticado
        
        Args:
            telegram_user_id: ID do usuário do Telegram
            username: Nome de usuário do Telegram (opcional)
            
        Returns:
            Dict com user_id, token, permissions ou None se não autenticado
        """
        try:
            # Verificar cache primeiro
            cache_key = f"telegram_{telegram_user_id}"
            if cache_key in self._token_cache:
                cached = self._token_cache[cache_key]
                # Verificar se não expirou (1 hora)
                if datetime.utcnow() < cached.get("expires_at", datetime.utcnow()):
                    logger.debug("Usando credenciais do cache", telegram_user_id=telegram_user_id)
                    return cached.get("credentials")
                else:
                    # Remover do cache se expirado
                    del self._token_cache[cache_key]
            
            # Buscar usuário no e-commerce
            user_data = await self.find_user_by_telegram_id(telegram_user_id)
            
            if not user_data:
                logger.info(
                    "Usuário não encontrado no e-commerce - acesso limitado",
                    telegram_user_id=telegram_user_id
                )
                return None
            
            # Se usuário encontrado, obter token JWT
            # Nota: Para obter token, precisaríamos de username/password
            # Por enquanto, retornamos os dados do usuário
            # O token seria obtido via login ou refresh token armazenado
            
            credentials = {
                "user_id": user_data.get("id"),
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "keycloak_id": user_data.get("keycloak_id"),
                "is_authenticated": True,
                "permissions": user_data.get("permissions", []),
                "profiles": user_data.get("profiles", [])
            }
            
            # Cachear credenciais (sem token por enquanto)
            self._token_cache[cache_key] = {
                "credentials": credentials,
                "expires_at": datetime.utcnow() + timedelta(hours=1)
            }
            
            logger.info(
                "Credenciais obtidas com sucesso",
                telegram_user_id=telegram_user_id,
                user_id=credentials.get("user_id")
            )
            
            return credentials
            
        except Exception as e:
            logger.error(
                "Erro ao obter credenciais do usuário",
                telegram_user_id=telegram_user_id,
                error=str(e),
                exc_info=True
            )
            return None
    
    async def check_user_permission(
        self,
        telegram_user_id: str,
        permission: str
    ) -> bool:
        """
        Verifica se o usuário tem uma permissão específica
        
        Args:
            telegram_user_id: ID do usuário do Telegram
            permission: Nome da permissão (ex: "chatbot:use", "orders:create")
            
        Returns:
            True se tem permissão, False caso contrário
        """
        try:
            credentials = await self.get_user_credentials(telegram_user_id)
            
            if not credentials or not credentials.get("is_authenticated"):
                logger.info(
                    "Usuário não autenticado - sem permissão",
                    telegram_user_id=telegram_user_id,
                    permission=permission
                )
                return False
            
            permissions = credentials.get("permissions", [])
            has_permission = permission in permissions or "admin" in permissions
            
            logger.debug(
                "Verificação de permissão",
                telegram_user_id=telegram_user_id,
                permission=permission,
                has_permission=has_permission
            )
            
            return has_permission
            
        except Exception as e:
            logger.error(
                "Erro ao verificar permissão",
                telegram_user_id=telegram_user_id,
                permission=permission,
                error=str(e)
            )
            return False
    
    def clear_cache(self, telegram_user_id: Optional[str] = None):
        """Limpa cache de credenciais"""
        if telegram_user_id:
            cache_key = f"telegram_{telegram_user_id}"
            if cache_key in self._token_cache:
                del self._token_cache[cache_key]
                logger.info("Cache limpo para usuário", telegram_user_id=telegram_user_id)
        else:
            self._token_cache.clear()
            logger.info("Cache de credenciais limpo completamente")


# Instância global do serviço de autenticação
telegram_auth_service = TelegramAuthService()
