from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from models.base import BaseModel
from typing import Dict, Any, List

class Conversation(BaseModel):
    __tablename__ = 'conversations'
    
    user_id = Column(Integer, ForeignKey('public.users.id'), nullable=False)
    username = Column(String(50), nullable=False, index=True)  # Para facilitar consultas
    title = Column(String(200), nullable=True)
    status = Column(String(20), default='active')  # active, archived, deleted
    
    # Métricas de tokens e custos agregadas
    total_tokens = Column(Integer, nullable=False, default=0)
    total_prompt_tokens = Column(Integer, nullable=False, default=0)
    total_completion_tokens = Column(Integer, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0.0)
    total_messages = Column(Integer, nullable=False, default=0)
    
    # Metadados da conversa
    conversation_metadata = Column(JSON, nullable=True)  # Configurações, contexto, etc
    
    # Relacionamentos
    transactions = relationship("AITransaction", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title='{self.title}', tokens={self.total_tokens})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário incluindo métricas"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'status': self.status,
            'total_tokens': self.total_tokens,
            'total_prompt_tokens': self.total_prompt_tokens,
            'total_completion_tokens': self.total_completion_tokens,
            'total_cost': self.total_cost,
            'total_messages': self.total_messages,
            'conversation_metadata': self.conversation_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_metrics_from_transaction(self, transaction):
        """Atualiza métricas da conversa baseado em uma transação"""
        if transaction.status == 'success':
            self.total_tokens += transaction.total_tokens or 0
            self.total_prompt_tokens += transaction.prompt_tokens or 0
            self.total_completion_tokens += transaction.completion_tokens or 0
            self.total_cost += transaction.total_cost or 0.0
    
    def get_avg_cost_per_message(self) -> float:
        """Calcula custo médio por mensagem"""
        if self.total_messages == 0:
            return 0.0
        return self.total_cost / self.total_messages
    
    def get_avg_tokens_per_message(self) -> float:
        """Calcula tokens médios por mensagem"""
        if self.total_messages == 0:
            return 0.0
        return self.total_tokens / self.total_messages

class Message(BaseModel):
    __tablename__ = 'messages'
    
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    message_metadata = Column(JSON, nullable=True)  # Para armazenar dados adicionais
    
    # Relacionamento com Conversation
    conversation = relationship("Conversation", backref="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"