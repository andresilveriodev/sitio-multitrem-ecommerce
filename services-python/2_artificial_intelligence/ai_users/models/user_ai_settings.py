from sqlalchemy import Column, String, Text, Integer, Boolean, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import BaseModel
from typing import Dict, Any

class UserAISettings(BaseModel):
    __tablename__ = 'user_ai_settings'
    
    # Relacionamento único com usuário
    user_id = Column(Integer, ForeignKey('public.users.id'), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=False, index=True)  # Para facilitar consultas
    
    # Configurações de modelo
    default_model = Column(String(100), nullable=False, default='ollama')
    preferred_models = Column(JSON, nullable=True)  # array de modelos preferidos
    
    # Configurações de comportamento
    auto_fallback = Column(Boolean, default=True)
    
    # Configurações de notificações
    notifications = Column(JSON, nullable=True)  # configurações de notificações
    
    def __repr__(self):
        return f"<UserAISettings(user_id={self.user_id}, default_model='{self.default_model}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'default_model': self.default_model,
            'preferred_models': self.preferred_models,
            'auto_fallback': self.auto_fallback,
            'notifications': self.notifications,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
