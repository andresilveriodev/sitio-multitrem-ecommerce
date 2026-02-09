#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelo Transaction para armazenar transações de IA
Armazena requests, responses, tokens gastos e custos
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class AITransaction(BaseModel):
    """Modelo para armazenar transações de IA"""
    __tablename__ = 'transactions'
    
    # Identificação
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Relacionamentos
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('public.users.id'), nullable=True, index=True)
    username = Column(String(50), nullable=True, index=True)  # Para facilitar consultas
    
    # Informações da requisição
    provider = Column(String(50), nullable=False, index=True)  # openai, deepseek, ollama
    model = Column(String(100), nullable=False, index=True)    # gpt-5-nano, etc
    endpoint = Column(String(100), nullable=False)             # /ai/generate, /ai/generate/stream
    
    # Dados da requisição
    request_data = Column(JSON, nullable=False)                # Dados completos da requisição
    response_data = Column(JSON, nullable=True)                # Dados completos da resposta
    
    # Métricas de tokens
    prompt_tokens = Column(Integer, nullable=True, default=0)
    completion_tokens = Column(Integer, nullable=True, default=0)
    total_tokens = Column(Integer, nullable=True, default=0)
    
    # Métricas de custo
    prompt_cost = Column(Float, nullable=True, default=0.0)    # Custo dos tokens de prompt
    completion_cost = Column(Float, nullable=True, default=0.0) # Custo dos tokens de completion
    total_cost = Column(Float, nullable=True, default=0.0)     # Custo total
    
    # Métricas de performance
    response_time_ms = Column(Integer, nullable=True)          # Tempo de resposta em ms
    is_streaming = Column(Boolean, default=False)             # Se foi streaming
    chunks_count = Column(Integer, nullable=True, default=0)   # Número de chunks (streaming)
    
    # Status e controle
    status = Column(String(20), nullable=False, default='pending') # pending, success, error
    error_message = Column(Text, nullable=True)                # Mensagem de erro se houver
    
    # Metadados
    ip_address = Column(String(45), nullable=True)            # IP do cliente
    user_agent = Column(String(500), nullable=True)           # User agent
    session_id = Column(String(100), nullable=True)           # ID da sessão
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)             # Quando a transação foi completada
    
    # Relacionamentos
    conversation = relationship("Conversation", back_populates="transactions")
    
    def __repr__(self):
        return f"<AITransaction(id={self.id}, provider={self.provider}, model={self.model}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'provider': self.provider,
            'model': self.model,
            'endpoint': self.endpoint,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'prompt_cost': self.prompt_cost,
            'completion_cost': self.completion_cost,
            'total_cost': self.total_cost,
            'response_time_ms': self.response_time_ms,
            'is_streaming': self.is_streaming,
            'chunks_count': self.chunks_count,
            'status': self.status,
            'error_message': self.error_message,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def create_ai_transaction(
        cls,
        transaction_id: str,
        provider: str,
        model: str,
        endpoint: str,
        request_data: Dict[str, Any],
        conversation_id: Optional[int] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> 'AITransaction':
        """Cria uma nova transação"""
        return cls(
            transaction_id=transaction_id,
            provider=provider,
            model=model,
            endpoint=endpoint,
            request_data=request_data,
            conversation_id=conversation_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            status='pending'
        )
    
    def complete_transaction(
        self,
        response_data: Dict[str, Any],
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        prompt_cost: float,
        completion_cost: float,
        total_cost: float,
        response_time_ms: int,
        is_streaming: bool = False,
        chunks_count: int = 0
    ):
        """Completa a transação com os dados de resposta"""
        self.response_data = response_data
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.prompt_cost = prompt_cost
        self.completion_cost = completion_cost
        self.total_cost = total_cost
        self.response_time_ms = response_time_ms
        self.is_streaming = is_streaming
        self.chunks_count = chunks_count
        self.status = 'success'
        self.completed_at = datetime.utcnow()
    
    def mark_error(self, error_message: str):
        """Marca a transação como erro"""
        self.status = 'error'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()