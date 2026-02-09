"""
Serviço de autenticação com integração Keycloak
"""

import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
import httpx
from cachetools import TTLCache

from config import settings
from models.auth import Token, TokenData, User, UserInDB
from models.acl import User as ACLUser, UserSession, AuditLog
from .keycloak_service import keycloak_service
from .acl_service import acl_service

logger = structlog.get_logger()

class AuthService:
    """Serviço de autenticação integrado com Keycloak e ACL"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Cache para tokens (TTL de 1 minuto)
        self._token_cache = TTLCache(
            maxsize=1000, 
            ttl=settings.TOKEN_CACHE_TTL_SECONDS
        )
        
        # Cache para usuários (TTL de 5 minutos)
        self._user_cache = TTLCache(
            maxsize=500, 
            ttl=settings.CACHE_TTL_SECONDS
        )
    
    async def authenticate_user(self, db: Session, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autentica usuário via Keycloak e sincroniza com banco local"""
        try:
            logger.info("Iniciando autenticação de usuário", username=username)
            
            # Autenticar via Keycloak
            keycloak_result = await keycloak_service.authenticate_user(username, password)
            if not keycloak_result:
                logger.warning("Falha na autenticação Keycloak", username=username)
                return None
            
            # Sincronizar/criar usuário no banco local
            user = await self._sync_user_from_keycloak(db, keycloak_result)
            if not user:
                logger.error("Falha ao sincronizar usuário", username=username)
                return None
            
            # Criar sessão local
            session = await self._create_user_session(db, user.id, keycloak_result['token'])
            if not session:
                logger.error("Falha ao criar sessão", user_id=user.id)
                return None
            
            # Registrar auditoria
            await self._log_audit(db, user.id, "LOGIN", "auth", success=True)
            
            logger.info("Usuário autenticado com sucesso", 
                       user_id=user.id, username=username)
            
            return {
                'user': user,
                'keycloak_token': keycloak_result['token'],
                'session': session,
                'permissions': await acl_service.get_user_permissions_summary(db, user.id)
            }
            
        except Exception as e:
            logger.error("Erro na autenticação", username=username, error=str(e))
            return None
    
    async def _sync_user_from_keycloak(self, db: Session, keycloak_result: Dict[str, Any]) -> Optional[ACLUser]:
        """Sincroniza/cria usuário no banco local baseado nos dados do Keycloak"""
        try:
            keycloak_id = keycloak_result['keycloak_id']
            
            # Verificar se usuário já existe
            user = db.query(ACLUser).filter(ACLUser.keycloak_id == keycloak_id).first()
            
            if user:
                # Atualizar dados do usuário
                user.username = keycloak_result['username']
                user.email = keycloak_result['email']
                user.first_name = keycloak_result['first_name']
                user.last_name = keycloak_result['last_name']
                user.last_login = datetime.utcnow()
                user.is_active = True
                
                db.commit()
                db.refresh(user)
                
                logger.debug("Usuário atualizado", user_id=user.id)
                
            else:
                # Criar novo usuário
                user = ACLUser(
                    keycloak_id=keycloak_id,
                    username=keycloak_result['username'],
                    email=keycloak_result['email'],
                    first_name=keycloak_result['first_name'],
                    last_name=keycloak_result['last_name'],
                    is_active=True,
                    is_verified=True,
                    last_login=datetime.utcnow()
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                logger.info("Novo usuário criado", user_id=user.id, username=user.username)
            
            return user
            
        except Exception as e:
            logger.error("Erro ao sincronizar usuário", error=str(e))
            db.rollback()
            return None
    
    async def _create_user_session(self, db: Session, user_id: int, keycloak_token: Dict[str, Any]) -> Optional[UserSession]:
        """Cria sessão de usuário no banco local"""
        try:
            # Inativar sessões anteriores do usuário
            db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).update({"is_active": False})
            
            # Criar nova sessão
            session = UserSession(
                user_id=user_id,
                session_token=keycloak_token['access_token'],
                refresh_token=keycloak_token.get('refresh_token'),
                expires_at=datetime.utcnow() + timedelta(seconds=keycloak_token.get('expires_in', 300)),
                is_active=True
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return session
            
        except Exception as e:
            logger.error("Erro ao criar sessão", user_id=user_id, error=str(e))
            db.rollback()
            return None
    
    async def validate_token(self, db: Session, token: str) -> Optional[Dict[str, Any]]:
        """Valida token JWT do Keycloak e retorna dados do usuário"""
        try:
            # Verificar cache
            if token in self._token_cache:
                logger.debug("Retornando validação de token do cache")
                return self._token_cache[token]
            
            # Validar token no Keycloak
            keycloak_user_info = await keycloak_service.validate_token(token)
            if not keycloak_user_info:
                logger.warning("Token inválido no Keycloak")
                return None
            
            # Buscar usuário no banco local
            user = db.query(ACLUser).filter(
                ACLUser.keycloak_id == keycloak_user_info['keycloak_id']
            ).first()
            
            if not user or not user.is_active:
                logger.warning("Usuário não encontrado ou inativo", 
                              keycloak_id=keycloak_user_info['keycloak_id'])
                return None
            
            # Verificar se sessão está ativa
            session = db.query(UserSession).filter(
                UserSession.session_token == token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                logger.warning("Sessão não encontrada ou expirada")
                return None
            
            result = {
                'user': user,
                'keycloak_info': keycloak_user_info,
                'session': session
            }
            
            # Armazenar no cache
            self._token_cache[token] = result
            
            return result
            
        except Exception as e:
            logger.error("Erro ao validar token", error=str(e))
            return None
    
    async def refresh_token(self, db: Session, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Renova token via Keycloak"""
        try:
            logger.debug("Renovando token")
            
            # Renovar token no Keycloak
            new_token_data = await keycloak_service.refresh_token(refresh_token)
            if not new_token_data:
                logger.warning("Falha ao renovar token no Keycloak")
                return None
            
            # Buscar sessão atual
            session = db.query(UserSession).filter(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True
            ).first()
            
            if not session:
                logger.warning("Sessão não encontrada para renovação")
                return None
            
            # Atualizar sessão
            session.session_token = new_token_data['access_token']
            session.refresh_token = new_token_data.get('refresh_token')
            session.expires_at = datetime.utcnow() + timedelta(seconds=new_token_data.get('expires_in', 300))
            
            db.commit()
            db.refresh(session)
            
            # Limpar cache do token antigo
            self._token_cache.pop(session.session_token, None)
            
            logger.info("Token renovado com sucesso", user_id=session.user_id)
            
            return {
                'access_token': new_token_data['access_token'],
                'refresh_token': new_token_data.get('refresh_token'),
                'expires_in': new_token_data.get('expires_in'),
                'session': session
            }
            
        except Exception as e:
            logger.error("Erro ao renovar token", error=str(e))
            return None
    
    async def logout_user(self, db: Session, token: str) -> bool:
        """Faz logout do usuário"""
        try:
            logger.info("Iniciando logout do usuário")
            
            # Buscar sessão
            session = db.query(UserSession).filter(
                UserSession.session_token == token,
                UserSession.is_active == True
            ).first()
            
            if not session:
                logger.warning("Sessão não encontrada para logout")
                return False
            
            # Fazer logout no Keycloak se tiver refresh token
            if session.refresh_token:
                await keycloak_service.logout_user(session.refresh_token)
            
            # Inativar sessão local
            session.is_active = False
            db.commit()
            
            # Limpar caches
            self._token_cache.pop(token, None)
            
            # Registrar auditoria
            await self._log_audit(db, session.user_id, "LOGOUT", "auth", success=True)
            
            logger.info("Logout realizado com sucesso", user_id=session.user_id)
            return True
            
        except Exception as e:
            logger.error("Erro ao fazer logout", error=str(e))
            return False
    
    async def get_current_user(self, db: Session, token: str) -> Optional[ACLUser]:
        """Obtém usuário atual baseado no token"""
        try:
            validation_result = await self.validate_token(db, token)
            if validation_result:
                return validation_result['user']
            return None
        except Exception as e:
            logger.error("Erro ao obter usuário atual", error=str(e))
            return None
    
    async def check_permission(
        self, 
        db: Session, 
        token: str, 
        resource: str, 
        action: str, 
        scope: Optional[str] = None
    ) -> bool:
        """Verifica se usuário tem permissão específica"""
        try:
            validation_result = await self.validate_token(db, token)
            if not validation_result:
                return False
            
            user = validation_result['user']
            acl_result = await acl_service.check_permission(db, user.id, resource, action, scope)
            
            return acl_result.allowed
            
        except Exception as e:
            logger.error("Erro ao verificar permissão", error=str(e))
            return False
    
    async def _log_audit(
        self, 
        db: Session, 
        user_id: int, 
        action: str, 
        resource: str, 
        success: bool = True,
        details: Optional[str] = None
    ):
        """Registra log de auditoria"""
        try:
            if not settings.AUDIT_LOG_ENABLED:
                return
            
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                details=details,
                success=success
            )
            
            db.add(audit_log)
            db.commit()
            
        except Exception as e:
            logger.error("Erro ao registrar auditoria", error=str(e))
            db.rollback()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica senha (usado apenas para compatibilidade)"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Gera hash de senha (usado apenas para compatibilidade)"""
        return self.pwd_context.hash(password)
    
    def clear_caches(self):
        """Limpa caches internos"""
        self._token_cache.clear()
        self._user_cache.clear()
        logger.debug("Caches de autenticação limpos")

# Instância global do serviço
auth_service = AuthService()
