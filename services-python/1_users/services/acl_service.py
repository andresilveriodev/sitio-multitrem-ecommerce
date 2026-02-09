import structlog
from typing import List, Dict, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from cachetools import TTLCache
from models.acl import User, Profile, Permission
from models.auth import ACLCheckRequest, ACLCheckResponse
from config import settings

logger = structlog.get_logger()

class ACLService:
    """Serviço de Access Control List (ACL) para controle granular de permissões"""
    
    def __init__(self):
        # Cache para permissões de usuário (TTL de 10 minutos)
        self._user_permissions_cache = TTLCache(
            maxsize=1000, 
            ttl=settings.ACL_CACHE_TTL_SECONDS
        )
        
        # Cache para permissões de perfil (TTL de 30 minutos)
        self._profile_permissions_cache = TTLCache(
            maxsize=100, 
            ttl=1800
        )
        
        # Cache para verificações de ACL (TTL de 1 minuto)
        self._acl_check_cache = TTLCache(
            maxsize=5000, 
            ttl=60
        )
    
    async def check_permission(
        self, 
        db: Session, 
        user_id: int, 
        resource: str, 
        action: str, 
        scope: Optional[str] = None
    ) -> ACLCheckResponse:
        """Verifica se usuário tem permissão para ação específica"""
        
        # Criar chave de cache
        cache_key = f"{user_id}:{resource}:{action}:{scope or 'all'}"
        
        # Verificar cache primeiro
        if cache_key in self._acl_check_cache:
            logger.debug("Retornando verificação ACL do cache", cache_key=cache_key)
            return self._acl_check_cache[cache_key]
        
        try:
            logger.debug("Verificando permissão ACL", 
                        user_id=user_id, resource=resource, action=action, scope=scope)
            
            # Obter usuário com perfis e permissões
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                result = ACLCheckResponse(
                    allowed=False,
                    permissions=[],
                    reason="Usuário não encontrado"
                )
                self._acl_check_cache[cache_key] = result
                return result
            
            if not user.is_active:
                result = ACLCheckResponse(
                    allowed=False,
                    permissions=[],
                    reason="Usuário inativo"
                )
                self._acl_check_cache[cache_key] = result
                return result
            
            # Obter todas as permissões do usuário
            user_permissions = await self._get_user_permissions(db, user_id)
            
            # Verificar permissão específica
            required_permission = f"{resource}:{action}"
            if scope:
                required_permission += f":{scope}"
            
            allowed = False
            matching_permissions = []
            
            for permission in user_permissions:
                if self._permission_matches(permission, resource, action, scope):
                    allowed = True
                    matching_permissions.append(permission.name)
            
            result = ACLCheckResponse(
                allowed=allowed,
                permissions=matching_permissions,
                reason=None if allowed else "Permissão não encontrada"
            )
            
            # Armazenar no cache
            self._acl_check_cache[cache_key] = result
            
            logger.debug("Verificação ACL concluída", 
                        user_id=user_id, allowed=allowed, permissions=matching_permissions)
            
            return result
            
        except Exception as e:
            logger.error("Erro ao verificar permissão ACL", 
                        user_id=user_id, error=str(e))
            return ACLCheckResponse(
                allowed=False,
                permissions=[],
                reason=f"Erro interno: {str(e)}"
            )
    
    async def _get_user_permissions(self, db: Session, user_id: int) -> List[Permission]:
        """Obtém todas as permissões do usuário (com cache)"""
        
        # Verificar cache
        if user_id in self._user_permissions_cache:
            logger.debug("Retornando permissões do usuário do cache", user_id=user_id)
            return self._user_permissions_cache[user_id]
        
        try:
            # Buscar usuário com perfis e permissões
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            
            # Coletar todas as permissões dos perfis do usuário
            permissions = set()
            for profile in user.profiles:
                if profile.is_active:
                    for permission in profile.permissions:
                        if permission.is_active:
                            permissions.add(permission)
            
            permissions_list = list(permissions)
            
            # Armazenar no cache
            self._user_permissions_cache[user_id] = permissions_list
            
            logger.debug("Permissões do usuário carregadas", 
                        user_id=user_id, count=len(permissions_list))
            
            return permissions_list
            
        except Exception as e:
            logger.error("Erro ao obter permissões do usuário", 
                        user_id=user_id, error=str(e))
            return []
    
    def _permission_matches(
        self, 
        permission: Permission, 
        resource: str, 
        action: str, 
        scope: Optional[str] = None
    ) -> bool:
        """Verifica se uma permissão corresponde aos critérios"""
        
        # Verificar recurso e ação
        if permission.resource != resource or permission.action != action:
            return False
        
        # Verificar escopo se especificado
        if scope and permission.scope and permission.scope != scope:
            # Verificar se o escopo da permissão é 'all' (acesso total)
            if permission.scope != 'all':
                return False
        
        return True
    
    async def get_user_permissions_summary(self, db: Session, user_id: int) -> Dict[str, List[str]]:
        """Obtém resumo das permissões do usuário agrupadas por recurso"""
        try:
            permissions = await self._get_user_permissions(db, user_id)
            
            summary = {}
            for permission in permissions:
                resource = permission.resource
                if resource not in summary:
                    summary[resource] = []
                summary[resource].append(permission.action)
            
            return summary
            
        except Exception as e:
            logger.error("Erro ao obter resumo de permissões", 
                        user_id=user_id, error=str(e))
            return {}
    
    async def create_permission(
        self, 
        db: Session, 
        name: str, 
        description: str, 
        resource: str, 
        action: str, 
        scope: Optional[str] = None
    ) -> Optional[Permission]:
        """Cria nova permissão"""
        try:
            # Verificar se permissão já existe
            existing = db.query(Permission).filter(
                and_(
                    Permission.resource == resource,
                    Permission.action == action,
                    Permission.scope == scope
                )
            ).first()
            
            if existing:
                logger.warning("Permissão já existe", 
                              resource=resource, action=action, scope=scope)
                return None
            
            permission = Permission(
                name=name,
                description=description,
                resource=resource,
                action=action,
                scope=scope
            )
            
            db.add(permission)
            db.commit()
            db.refresh(permission)
            
            # Limpar caches relacionados
            self._clear_related_caches()
            
            logger.info("Permissão criada", 
                       permission_id=permission.id, name=name)
            
            return permission
            
        except Exception as e:
            logger.error("Erro ao criar permissão", error=str(e))
            db.rollback()
            return None
    
    async def create_profile(
        self, 
        db: Session, 
        name: str, 
        description: str, 
        permission_ids: List[int] = None
    ) -> Optional[Profile]:
        """Cria novo perfil com permissões"""
        try:
            # Verificar se perfil já existe
            existing = db.query(Profile).filter(Profile.name == name).first()
            if existing:
                logger.warning("Perfil já existe", name=name)
                return None
            
            profile = Profile(
                name=name,
                description=description
            )
            
            db.add(profile)
            db.commit()
            db.refresh(profile)
            
            # Adicionar permissões se especificadas
            if permission_ids:
                permissions = db.query(Permission).filter(
                    Permission.id.in_(permission_ids)
                ).all()
                profile.permissions.extend(permissions)
                db.commit()
            
            # Limpar caches relacionados
            self._clear_related_caches()
            
            logger.info("Perfil criado", 
                       profile_id=profile.id, name=name)
            
            return profile
            
        except Exception as e:
            logger.error("Erro ao criar perfil", error=str(e))
            db.rollback()
            return None
    
    async def assign_profile_to_user(
        self, 
        db: Session, 
        user_id: int, 
        profile_id: int
    ) -> bool:
        """Atribui perfil ao usuário"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            profile = db.query(Profile).filter(Profile.id == profile_id).first()
            
            if not user or not profile:
                logger.warning("Usuário ou perfil não encontrado", 
                              user_id=user_id, profile_id=profile_id)
                return False
            
            if profile not in user.profiles:
                user.profiles.append(profile)
                db.commit()
                
                # Limpar cache do usuário
                self._user_permissions_cache.pop(user_id, None)
                
                logger.info("Perfil atribuído ao usuário", 
                           user_id=user_id, profile_id=profile_id)
                return True
            
            return True
            
        except Exception as e:
            logger.error("Erro ao atribuir perfil", 
                        user_id=user_id, profile_id=profile_id, error=str(e))
            db.rollback()
            return False
    
    def _clear_related_caches(self):
        """Limpa caches relacionados"""
        self._user_permissions_cache.clear()
        self._profile_permissions_cache.clear()
        self._acl_check_cache.clear()
        logger.debug("Caches ACL limpos")
    
    def clear_all_caches(self):
        """Limpa todos os caches"""
        self._user_permissions_cache.clear()
        self._profile_permissions_cache.clear()
        self._acl_check_cache.clear()
        logger.info("Todos os caches ACL limpos")

# Instância global do serviço
acl_service = ACLService()

