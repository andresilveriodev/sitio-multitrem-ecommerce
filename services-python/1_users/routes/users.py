"""
Rotas CRUD para usuários
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import structlog

from db_session import get_db_session
from services.auth_service import AuthService
from services.user_service import UserService
from services.audit_service import AuditService
from schemas.auth import (
    UserCreate, UserUpdate, UserResponse, UserInDB
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/users", tags=["Users"])

# Instanciar serviços
auth_service = AuthService()
user_service = UserService()
audit_service = AuditService()


def get_current_user_id(request: Request, db: Session = Depends(get_db_session)) -> int:
    """Obtém o ID do usuário atual a partir do token"""
    try:
        # Extrair token do header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticação necessário"
            )
        
        token = auth_header.split(" ")[1]
        user_data = auth_service.get_user_from_token(token)
        
        if not user_data or not user_data.get("id"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado"
            )
        
        return user_data["id"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter usuário atual", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro na autenticação"
        )


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Lista usuários com paginação"""
    try:
        # Verificar permissão de admin
        has_permission = await auth_service.check_permission(
            db, current_user_id, "admin", "read", "all"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para listar usuários"
            )
        
        users = await user_service.get_users(db, skip, limit)
        
        # Log de consulta
        await audit_service.log_action(
            db=db,
            user_id=current_user_id,
            action="users_listed",
            resource="users",
            details={"skip": skip, "limit": limit, "count": len(users)},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao listar usuários", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Obtém um usuário específico"""
    try:
        # Verificar se usuário está consultando seu próprio perfil ou tem permissão admin
        if current_user_id != user_id:
            has_permission = await auth_service.check_permission(
                db, current_user_id, "admin", "read", "all"
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sem permissão para acessar dados de outro usuário"
                )
        
        user = await user_service.get_user(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Log de consulta
        await audit_service.log_action(
            db=db,
            user_id=current_user_id,
            action="user_viewed",
            resource="user",
            resource_id=str(user_id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter usuário", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Cria um novo usuário"""
    try:
        # Verificar permissão de admin
        has_permission = await auth_service.check_permission(
            db, current_user_id, "admin", "write", "all"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para criar usuários"
            )
        
        user = await user_service.create_user(db, user_data)
        
        # Log de criação
        await audit_service.log_action(
            db=db,
            user_id=current_user_id,
            action="user_created",
            resource="user",
            resource_id=str(user.id),
            details={"username": user.username, "email": user.email},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        return user
        
    except ValueError as e:
        await audit_service.log_action(
            db=db,
            user_id=current_user_id,
            action="user_creation_failed",
            resource="user",
            details={"error": str(e), "username": user_data.username},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao criar usuário", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Atualiza um usuário"""
    try:
        # Verificar se usuário está atualizando seu próprio perfil ou tem permissão admin
        if current_user_id != user_id:
            has_permission = await auth_service.check_permission(
                db, current_user_id, "admin", "write", "all"
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sem permissão para atualizar dados de outro usuário"
                )
        
        user = await user_service.update_user(db, user_id, user_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Log de atualização
        await audit_service.log_action(
            db=db,
            user_id=current_user_id,
            action="user_updated",
            resource="user",
            resource_id=str(user_id),
            details={"updated_fields": list(user_data.dict(exclude_unset=True).keys())},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao atualizar usuário", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Deleta um usuário"""
    try:
        # Verificar permissão de admin
        has_permission = await auth_service.check_permission(
            db, current_user_id, "admin", "write", "all"
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para deletar usuários"
            )
        
        # Não permitir deletar o próprio usuário
        if current_user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível deletar o próprio usuário"
            )
        
        deleted = await user_service.delete_user(db, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Log de exclusão
        await audit_service.log_action(
            db=db,
            user_id=current_user_id,
            action="user_deleted",
            resource="user",
            resource_id=str(user_id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        return {"message": "Usuário deletado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao deletar usuário", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


