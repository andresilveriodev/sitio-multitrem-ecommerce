"""
Schemas Pydantic para dados pessoais do usuário
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import date, datetime


class UserProfileDataBase(BaseModel):
    """Schema base para dados pessoais do usuário"""
    full_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: Optional[date] = None
    cpf: Optional[str] = Field(None, pattern=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None


class UserProfileDataCreate(UserProfileDataBase):
    """Schema para criação de dados pessoais"""
    pass


class UserProfileDataUpdate(BaseModel):
    """Schema para atualização de dados pessoais"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    date_of_birth: Optional[date] = None
    cpf: Optional[str] = Field(None, pattern=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None


class UserProfileDataResponse(UserProfileDataBase):
    """Schema para resposta de dados pessoais"""
    id: int
    user_id: int
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserPreferencesBase(BaseModel):
    """Schema base para preferências do usuário"""
    language: str = Field(default="pt-BR", max_length=10)
    timezone: str = Field(default="America/Sao_Paulo", max_length=50)
    theme: str = Field(default="light", max_length=20)
    notifications_enabled: bool = True
    email_notifications: bool = True
    push_notifications: bool = False
    sms_notifications: bool = False
    sound_enabled: bool = True
    auto_refresh: bool = True
    refresh_interval: int = Field(default=5000, ge=1000, le=60000)


class UserPreferencesCreate(UserPreferencesBase):
    """Schema para criação de preferências"""
    pass


class UserPreferencesUpdate(BaseModel):
    """Schema para atualização de preferências"""
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    theme: Optional[str] = Field(None, max_length=20)
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    auto_refresh: Optional[bool] = None
    refresh_interval: Optional[int] = Field(None, ge=1000, le=60000)


class UserPreferencesResponse(UserPreferencesBase):
    """Schema para resposta de preferências"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserSettingsBase(BaseModel):
    """Schema base para configurações do usuário"""
    two_factor_enabled: bool = False
    privacy_level: str = Field(default="public", max_length=20)
    data_sharing: bool = True
    marketing_emails: bool = False
    newsletter_subscription: bool = False


class UserSettingsCreate(UserSettingsBase):
    """Schema para criação de configurações"""
    pass


class UserSettingsUpdate(BaseModel):
    """Schema para atualização de configurações"""
    two_factor_enabled: Optional[bool] = None
    privacy_level: Optional[str] = Field(None, max_length=20)
    data_sharing: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    newsletter_subscription: Optional[bool] = None


class UserSettingsResponse(UserSettingsBase):
    """Schema para resposta de configurações"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserActivityBase(BaseModel):
    """Schema base para atividades do usuário"""
    activity_type: str = Field(..., max_length=100)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None


class UserActivityCreate(UserActivityBase):
    """Schema para criação de atividade"""
    pass


class UserActivityResponse(UserActivityBase):
    """Schema para resposta de atividade"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserCompleteProfile(BaseModel):
    """Schema para perfil completo do usuário"""
    user_id: int
    username: str
    email: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Dados pessoais
    profile_data: Optional[UserProfileDataResponse] = None
    preferences: Optional[UserPreferencesResponse] = None
    settings: Optional[UserSettingsResponse] = None
    
    # Perfis e permissões
    profiles: list[str] = []
    permissions: list[str] = []
    
    class Config:
        from_attributes = True
