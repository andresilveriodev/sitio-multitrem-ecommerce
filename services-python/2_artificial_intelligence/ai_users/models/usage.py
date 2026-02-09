#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelo Usage para métricas de uso agregadas
Armazena estatísticas por período, modelo e usuário
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.base import BaseModel
from datetime import datetime, date
from typing import Optional, Dict, Any

class Usage(BaseModel):
    """Modelo para métricas de uso agregadas"""
    __tablename__ = 'usage'
    
    # Identificação
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Relacionamentos
    user_id = Column(Integer, nullable=True, index=True)  # Temporariamente sem FK para permitir inicialização
    username = Column(String(50), nullable=True, index=True)  # Para facilitar consultas
    
    # Dimensões de agregação
    provider = Column(String(50), nullable=False, index=True)  # openai, deepseek, ollama
    model = Column(String(100), nullable=False, index=True)    # gpt-5-nano, etc
    date = Column(Date, nullable=False, index=True)            # Data da agregação
    period_type = Column(String(20), nullable=False, default='daily') # daily, weekly, monthly
    
    # Métricas de transações
    total_requests = Column(Integer, nullable=False, default=0)
    successful_requests = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)
    streaming_requests = Column(Integer, nullable=False, default=0)
    
    # Métricas de tokens
    total_prompt_tokens = Column(Integer, nullable=False, default=0)
    total_completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    
    # Métricas de custo
    total_prompt_cost = Column(Float, nullable=False, default=0.0)
    total_completion_cost = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)
    
    # Métricas de performance
    avg_response_time_ms = Column(Float, nullable=True)
    min_response_time_ms = Column(Integer, nullable=True)
    max_response_time_ms = Column(Integer, nullable=True)
    total_chunks = Column(Integer, nullable=False, default=0)  # Para streaming
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Índices compostos para performance
    __table_args__ = (
        Index('idx_usage_user_date', 'user_id', 'date'),
        Index('idx_usage_provider_model_date', 'provider', 'model', 'date'),
        Index('idx_usage_date_period', 'date', 'period_type'),
    )
    
    def __repr__(self):
        return f"<Usage(id={self.id}, provider={self.provider}, model={self.model}, date={self.date}, requests={self.total_requests})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'model': self.model,
            'date': self.date.isoformat() if self.date else None,
            'period_type': self.period_type,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'streaming_requests': self.streaming_requests,
            'total_prompt_tokens': self.total_prompt_tokens,
            'total_completion_tokens': self.total_completion_tokens,
            'total_tokens': self.total_tokens,
            'total_prompt_cost': self.total_prompt_cost,
            'total_completion_cost': self.total_completion_cost,
            'total_cost': self.total_cost,
            'avg_response_time_ms': self.avg_response_time_ms,
            'min_response_time_ms': self.min_response_time_ms,
            'max_response_time_ms': self.max_response_time_ms,
            'total_chunks': self.total_chunks,
            'success_rate': self.get_success_rate(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_success_rate(self) -> float:
        """Calcula a taxa de sucesso"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_avg_tokens_per_request(self) -> float:
        """Calcula a média de tokens por requisição"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_tokens / self.successful_requests
    
    def get_avg_cost_per_request(self) -> float:
        """Calcula o custo médio por requisição"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_cost / self.successful_requests
    
    @classmethod
    def get_or_create(
        cls,
        session,
        user_id: Optional[int],
        provider: str,
        model: str,
        date_obj: date,
        period_type: str = 'daily'
    ) -> 'Usage':
        """Obtém ou cria um registro de uso"""
        usage = session.query(cls).filter(
            cls.user_id == user_id,
            cls.provider == provider,
            cls.model == model,
            cls.date == date_obj,
            cls.period_type == period_type
        ).first()
        
        if not usage:
            usage = cls(
                user_id=user_id,
                provider=provider,
                model=model,
                date=date_obj,
                period_type=period_type
            )
            session.add(usage)
            session.flush()  # Para obter o ID
        
        return usage
    
    def update_from_transaction(self, transaction):
        """Atualiza métricas baseado em uma transação"""
        # Incrementa contadores
        self.total_requests += 1
        
        if transaction.status == 'success':
            self.successful_requests += 1
            
            # Atualiza tokens
            if transaction.total_tokens:
                self.total_prompt_tokens += transaction.prompt_tokens or 0
                self.total_completion_tokens += transaction.completion_tokens or 0
                self.total_tokens += transaction.total_tokens
            
            # Atualiza custos
            if transaction.total_cost:
                self.total_prompt_cost += transaction.prompt_cost or 0.0
                self.total_completion_cost += transaction.completion_cost or 0.0
                self.total_cost += transaction.total_cost
            
            # Atualiza métricas de performance
            if transaction.response_time_ms:
                if self.avg_response_time_ms is None:
                    self.avg_response_time_ms = float(transaction.response_time_ms)
                    self.min_response_time_ms = transaction.response_time_ms
                    self.max_response_time_ms = transaction.response_time_ms
                else:
                    # Recalcula média ponderada
                    total_time = (self.avg_response_time_ms * (self.successful_requests - 1)) + transaction.response_time_ms
                    self.avg_response_time_ms = total_time / self.successful_requests
                    
                    # Atualiza min/max
                    if transaction.response_time_ms < self.min_response_time_ms:
                        self.min_response_time_ms = transaction.response_time_ms
                    if transaction.response_time_ms > self.max_response_time_ms:
                        self.max_response_time_ms = transaction.response_time_ms
            
            # Streaming
            if transaction.is_streaming:
                self.streaming_requests += 1
                self.total_chunks += transaction.chunks_count or 0
        
        elif transaction.status == 'error':
            self.failed_requests += 1
        
        # Atualiza timestamp
        self.updated_at = datetime.utcnow()

class UsageSummary(BaseModel):
    """Modelo para resumos de uso por período mais amplo"""
    __tablename__ = 'usage_summary'
    
    # Identificação
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Dimensões
    user_id = Column(Integer, nullable=True, index=True)  # Temporariamente sem FK para permitir inicialização
    provider = Column(String(50), nullable=True, index=True)   # NULL = todos os provedores
    model = Column(String(100), nullable=True, index=True)     # NULL = todos os modelos
    
    # Período
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # weekly, monthly, yearly
    
    # Métricas agregadas
    total_requests = Column(Integer, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0.0)
    total_tokens = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    # user = relationship("User")  # Comentado temporariamente - modelo User não existe no serviço
    
    def __repr__(self):
        return f"<UsageSummary(id={self.id}, period={self.period_start}-{self.period_end}, requests={self.total_requests})>"