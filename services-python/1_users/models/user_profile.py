"""
Modelo para dados pessoais completos do usuário
"""

from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .acl import Base


class UserProfileData(Base):
    """Modelo para dados pessoais completos do usuário"""
    __tablename__ = "user_profiles_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    cpf = Column(String(14), nullable=True, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    country = Column(String(50), default="Brasil")
    postal_code = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    user = relationship("User")


class UserPreferences(Base):
    """Modelo para preferências de interface do usuário"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    language = Column(String(10), default="pt-BR", nullable=False)
    timezone = Column(String(50), default="America/Sao_Paulo", nullable=False)
    theme = Column(String(20), default="light", nullable=False)
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    email_notifications = Column(Boolean, default=True, nullable=False)
    push_notifications = Column(Boolean, default=False, nullable=False)
    sms_notifications = Column(Boolean, default=False, nullable=False)
    sound_enabled = Column(Boolean, default=True, nullable=False)
    auto_refresh = Column(Boolean, default=True, nullable=False)
    refresh_interval = Column(Integer, default=5000, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    user = relationship("User")


class UserSettings(Base):
    """Modelo para configurações de conta do usuário"""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    privacy_level = Column(String(20), default="public", nullable=False)
    data_sharing = Column(Boolean, default=True, nullable=False)
    marketing_emails = Column(Boolean, default=False, nullable=False)
    newsletter_subscription = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    user = relationship("User")


class UserActivity(Base):
    """Modelo para histórico de atividades do usuário"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    activity_metadata = Column(Text, nullable=True)  # JSON como texto
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relacionamentos
    user = relationship("User")
