"""
Modelos SQLAlchemy para ACL (Access Control List)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db_session import Base


class User(Base):
    """Modelo de usuário para autenticação"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    keycloak_id = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Profile(Base):
    """Modelo de perfil de acesso"""
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    user_profiles = relationship("UserProfile", back_populates="profile", cascade="all, delete-orphan")
    profile_permissions = relationship("ProfilePermission", back_populates="profile", cascade="all, delete-orphan")


class Permission(Base):
    """Modelo de permissão individual"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)
    scope = Column(String(20), default="own", nullable=False)  # own, all, admin
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    profile_permissions = relationship("ProfilePermission", back_populates="permission", cascade="all, delete-orphan")


class UserProfile(Base):
    """Relacionamento N:N entre usuário e perfil"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=func.now(), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Relacionamentos
    user = relationship("User", foreign_keys=[user_id])
    profile = relationship("Profile", back_populates="user_profiles")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])


class ProfilePermission(Base):
    """Relacionamento N:N entre perfil e permissão"""
    __tablename__ = "profile_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    profile = relationship("Profile", back_populates="profile_permissions")
    permission = relationship("Permission", back_populates="profile_permissions")


class UserSession(Base):
    """Modelo de sessão ativa do usuário"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    user = relationship("User", back_populates="sessions")


class AuditLog(Base):
    """Modelo de log de auditoria"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relacionamentos
    user = relationship("User", back_populates="audit_logs")
