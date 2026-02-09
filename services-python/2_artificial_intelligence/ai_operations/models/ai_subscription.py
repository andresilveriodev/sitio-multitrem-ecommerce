from sqlalchemy import Column, String, Text, Integer, Boolean, Float, JSON, DateTime, Enum
from sqlalchemy.sql import func
from models.base import BaseModel
from typing import Dict, Any
import enum

class BillingCycle(enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

class AISubscription(BaseModel):
    __tablename__ = 'ai_subscriptions'
    
    # Identificação
    plan_id = Column(String(100), unique=True, nullable=False, index=True)  # ex: 'free', 'premium'
    name = Column(String(200), nullable=False)  # ex: 'Plano Gratuito'
    
    # Configurações de preço
    price = Column(Float, default=0.0)
    currency = Column(String(10), default='BRL')
    billing_cycle = Column(Enum(BillingCycle), default=BillingCycle.MONTHLY)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Configurações do plano
    features = Column(JSON, nullable=True)  # features incluídas
    limits = Column(JSON, nullable=True)  # limites do plano
    
    def __repr__(self):
        return f"<AISubscription(plan_id='{self.plan_id}', name='{self.name}', price={self.price})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'name': self.name,
            'price': self.price,
            'currency': self.currency,
            'billing_cycle': self.billing_cycle.value if self.billing_cycle else None,
            'is_active': self.is_active,
            'features': self.features,
            'limits': self.limits,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
