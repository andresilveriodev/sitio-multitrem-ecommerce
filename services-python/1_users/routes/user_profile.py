"""
Rotas para gerenciar dados pessoais do usuário
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File
from sqlalchemy.orm import Session
import structlog

from db_session import get_db_session
from services.user_profile_service import UserProfileService
from services.auth_service import AuthService
from schemas.user_profile import (
    UserProfileDataCreate, UserProfileDataUpdate, UserProfileDataResponse,
    UserPreferencesCreate, UserPreferencesUpdate, UserPreferencesResponse,
    UserSettingsCreate, UserSettingsUpdate, UserSettingsResponse,
    UserActivityResponse, UserCompleteProfile
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/users", tags=["User Profile"])

# Instanciar serviços
user_profile_service = UserProfileService()
auth_service = AuthService()


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


# ==================== DADOS PESSOAIS ====================

@router.get("/{user_id}/profile", response_model=UserProfileDataResponse)
async def get_user_profile_data(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Obtém dados pessoais do usuário"""
    try:
        # Verificar se usuário está consultando seu próprio perfil
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para acessar perfil de outro usuário"
            )
        
        profile_data = await user_profile_service.get_user_profile_data(db, user_id)
        
        if not profile_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dados pessoais não encontrados"
            )
        
        return profile_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter dados pessoais", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post("/{user_id}/profile", response_model=UserProfileDataResponse)
async def create_user_profile_data(
    user_id: int,
    profile_data: UserProfileDataCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Cria dados pessoais do usuário"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para criar perfil de outro usuário"
            )
        
        created_profile = await user_profile_service.create_user_profile_data(
            db, user_id, profile_data
        )
        
        # Log da criação
        await user_profile_service.log_user_activity(
            db=db,
            user_id=user_id,
            activity_type="PROFILE_DATA_CREATED",
            description="Dados pessoais criados",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return created_profile
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao criar dados pessoais", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.put("/{user_id}/profile", response_model=UserProfileDataResponse)
async def update_user_profile_data(
    user_id: int,
    profile_data: UserProfileDataUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Atualiza dados pessoais do usuário"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para atualizar perfil de outro usuário"
            )
        
        updated_profile = await user_profile_service.update_user_profile_data(
            db, user_id, profile_data
        )
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dados pessoais não encontrados"
            )
        
        # Log da atualização
        await user_profile_service.log_user_activity(
            db=db,
            user_id=user_id,
            activity_type="PROFILE_DATA_UPDATED",
            description="Dados pessoais atualizados",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return updated_profile
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao atualizar dados pessoais", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.delete("/{user_id}/profile")
async def delete_user_profile_data(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Deleta dados pessoais do usuário"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para deletar perfil de outro usuário"
            )
        
        deleted = await user_profile_service.delete_user_profile_data(db, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dados pessoais não encontrados"
            )
        
        # Log da exclusão
        await user_profile_service.log_user_activity(
            db=db,
            user_id=user_id,
            activity_type="PROFILE_DATA_DELETED",
            description="Dados pessoais deletados",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return {"message": "Dados pessoais deletados com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao deletar dados pessoais", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


# ==================== PREFERÊNCIAS ====================

@router.get("/{user_id}/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Obtém preferências do usuário"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para acessar preferências de outro usuário"
            )
        
        preferences = await user_profile_service.get_user_preferences(db, user_id)
        
        if not preferences:
            # Criar preferências padrão
            preferences = await user_profile_service.get_or_create_user_preferences(db, user_id)
        
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter preferências", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.put("/{user_id}/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    user_id: int,
    preferences_data: UserPreferencesUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Atualiza preferências do usuário"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para atualizar preferências de outro usuário"
            )
        
        updated_preferences = await user_profile_service.update_user_preferences(
            db, user_id, preferences_data
        )
        
        # Log da atualização
        await user_profile_service.log_user_activity(
            db=db,
            user_id=user_id,
            activity_type="PREFERENCES_UPDATED",
            description="Preferências atualizadas",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return updated_preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao atualizar preferências", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


# ==================== CONFIGURAÇÕES ====================

@router.get("/{user_id}/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Obtém configurações do usuário"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para acessar configurações de outro usuário"
            )
        
        settings = await user_profile_service.get_user_settings(db, user_id)
        
        if not settings:
            # Criar configurações padrão
            settings = await user_profile_service.get_or_create_user_settings(db, user_id)
        
        return settings
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter configurações", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.put("/{user_id}/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    user_id: int,
    settings_data: UserSettingsUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Atualiza configurações do usuário"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para atualizar configurações de outro usuário"
            )
        
        updated_settings = await user_profile_service.update_user_settings(
            db, user_id, settings_data
        )
        
        # Log da atualização
        await user_profile_service.log_user_activity(
            db=db,
            user_id=user_id,
            activity_type="SETTINGS_UPDATED",
            description="Configurações atualizadas",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return updated_settings
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao atualizar configurações", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


# ==================== ATIVIDADES ====================

@router.get("/{user_id}/activities", response_model=List[UserActivityResponse])
async def get_user_activities(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Obtém histórico de atividades do usuário"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para acessar atividades de outro usuário"
            )
        
        activities = await user_profile_service.get_user_activities(
            db, user_id, limit, offset
        )
        
        return activities
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter atividades", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get("/{user_id}/activities/stats")
async def get_user_activity_stats(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Obtém estatísticas de atividades do usuário"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para acessar estatísticas de outro usuário"
            )
        
        stats = await user_profile_service.get_user_activity_stats(db, user_id)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter estatísticas", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


# ==================== PERFIL COMPLETO ====================

@router.get("/{user_id}/complete", response_model=UserCompleteProfile)
async def get_complete_user_profile(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Obtém perfil completo do usuário com todos os dados"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para acessar perfil de outro usuário"
            )
        
        complete_profile = await user_profile_service.get_complete_user_profile(db, user_id)
        
        if not complete_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        return complete_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter perfil completo", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post("/{user_id}/initialize")
async def initialize_user_profile(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    """Inicializa perfil do usuário com dados padrão"""
    try:
        # Verificar permissão
        if current_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para inicializar perfil de outro usuário"
            )
        
        initialized = await user_profile_service.initialize_user_profile(db, user_id)
        
        return {
            "message": "Perfil inicializado com sucesso",
            "data": initialized
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao inicializar perfil", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )



