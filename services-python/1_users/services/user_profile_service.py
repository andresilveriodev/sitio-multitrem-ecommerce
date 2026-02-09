"""
Serviço para gerenciar dados pessoais do usuário
"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.acl import User
from models.user_profile import (
    UserProfileData, UserPreferences, UserSettings, UserActivity
)
from schemas.user_profile import (
    UserProfileDataCreate, UserProfileDataUpdate,
    UserPreferencesCreate, UserPreferencesUpdate,
    UserSettingsCreate, UserSettingsUpdate,
    UserActivityCreate
)


class UserProfileService:
    """Serviço para gestão de dados pessoais do usuário"""
    
    def __init__(self):
        pass
    
    # ==================== DADOS PESSOAIS ====================
    
    async def get_user_profile_data(self, db: Session, user_id: int) -> Optional[UserProfileData]:
        """Obtém dados pessoais do usuário"""
        return db.query(UserProfileData).filter(UserProfileData.user_id == user_id).first()
    
    async def create_user_profile_data(
        self, 
        db: Session, 
        user_id: int, 
        profile_data: UserProfileDataCreate
    ) -> UserProfileData:
        """Cria dados pessoais do usuário"""
        # Verificar se já existe
        existing = await self.get_user_profile_data(db, user_id)
        if existing:
            raise ValueError("Dados pessoais já existem para este usuário")
        
        # Verificar se CPF já existe (se fornecido)
        if profile_data.cpf:
            existing_cpf = db.query(UserProfileData).filter(
                UserProfileData.cpf == profile_data.cpf
            ).first()
            if existing_cpf:
                raise ValueError("CPF já cadastrado")
        
        profile = UserProfileData(
            user_id=user_id,
            **profile_data.dict()
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    
    async def update_user_profile_data(
        self, 
        db: Session, 
        user_id: int, 
        profile_data: UserProfileDataUpdate
    ) -> Optional[UserProfileData]:
        """Atualiza dados pessoais do usuário"""
        profile = await self.get_user_profile_data(db, user_id)
        if not profile:
            return None
        
        # Verificar se CPF já existe (se fornecido)
        if profile_data.cpf and profile_data.cpf != profile.cpf:
            existing_cpf = db.query(UserProfileData).filter(
                and_(
                    UserProfileData.cpf == profile_data.cpf,
                    UserProfileData.user_id != user_id
                )
            ).first()
            if existing_cpf:
                raise ValueError("CPF já cadastrado para outro usuário")
        
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        db.commit()
        db.refresh(profile)
        return profile
    
    async def delete_user_profile_data(self, db: Session, user_id: int) -> bool:
        """Deleta dados pessoais do usuário"""
        profile = await self.get_user_profile_data(db, user_id)
        if not profile:
            return False
        
        db.delete(profile)
        db.commit()
        return True
    
    # ==================== PREFERÊNCIAS ====================
    
    async def get_user_preferences(self, db: Session, user_id: int) -> Optional[UserPreferences]:
        """Obtém preferências do usuário"""
        return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    
    async def create_user_preferences(
        self, 
        db: Session, 
        user_id: int, 
        preferences_data: UserPreferencesCreate
    ) -> UserPreferences:
        """Cria preferências do usuário"""
        # Verificar se já existe
        existing = await self.get_user_preferences(db, user_id)
        if existing:
            raise ValueError("Preferências já existem para este usuário")
        
        preferences = UserPreferences(
            user_id=user_id,
            **preferences_data.dict()
        )
        
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
        return preferences
    
    async def update_user_preferences(
        self, 
        db: Session, 
        user_id: int, 
        preferences_data: UserPreferencesUpdate
    ) -> Optional[UserPreferences]:
        """Atualiza preferências do usuário"""
        preferences = await self.get_user_preferences(db, user_id)
        if not preferences:
            # Criar preferências padrão se não existirem
            preferences = UserPreferences(user_id=user_id)
            db.add(preferences)
        
        update_data = preferences_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
        
        db.commit()
        db.refresh(preferences)
        return preferences
    
    async def get_or_create_user_preferences(self, db: Session, user_id: int) -> UserPreferences:
        """Obtém ou cria preferências padrão do usuário"""
        preferences = await self.get_user_preferences(db, user_id)
        if not preferences:
            preferences = UserPreferences(user_id=user_id)
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
        return preferences
    
    # ==================== CONFIGURAÇÕES ====================
    
    async def get_user_settings(self, db: Session, user_id: int) -> Optional[UserSettings]:
        """Obtém configurações do usuário"""
        return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    
    async def create_user_settings(
        self, 
        db: Session, 
        user_id: int, 
        settings_data: UserSettingsCreate
    ) -> UserSettings:
        """Cria configurações do usuário"""
        # Verificar se já existe
        existing = await self.get_user_settings(db, user_id)
        if existing:
            raise ValueError("Configurações já existem para este usuário")
        
        settings = UserSettings(
            user_id=user_id,
            **settings_data.dict()
        )
        
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings
    
    async def update_user_settings(
        self, 
        db: Session, 
        user_id: int, 
        settings_data: UserSettingsUpdate
    ) -> Optional[UserSettings]:
        """Atualiza configurações do usuário"""
        settings = await self.get_user_settings(db, user_id)
        if not settings:
            # Criar configurações padrão se não existirem
            settings = UserSettings(user_id=user_id)
            db.add(settings)
        
        update_data = settings_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        db.commit()
        db.refresh(settings)
        return settings
    
    async def get_or_create_user_settings(self, db: Session, user_id: int) -> UserSettings:
        """Obtém ou cria configurações padrão do usuário"""
        settings = await self.get_user_settings(db, user_id)
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings
    
    # ==================== ATIVIDADES ====================
    
    async def get_user_activities(
        self, 
        db: Session, 
        user_id: int, 
        limit: int = 50,
        offset: int = 0
    ) -> List[UserActivity]:
        """Obtém histórico de atividades do usuário"""
        return db.query(UserActivity)\
            .filter(UserActivity.user_id == user_id)\
            .order_by(UserActivity.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
    
    async def log_user_activity(
        self, 
        db: Session, 
        user_id: int, 
        activity_type: str, 
        description: str = None, 
        metadata: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> UserActivity:
        """Registra atividade do usuário"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            metadata=json.dumps(metadata) if metadata else None,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
    
    async def get_user_activity_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Obtém estatísticas de atividades do usuário"""
        total_activities = db.query(UserActivity)\
            .filter(UserActivity.user_id == user_id)\
            .count()
        
        # Atividades por tipo
        activity_types = db.query(UserActivity.activity_type)\
            .filter(UserActivity.user_id == user_id)\
            .group_by(UserActivity.activity_type)\
            .all()
        
        activity_count = {}
        for activity_type in activity_types:
            count = db.query(UserActivity)\
                .filter(
                    and_(
                        UserActivity.user_id == user_id,
                        UserActivity.activity_type == activity_type[0]
                    )
                ).count()
            activity_count[activity_type[0]] = count
        
        return {
            "total_activities": total_activities,
            "activity_types": activity_count
        }
    
    # ==================== PERFIL COMPLETO ====================
    
    async def get_complete_user_profile(self, db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtém perfil completo do usuário com todos os dados"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Dados pessoais
        profile_data = await self.get_user_profile_data(db, user_id)
        preferences = await self.get_user_preferences(db, user_id)
        settings = await self.get_user_settings(db, user_id)
        
        # Perfis e permissões (usando ACL service)
        from services.acl_service import ACLService
        acl_service = ACLService()
        profiles = await acl_service.get_user_profiles(db, user_id)
        permissions = await acl_service.get_user_permissions(db, user_id)
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "last_login": user.last_login,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "profile_data": profile_data,
            "preferences": preferences,
            "settings": settings,
            "profiles": profiles,
            "permissions": permissions
        }
    
    async def initialize_user_profile(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Inicializa perfil completo do usuário com dados padrão"""
        # Criar preferências padrão
        preferences = await self.get_or_create_user_preferences(db, user_id)
        
        # Criar configurações padrão
        settings = await self.get_or_create_user_settings(db, user_id)
        
        # Log da inicialização
        await self.log_user_activity(
            db=db,
            user_id=user_id,
            activity_type="PROFILE_INITIALIZED",
            description="Perfil do usuário inicializado"
        )
        
        return {
            "preferences": preferences,
            "settings": settings
        }



