from sqlalchemy import Column, String, Text, Integer, Boolean, Float, JSON, DateTime
from sqlalchemy.sql import func
from models.base import BaseModel
from typing import Dict, Any

class AIModel(BaseModel):
    __tablename__ = 'ai_models'
    
    # Identificação
    model_id = Column(String(100), unique=True, nullable=False, index=True)  # ex: 'ollama', 'gpt-4o-mini'
    name = Column(String(200), nullable=False)  # ex: 'GPT-4o Mini'
    provider = Column(String(100), nullable=False, index=True)  # ex: 'OpenAI', 'Ollama'
    
    # Configurações de custo
    is_paid = Column(Boolean, default=False)
    cost_per_1k_tokens = Column(Float, default=0.0)
    max_tokens_per_request = Column(Integer, default=4096)
    
    # Status e disponibilidade
    is_available = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    
    # Configurações avançadas
    features = Column(JSON, nullable=True)  # array de features disponíveis
    rate_limits = Column(JSON, nullable=True)  # limites de rate
    
    def __repr__(self):
        return f"<AIModel(model_id='{self.model_id}', name='{self.name}', provider='{self.provider}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'model_id': self.model_id,
            'name': self.name,
            'provider': self.provider,
            'is_paid': self.is_paid,
            'cost_per_1k_tokens': self.cost_per_1k_tokens,
            'max_tokens_per_request': self.max_tokens_per_request,
            'is_available': self.is_available,
            'description': self.description,
            'features': self.features,
            'rate_limits': self.rate_limits,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
