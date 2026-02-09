from sqlalchemy import Column, String, Text, Integer, Boolean, Float, JSON, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import BaseModel
from typing import Dict, Any
import enum

class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"

class UserSubscription(BaseModel):
    __tablename__ = 'user_subscriptions'
    
    # Relacionamentos
    user_id = Column(String(50), nullable=False, index=True)  # UUID como string
    subscription_id = Column(Integer, ForeignKey('ai_subscriptions.id'), nullable=False, index=True)
    
    # Status da assinatura
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    
    # Período da assinatura
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    
    # Uso atual
    usage_limits = Column(JSON, nullable=True)  # limites atuais
    current_usage = Column(JSON, nullable=True)  # uso atual
    
    # Relacionamentos
    subscription = relationship("AISubscription")
    
    def __repr__(self):
        return f"<UserSubscription(user_id={self.user_id}, subscription_id={self.subscription_id}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'status': self.status.value if self.status else None,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'usage_limits': self.usage_limits,
            'current_usage': self.current_usage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
