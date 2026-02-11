"""
Serviço de autenticação OAuth com Keycloak para usuários do Telegram
Adaptado da implementação Java do projeto b3/telegram
"""

import httpx
import structlog
import secrets
import jwt
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode
from config import settings

logger = structlog.get_logger(__name__)


class KeycloakAuthService:
    """Serviço para autenticação OAuth com Keycloak"""
    
    def __init__(self):
        self.auth_server_url = settings.KEYCLOAK_AUTH_SERVER_URL.rstrip('/')
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        self.redirect_uri = settings.KEYCLOAK_REDIRECT_URI
        self.scope = settings.KEYCLOAK_SCOPE
        self.service_base_url = settings.SERVICE_BASE_URL.rstrip('/')
        
        # URLs do Keycloak
        self.authorization_url = f"{self.auth_server_url}/realms/{self.realm}/protocol/openid-connect/auth"
        self.token_url = f"{self.auth_server_url}/realms/{self.realm}/protocol/openid-connect/token"
        self.userinfo_url = f"{self.auth_server_url}/realms/{self.realm}/protocol/openid-connect/userinfo"
        self.logout_url = f"{self.auth_server_url}/realms/{self.realm}/protocol/openid-connect/logout"
        
        # UserTrackerStorage: mapeia state -> telegram_user_id (expira em 30 minutos)
        self._user_trackers: Dict[str, Dict[str, Any]] = {}
        # TokenStorage: armazena tokens por telegram_user_id com expiração automática
        self._user_tokens: Dict[str, Dict[str, Any]] = {}
        
        self.client: Optional[httpx.AsyncClient] = None
    
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
    
    def generate_authorization_url(
        self,
        telegram_user_id: str,
        telegram_chat_id: Optional[str] = None,
        state: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Gera URL de autorização do Keycloak (adaptado de OidcService.getAuthUrl)
        
        Args:
            telegram_user_id: ID do usuário no Telegram
            telegram_chat_id: ID do chat no Telegram (opcional)
            state: Estado OAuth (se None, será gerado como UUID)
            
        Returns:
            Tupla (authorization_url, state)
        """
        if not state:
            # Gerar state como UUID (similar ao Java)
            state = secrets.token_urlsafe(32)
        
        # UserTrackerStorage: armazenar state -> telegram_user_id (expira em 30 minutos)
        self._user_trackers[state] = {
            "telegram_user_id": telegram_user_id,
            "telegram_chat_id": telegram_chat_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=30)  # 30 minutos como no Java
        }
        
        # Parâmetros para a URL de autorização (scope inclui offline_access para refresh token)
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": f"{self.scope} offline_access",  # offline_access para refresh token
            "state": state
        }
        
        authorization_url = f"{self.authorization_url}?{urlencode(params)}"
        
        logger.info(
            "URL de autorização gerada",
            telegram_user_id=telegram_user_id,
            state=state[:8] + "..."  # Log apenas parte do state por segurança
        )
        
        return authorization_url, state
    
    async def exchange_code_for_tokens(self, code: str, state: str) -> Optional[Dict[str, Any]]:
        """
        Completa autenticação trocando code por tokens (adaptado de OidcService.completeAuth)
        
        Args:
            code: Código de autorização retornado pelo Keycloak
            state: Estado OAuth para validação
            
        Returns:
            Dict com UserInfo ou None se falhar
        """
        try:
            # UserTrackerStorage: buscar telegram_user_id pelo state (e remover após uso)
            tracker_data = self._user_trackers.pop(state, None)
            
            if not tracker_data:
                logger.warning("State inválido ou expirado", state=state[:8] + "...")
                return None
            
            # Verificar se state não expirou
            if datetime.utcnow() > tracker_data["expires_at"]:
                logger.warning("State expirado", state=state[:8] + "...")
                return None
            
            telegram_user_id = tracker_data["telegram_user_id"]
            telegram_chat_id = tracker_data.get("telegram_chat_id")
            
            # Obter tokens do Keycloak
            tokens = await self._request_token(code)
            
            if not tokens:
                logger.error("Erro ao obter tokens do Keycloak")
                return None
            
            # Extrair UserInfo do id_token (JWT) - similar a UserInfo.of()
            userinfo = self._extract_userinfo_from_id_token(tokens.get("id_token"))
            
            if not userinfo:
                logger.error("Erro ao extrair informações do usuário do id_token")
                return None
            
            # TokenStorage: armazenar tokens com expiração
            expires_in = tokens.get("expires_in", 3600)
            self._user_tokens[telegram_user_id] = {
                "access_token": tokens.get("access_token"),
                "refresh_token": tokens.get("refresh_token"),  # offline token
                "id_token": tokens.get("id_token"),
                "expires_in": expires_in,
                "refresh_expires_in": tokens.get("refresh_expires_in"),
                "token_type": tokens.get("token_type", "Bearer"),
                "userinfo": userinfo,
                "authenticated_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(seconds=expires_in)
            }
            
            logger.info(
                "Autenticação completada com sucesso",
                telegram_user_id=telegram_user_id,
                keycloak_user_id=userinfo.get("sub"),
                preferred_username=userinfo.get("preferred_username")
            )
            
            return {
                "telegram_user_id": telegram_user_id,
                "telegram_chat_id": telegram_chat_id,
                "userinfo": userinfo
            }
            
        except Exception as e:
            logger.error(
                "Erro ao completar autenticação",
                error=str(e),
                exc_info=True
            )
            return None
    
    async def _request_token(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Solicita tokens do Keycloak (adaptado de OidcService.requestToken)
        """
        try:
            client = await self._get_client()
            
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = await client.post(
                self.token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error(
                    "Erro ao obter tokens do Keycloak",
                    status_code=response.status_code,
                    response=response.text
                )
                return None
            
            return response.json()
            
        except Exception as e:
            logger.error("Erro ao solicitar token", error=str(e), exc_info=True)
            return None
    
    def _extract_userinfo_from_id_token(self, id_token: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Extrai informações do usuário do id_token JWT (adaptado de UserInfo.of)
        """
        if not id_token:
            return None
        
        try:
            # Decodificar JWT sem verificar assinatura (para extrair claims)
            # Em produção, deveria verificar a assinatura
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            
            userinfo = {
                "sub": decoded.get("sub"),  # Subject (Keycloak user ID)
                "preferred_username": decoded.get("preferred_username"),
                "email": decoded.get("email"),
                "name": decoded.get("name"),
                "given_name": decoded.get("given_name"),
                "family_name": decoded.get("family_name"),
                "email_verified": decoded.get("email_verified", False)
            }
            
            return userinfo
            
        except Exception as e:
            logger.error("Erro ao decodificar id_token", error=str(e))
            return None
    
    async def _get_userinfo(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Obtém informações do usuário do Keycloak"""
        try:
            client = await self._get_client()
            response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    "Erro ao obter userinfo",
                    status_code=response.status_code
                )
                return None
                
        except Exception as e:
            logger.error("Erro ao obter userinfo", error=str(e))
            return None
    
    def get_user_auth_status(self, telegram_user_id: str) -> Dict[str, Any]:
        """
        Verifica status de autenticação do usuário (adaptado de OidcService.findUserInfo)
        
        Returns:
            Dict com status de autenticação e UserInfo se autenticado
        """
        # LOGGING PARA DEBUG
        logger.debug(f"Verificando autenticação para user_id={telegram_user_id}, tokens armazenados: {list(self._user_tokens.keys())}")
        
        if telegram_user_id not in self._user_tokens:
            logger.debug(f"Usuário {telegram_user_id} NÃO encontrado em _user_tokens - retornando is_authenticated=False")
            return {
                "is_authenticated": False,
                "telegram_user_id": telegram_user_id
            }
        
        token_data = self._user_tokens[telegram_user_id]
        
        # Verificar se token expirou (TokenStorage faz refresh automático)
        expires_at = token_data.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            logger.debug(f"Token expirado para user_id={telegram_user_id}, expires_at={expires_at}")
            # Tentar refresh se tiver refresh_token (offline token)
            if token_data.get("refresh_token"):
                # Refresh será feito de forma assíncrona quando necessário
                logger.debug(f"Token expirado mas tem refresh_token - retornando needs_refresh=True")
                return {
                    "is_authenticated": False,
                    "needs_refresh": True,
                    "telegram_user_id": telegram_user_id
                }
            else:
                # Token expirado e sem refresh_token
                logger.debug(f"Token expirado e sem refresh_token - removendo tokens")
                del self._user_tokens[telegram_user_id]
                return {
                    "is_authenticated": False,
                    "telegram_user_id": telegram_user_id
                }
        
        # Verificar se tem access_token válido
        if not token_data.get("access_token"):
            logger.debug(f"Usuário {telegram_user_id} não tem access_token - retornando is_authenticated=False")
            del self._user_tokens[telegram_user_id]
            return {
                "is_authenticated": False,
                "telegram_user_id": telegram_user_id
            }
        
        # Retornar UserInfo similar ao Java
        userinfo = token_data.get("userinfo", {})
        logger.debug(f"Usuário {telegram_user_id} está autenticado - retornando is_authenticated=True")
        return {
            "is_authenticated": True,
            "telegram_user_id": telegram_user_id,
            "userinfo": userinfo,
            "authenticated_at": token_data.get("authenticated_at").isoformat() if token_data.get("authenticated_at") else None
        }
    
    def find_user_info(self, telegram_user_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca informações do usuário autenticado (adaptado de OidcService.findUserInfo)
        
        Returns:
            UserInfo se autenticado, None caso contrário
        """
        auth_status = self.get_user_auth_status(telegram_user_id)
        
        if not auth_status.get("is_authenticated"):
            return None
        
        return auth_status.get("userinfo")
    
    def get_access_token(self, telegram_user_id: str) -> Optional[str]:
        """Obtém access token do usuário se autenticado e válido"""
        auth_status = self.get_user_auth_status(telegram_user_id)
        
        if not auth_status.get("is_authenticated"):
            return None
        
        token_data = self._user_tokens[telegram_user_id]
        return token_data.get("access_token")
    
    async def refresh_access_token(self, telegram_user_id: str) -> bool:
        """
        Atualiza access token usando refresh token (adaptado de TokenStorage.refreshAccessToken)
        """
        try:
            if telegram_user_id not in self._user_tokens:
                logger.debug("Token não encontrado para refresh", telegram_user_id=telegram_user_id)
                return False
            
            token_data = self._user_tokens[telegram_user_id]
            refresh_token = token_data.get("refresh_token")  # offline token
            
            if not refresh_token:
                logger.debug("Refresh token não encontrado", telegram_user_id=telegram_user_id)
                return False
            
            client = await self._get_client()
            
            refresh_data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = await client.post(
                self.token_url,
                data=refresh_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error("Erro ao atualizar token", status_code=response.status_code)
                # Remover tokens inválidos
                del self._user_tokens[telegram_user_id]
                return False
            
            tokens = response.json()
            expires_in = tokens.get("expires_in", 3600)
            
            # Atualizar tokens mantendo refresh_token se não vier novo
            token_data["access_token"] = tokens.get("access_token")
            token_data["refresh_token"] = tokens.get("refresh_token", refresh_token)
            token_data["id_token"] = tokens.get("id_token", token_data.get("id_token"))
            token_data["expires_at"] = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Atualizar userinfo se id_token mudou
            if tokens.get("id_token"):
                userinfo = self._extract_userinfo_from_id_token(tokens.get("id_token"))
                if userinfo:
                    token_data["userinfo"] = userinfo
            
            logger.debug("Token atualizado com sucesso", telegram_user_id=telegram_user_id)
            return True
            
        except Exception as e:
            logger.error("Erro ao atualizar token", error=str(e), exc_info=True)
            return False
    
    async def logout(self, telegram_user_id: str) -> bool:
        """Faz logout do usuário"""
        try:
            if telegram_user_id in self._user_tokens:
                token_data = self._user_tokens[telegram_user_id]
                refresh_token = token_data.get("refresh_token")
                
                if refresh_token:
                    # Fazer logout no Keycloak
                    try:
                        client = await self._get_client()
                        await client.post(
                            self.logout_url,
                            data={
                                "client_id": self.client_id,
                                "client_secret": self.client_secret,
                                "refresh_token": refresh_token
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Erro ao fazer logout no Keycloak (continuando com limpeza local): {e}")
                
                # Remover tokens locais
                del self._user_tokens[telegram_user_id]
                logger.info("Logout realizado", telegram_user_id=telegram_user_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Erro ao fazer logout", error=str(e))
            return False
    
    def clear_user_session(self, telegram_user_id: str):
        """
        Limpa a sessão do usuário localmente (sem fazer logout no Keycloak)
        Útil para limpar estado residual mesmo quando não há tokens válidos
        """
        try:
            if telegram_user_id in self._user_tokens:
                del self._user_tokens[telegram_user_id]
                logger.debug("Sessão local limpa", telegram_user_id=telegram_user_id)
            
            # Limpar também qualquer tracker relacionado
            trackers_to_remove = [
                state for state, data in self._user_trackers.items()
                if data.get("telegram_user_id") == telegram_user_id
            ]
            for state in trackers_to_remove:
                del self._user_trackers[state]
                logger.debug("Tracker removido", telegram_user_id=telegram_user_id, state=state[:8] + "...")
                
        except Exception as e:
            logger.error("Erro ao limpar sessão local", error=str(e), telegram_user_id=telegram_user_id)
    
    def cleanup_expired_data(self):
        """
        Remove dados expirados (UserTrackers e Tokens)
        Similar ao comportamento automático do ExpiringMap no Java
        """
        now = datetime.utcnow()
        
        # Limpar UserTrackers expirados
        expired_trackers = [
            state for state, data in self._user_trackers.items()
            if now > data["expires_at"]
        ]
        for state in expired_trackers:
            del self._user_trackers[state]
            logger.debug("UserTracker expirado removido", state=state[:8] + "...")
        
        # Limpar tokens expirados (sem refresh_token)
        expired_tokens = [
            user_id for user_id, token_data in self._user_tokens.items()
            if now > token_data["expires_at"] and not token_data.get("refresh_token")
        ]
        for user_id in expired_tokens:
            del self._user_tokens[user_id]
            logger.debug("Token expirado removido", telegram_user_id=user_id)
        
        if expired_trackers or expired_tokens:
            logger.debug(
                f"Limpeza: {len(expired_trackers)} trackers, {len(expired_tokens)} tokens removidos"
            )


# Instância global do serviço de autenticação Keycloak
keycloak_auth_service = KeycloakAuthService()
