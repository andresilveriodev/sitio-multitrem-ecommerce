from sqlalchemy import Column, String, Text, Integer, Boolean, Float, JSON, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import BaseModel
from typing import Dict, Any
import enum

class AlertType(enum.Enum):
    USAGE = "usage"
    COST = "cost"
    RATE_LIMIT = "rate_limit"

class AIUsageAlert(BaseModel):
    __tablename__ = 'ai_usage_alerts'
    
    # Relacionamento
    user_id = Column(Integer, ForeignKey('public.users.id'), nullable=False, index=True)
    username = Column(String(50), nullable=False, index=True)  # Para facilitar consultas
    
    # Tipo e configuração do alerta
    alert_type = Column(Enum(AlertType), nullable=False)
    threshold = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    
    # Mensagem e status
    message = Column(Text, nullable=False)
    is_triggered = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<AIUsageAlert(user_id={self.user_id}, alert_type={self.alert_type}, threshold={self.threshold})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'alert_type': self.alert_type.value if self.alert_type else None,
            'threshold': self.threshold,
            'current_value': self.current_value,
            'message': self.message,
            'is_triggered': self.is_triggered,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
