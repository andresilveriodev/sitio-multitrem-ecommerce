import httpx
import structlog
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError
from config import settings

logger = structlog.get_logger()

class KeycloakService:
    """Serviço para integração com Keycloak remoto"""
    
    def __init__(self):
        self.keycloak_openid = KeycloakOpenID(
            server_url=settings.KEYCLOAK_AUTH_SERVER_URL,
            client_id=settings.KEYCLOAK_RESOURCE,
            realm_name=settings.KEYCLOAK_REALM,
            client_secret_key=settings.KEYCLOAK_CREDENTIALS_SECRET,
            verify=False  # ← DESABILITAR VERIFICAÇÃO SSL para debug
        )
        self._token_cache = {}
        self._user_cache = {}
        
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autentica usuário via Keycloak"""
        try:
            logger.info("Tentando autenticar usuário via Keycloak", username=username)
            
            # Obter token do Keycloak
            token = self.keycloak_openid.token(
                username=username,
                password=password
            )
            
            if not token:
                logger.warning("Falha na autenticação Keycloak", username=username)
                return None
            
            # Decodificar token para obter informações do usuário
            user_info = self.keycloak_openid.decode_token(
                token['access_token'],
                key=self.keycloak_openid.public_key(),
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "verify_exp": True
                }
            )
            
            logger.info("Usuário autenticado com sucesso", 
                       username=username, 
                       keycloak_id=user_info.get('sub'))
            
            return {
                'token': token,
                'user_info': user_info,
                'keycloak_id': user_info.get('sub'),
                'username': user_info.get('preferred_username'),
                'email': user_info.get('email'),
                'first_name': user_info.get('given_name'),
                'last_name': user_info.get('family_name'),
                'roles': user_info.get('realm_access', {}).get('roles', []),
                'resource_roles': user_info.get('resource_access', {})
            }
            
        except KeycloakAuthenticationError as e:
            logger.warning("Erro de autenticação Keycloak", 
                          username=username, error=str(e))
            return None
        except Exception as e:
            logger.error("Erro inesperado na autenticação Keycloak", 
                        username=username, error=str(e))
            return None
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida token JWT do Keycloak"""
        try:
            logger.debug("Validando token Keycloak")
            
            # Decodificar e validar token
            user_info = self.keycloak_openid.decode_token(
                token,
                key=self.keycloak_openid.public_key(),
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "verify_exp": True
                }
            )
            
            logger.debug("Token validado com sucesso", 
                        keycloak_id=user_info.get('sub'))
            
            return {
                'keycloak_id': user_info.get('sub'),
                'username': user_info.get('preferred_username'),
                'email': user_info.get('email'),
                'first_name': user_info.get('given_name'),
                'last_name': user_info.get('family_name'),
                'roles': user_info.get('realm_access', {}).get('roles', []),
                'resource_roles': user_info.get('resource_access', {}),
                'exp': user_info.get('exp'),
                'iat': user_info.get('iat')
            }
            
        except KeycloakGetError as e:
            logger.warning("Token inválido", error=str(e))
            return None
        except Exception as e:
            logger.error("Erro ao validar token", error=str(e))
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Renova token via Keycloak"""
        try:
            logger.debug("Renovando token via Keycloak")
            
            # Renovar token
            new_token = self.keycloak_openid.refresh_token(refresh_token)
            
            if not new_token:
                logger.warning("Falha ao renovar token")
                return None
            
            logger.debug("Token renovado com sucesso")
            
            return {
                'access_token': new_token['access_token'],
                'refresh_token': new_token.get('refresh_token'),
                'expires_in': new_token.get('expires_in'),
                'refresh_expires_in': new_token.get('refresh_expires_in')
            }
            
        except Exception as e:
            logger.error("Erro ao renovar token", error=str(e))
            return None
    
    async def get_user_info(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Obtém informações detalhadas do usuário no Keycloak"""
        try:
            logger.debug("Obtendo informações do usuário no Keycloak", 
                        keycloak_id=keycloak_id)
            
            # Verificar cache
            if keycloak_id in self._user_cache:
                cache_entry = self._user_cache[keycloak_id]
                if datetime.now() < cache_entry['expires_at']:
                    logger.debug("Retornando usuário do cache", keycloak_id=keycloak_id)
                    return cache_entry['data']
            
            # Obter usuário do Keycloak
            user_info = self.keycloak_openid.get_userinfo(keycloak_id)
            
            if not user_info:
                logger.warning("Usuário não encontrado no Keycloak", 
                              keycloak_id=keycloak_id)
                return None
            
            # Cache por 5 minutos
            self._user_cache[keycloak_id] = {
                'data': user_info,
                'expires_at': datetime.now() + timedelta(minutes=5)
            }
            
            logger.debug("Informações do usuário obtidas", 
                        keycloak_id=keycloak_id)
            
            return user_info
            
        except Exception as e:
            logger.error("Erro ao obter informações do usuário", 
                        keycloak_id=keycloak_id, error=str(e))
            return None
    
    async def logout_user(self, refresh_token: str) -> bool:
        """Faz logout do usuário no Keycloak"""
        try:
            logger.info("Fazendo logout do usuário no Keycloak")
            
            # Logout no Keycloak
            self.keycloak_openid.logout(refresh_token)
            
            logger.info("Logout realizado com sucesso")
            return True
            
        except Exception as e:
            logger.error("Erro ao fazer logout", error=str(e))
            return False
    
    async def get_user_roles(self, keycloak_id: str) -> List[str]:
        """Obtém roles do usuário no Keycloak"""
        try:
            user_info = await self.get_user_info(keycloak_id)
            if user_info:
                return user_info.get('realm_access', {}).get('roles', [])
            return []
        except Exception as e:
            logger.error("Erro ao obter roles do usuário", 
                        keycloak_id=keycloak_id, error=str(e))
            return []
    
    def clear_cache(self):
        """Limpa cache interno"""
        self._token_cache.clear()
        self._user_cache.clear()
        logger.debug("Cache limpo")
    
    # ==================== MÉTODOS DE ADMIN API ====================
    
    async def get_admin_token(self) -> Optional[str]:
        """Obtém token de admin para operações administrativas"""
        try:
            logger.debug("Obtendo token de admin do Keycloak")
            
            data = {
                "grant_type": "password",
                "client_id": settings.KEYCLOAK_ADMIN_CLIENT_ID,
                "username": settings.KEYCLOAK_ADMIN_USERNAME,
                "password": settings.KEYCLOAK_ADMIN_PASSWORD,
            }
            
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/realms/{settings.KEYCLOAK_ADMIN_REALM}/protocol/openid-connect/token", 
                    data=data
                )
                r.raise_for_status()
                token_data = r.json()
                
                logger.debug("Token de admin obtido com sucesso")
                return token_data["access_token"]
                
        except Exception as e:
            logger.error("Erro ao obter token de admin", error=str(e))
            return None
    
    async def check_user_exists(self, cpf: str = None, email: str = None) -> Optional[Dict[str, Any]]:
        """Verifica se usuário já existe no Keycloak por CPF ou email"""
        try:
            token = await self.get_admin_token()
            if not token:
                return None
            
            # Buscar por CPF
            if cpf:
                cpf_clean = re.sub(r'[^0-9]', '', cpf)
                async with httpx.AsyncClient() as client:
                    r = await client.get(
                        f"{settings.KEYCLOAK_AUTH_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users",
                        params={"username": cpf_clean},
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    r.raise_for_status()
                    users = r.json()
                    if users:
                        logger.info("Usuário encontrado por CPF", cpf=cpf_clean)
                        return users[0]
            
            # Buscar por email
            if email:
                async with httpx.AsyncClient() as client:
                    r = await client.get(
                        f"{settings.KEYCLOAK_AUTH_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users",
                        params={"email": email},
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    r.raise_for_status()
                    users = r.json()
                    if users:
                        logger.info("Usuário encontrado por email", email=email)
                        return users[0]
            
            return None
            
        except Exception as e:
            logger.error("Erro ao verificar usuário existente", error=str(e))
            return None

    async def create_user_in_keycloak(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Cria usuário no Keycloak via Admin API"""
        try:
            logger.info("Criando usuário no Keycloak", email=user_data.get("email"))
            
            token = await self.get_admin_token()
            if not token:
                logger.error("Não foi possível obter token de admin")
                return None
            
            # Usar CPF como username
            cpf = user_data["cpf"]
            cpf_clean = re.sub(r'[^0-9]', '', cpf)
            email = user_data["email"]
            
            # Verificar se usuário já existe
            existing_user = await self.check_user_exists(cpf=cpf, email=email)
            if existing_user:
                logger.warning("Usuário já existe no Keycloak", 
                              keycloak_id=existing_user.get("id"),
                              username=existing_user.get("username"),
                              email=existing_user.get("email"))
                raise ValueError(f"Usuário já existe no sistema. CPF ou email já cadastrado.")
            
            payload = {
                "username": cpf_clean,  # Usar CPF limpo como username
                "email": email,
                "firstName": user_data.get("first_name", ""),
                "lastName": user_data.get("last_name", ""),
                "enabled": True,
                "emailVerified": False,
                "attributes": {
                    "aceiteTermos": ["true"],
                    "source": ["auth_service"],
                    "created_at": [datetime.now().isoformat()],
                    "cpf": [cpf_clean],
                    "cpf_formatted": [cpf],  # CPF com formatação original
                    "phone": [user_data.get("phone", "")]  # Telefone internacional
                }
            }
            
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users",
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"}
                )
                r.raise_for_status()
                
                # Extrair ID do usuário criado
                user_id = r.headers["Location"].rstrip("/").split("/")[-1]
                
                logger.info("Usuário criado no Keycloak com sucesso", 
                           email=email, keycloak_id=user_id)
                
                return user_id
                
        except ValueError as e:
            # Re-raise para ser tratado na rota
            raise e
        except Exception as e:
            logger.error("Erro ao criar usuário no Keycloak", 
                        email=user_data.get("email"), error=str(e))
            return None
    
    async def set_user_password(self, keycloak_id: str, password: str, temporary: bool = True) -> bool:
        """Define senha para usuário no Keycloak"""
        try:
            logger.info("Definindo senha para usuário", keycloak_id=keycloak_id)
            
            token = await self.get_admin_token()
            if not token:
                return False
            
            payload = {
                "type": "password",
                "temporary": temporary,
                "value": password
            }
            
            async with httpx.AsyncClient() as client:
                r = await client.put(
                    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{keycloak_id}/reset-password",
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"}
                )
                r.raise_for_status()
                
                logger.info("Senha definida com sucesso", keycloak_id=keycloak_id)
                return True
                
        except Exception as e:
            logger.error("Erro ao definir senha", keycloak_id=keycloak_id, error=str(e))
            return False
    
    async def send_verification_email(self, keycloak_id: str) -> bool:
        """Envia e-mail de verificação para o usuário"""
        try:
            logger.info("Enviando e-mail de verificação", keycloak_id=keycloak_id)
            
            token = await self.get_admin_token()
            if not token:
                return False
            
            async with httpx.AsyncClient() as client:
                r = await client.put(
                    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{keycloak_id}/send-verify-email",
                    headers={"Authorization": f"Bearer {token}"}
                )
                r.raise_for_status()
                
                logger.info("E-mail de verificação enviado", keycloak_id=keycloak_id)
                return True
                
        except Exception as e:
            logger.error("Erro ao enviar e-mail de verificação", 
                        keycloak_id=keycloak_id, error=str(e))
            return False
    
    async def get_user_by_id(self, keycloak_id: str) -> Optional[Dict[str, Any]]:
        """Obtém informações detalhadas do usuário no Keycloak"""
        try:
            logger.debug("Obtendo usuário do Keycloak", keycloak_id=keycloak_id)
            
            token = await self.get_admin_token()
            if not token:
                return None
            
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{keycloak_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                r.raise_for_status()
                
                user_data = r.json()
                logger.debug("Usuário obtido do Keycloak", keycloak_id=keycloak_id)
                return user_data
                
        except Exception as e:
            logger.error("Erro ao obter usuário do Keycloak", 
                        keycloak_id=keycloak_id, error=str(e))
            return None
    
    async def update_user_in_keycloak(self, keycloak_id: str, user_data: Dict[str, Any]) -> bool:
        """Atualiza usuário no Keycloak"""
        try:
            logger.info("Atualizando usuário no Keycloak", keycloak_id=keycloak_id)
            
            token = await self.get_admin_token()
            if not token:
                return False
            
            async with httpx.AsyncClient() as client:
                r = await client.put(
                    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{keycloak_id}",
                    json=user_data,
                    headers={"Authorization": f"Bearer {token}"}
                )
                r.raise_for_status()
                
                logger.info("Usuário atualizado no Keycloak", keycloak_id=keycloak_id)
                return True
                
        except Exception as e:
            logger.error("Erro ao atualizar usuário no Keycloak", 
                        keycloak_id=keycloak_id, error=str(e))
            return False
    
    async def delete_user_from_keycloak(self, keycloak_id: str) -> bool:
        """Remove usuário do Keycloak"""
        try:
            logger.info("Removendo usuário do Keycloak", keycloak_id=keycloak_id)
            
            token = await self.get_admin_token()
            if not token:
                return False
            
            async with httpx.AsyncClient() as client:
                r = await client.delete(
                    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users/{keycloak_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                r.raise_for_status()
                
                logger.info("Usuário removido do Keycloak", keycloak_id=keycloak_id)
                return True
                
        except Exception as e:
            logger.error("Erro ao remover usuário do Keycloak", 
                        keycloak_id=keycloak_id, error=str(e))
            return False

# Instância global do serviço
keycloak_service = KeycloakService()

