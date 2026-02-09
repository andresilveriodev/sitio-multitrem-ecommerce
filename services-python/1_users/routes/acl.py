"""
Rotas para ACL (Access Control List)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Dict, List
import structlog

from models.auth import (
    ACLCheckRequest, ACLCheckResponse, ProfileCreate, ProfileUpdate,
    PermissionCreate, PermissionUpdate
)
from models.acl import User, Profile, Permission, UserSession, AuditLog
from services.acl_service import acl_service
from services.auth_service import auth_service
from db_session import get_db_session

logger = structlog.get_logger()
router = APIRouter(prefix="/acl", tags=["ACL"])

# OAuth2 scheme local
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user_token(
    db: Session = Depends(get_db_session),
    token: str = Depends(oauth2_scheme)
):
    """Dependency para obter usuário atual"""
    user = await auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user, token

@router.post("/check", response_model=ACLCheckResponse)
async def check_permission(
    acl_check: ACLCheckRequest,
    db: Session = Depends(get_db_session),
    current_user_token: tuple = Depends(get_current_user_token)
):
    """Verifica se usuário tem permissão específica"""
    try:
        current_user, token = current_user_token
        
        # Verificar se usuário está verificando suas próprias permissões
        # ou se tem permissão administrativa
        if acl_check.user_id != current_user.id:
            # Verificar se tem permissão administrativa
            has_admin = await auth_service.check_permission(
                db, token, "acl", "read", "all"
            )
            if not has_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sem permissão para verificar permissões de outros usuários"
                )
        
        result = await acl_service.check_permission(
            db, 
            acl_check.user_id, 
            acl_check.resource, 
            acl_check.action, 
            acl_check.scope
        )
        
        logger.info("Verificação ACL realizada", 
                   user_id=acl_check.user_id,
                   resource=acl_check.resource,
                   action=acl_check.action,
                   allowed=result.allowed)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao verificar permissão ACL", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/permissions/summary/{user_id}")
async def get_user_permissions_summary(
    user_id: int,
    db: Session = Depends(get_db_session),
    current_user_token: tuple = Depends(get_current_user_token)
):
    """Obtém resumo das permissões do usuário agrupadas por recurso"""
    try:
        current_user, token = current_user_token
        
        # Verificar se usuário está consultando suas próprias permissões
        # ou se tem permissão administrativa
        if user_id != current_user.id:
            has_admin = await auth_service.check_permission(
                db, token, "acl", "read", "all"
            )
            if not has_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sem permissão para consultar permissões de outros usuários"
                )
        
        summary = await acl_service.get_user_permissions_summary(db, user_id)
        
        logger.info("Resumo de permissões consultado", user_id=user_id)
        
        return {
            "user_id": user_id,
            "permissions": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter resumo de permissões", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/permissions", response_model=PermissionUpdate)
async def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db_session),
    current_user_token: tuple = Depends(get_current_user_token)
):
    """Cria nova permissão (apenas administradores)"""
    try:
        current_user, token = current_user_token
        
        # Verificar permissão administrativa
        has_admin = await auth_service.check_permission(
            db, token, "acl", "write", "all"
        )
        if not has_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para criar permissões"
            )
        
        new_permission = await acl_service.create_permission(
            db,
            permission.name,
            permission.description,
            permission.resource,
            permission.action,
            permission.scope
        )
        
        if not new_permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permissão já existe ou dados inválidos"
            )
        
        logger.info("Permissão criada", 
                   permission_id=new_permission.id,
                   name=new_permission.name,
                   created_by=current_user.id)
        
        return new_permission
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao criar permissão", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/profiles", response_model=ProfileUpdate)
async def create_profile(
    profile: ProfileCreate,
    db: Session = Depends(get_db_session),
    current_user_token: tuple = Depends(get_current_user_token)
):
    """Cria novo perfil (apenas administradores)"""
    try:
        current_user, token = current_user_token
        
        # Verificar permissão administrativa
        has_admin = await auth_service.check_permission(
            db, token, "acl", "write", "all"
        )
        if not has_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para criar perfis"
            )
        
        new_profile = await acl_service.create_profile(
            db,
            profile.name,
            profile.description
        )
        
        if not new_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Perfil já existe ou dados inválidos"
            )
        
        logger.info("Perfil criado", 
                   profile_id=new_profile.id,
                   name=new_profile.name,
                   created_by=current_user.id)
        
        return new_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao criar perfil", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/profiles/{profile_id}/assign/{user_id}")
async def assign_profile_to_user(
    profile_id: int,
    user_id: int,
    db: Session = Depends(get_db_session),
    current_user_token: tuple = Depends(get_current_user_token)
):
    """Atribui perfil ao usuário (apenas administradores)"""
    try:
        current_user, token = current_user_token
        
        # Verificar permissão administrativa
        has_admin = await auth_service.check_permission(
            db, token, "acl", "write", "all"
        )
        if not has_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para atribuir perfis"
            )
        
        success = await acl_service.assign_profile_to_user(db, user_id, profile_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário ou perfil não encontrado"
            )
        
        logger.info("Perfil atribuído ao usuário", 
                   user_id=user_id,
                   profile_id=profile_id,
                   assigned_by=current_user.id)
        
        return {
            "message": "Perfil atribuído com sucesso",
            "user_id": user_id,
            "profile_id": profile_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao atribuir perfil", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/cache/clear")
async def clear_acl_cache(
    db: Session = Depends(get_db_session),
    current_user_token: tuple = Depends(get_current_user_token)
):
    """Limpa cache do ACL (apenas administradores)"""
    try:
        current_user, token = current_user_token
        
        # Verificar permissão administrativa
        has_admin = await auth_service.check_permission(
            db, token, "acl", "write", "all"
        )
        if not has_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para limpar cache"
            )
        
        acl_service.clear_all_caches()
        
        logger.info("Cache ACL limpo", cleared_by=current_user.id)
        
        return {
            "message": "Cache ACL limpo com sucesso",
            "cleared_by": current_user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao limpar cache ACL", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )
