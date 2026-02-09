"""Serviço para tracking de transações e cálculo de custos de IA"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from models.transaction import AITransaction
from models.usage import Usage, UsageSummary
from models.conversation import Conversation
from app.db import Session as DBSession
import logging
import json

logger = logging.getLogger(__name__)

class TransactionService:
    """Serviço para gerenciar transações e métricas de uso"""
    
    # Preços por token para diferentes modelos (em USD)
    TOKEN_PRICES = {
        'gpt-4o-mini': {
            'prompt': 0.00015 / 1000,  # $0.15 per 1K tokens
            'completion': 0.0006 / 1000  # $0.60 per 1K tokens
        },
        'gpt-4.1-nano': {
            'prompt': 0.0001 / 1000,   # $0.10 per 1K tokens
            'completion': 0.0004 / 1000  # $0.40 per 1K tokens
        },
        'gpt-5-nano': {
            'prompt': 0.0001 / 1000,   # $0.10 per 1K tokens
            'completion': 0.0004 / 1000  # $0.40 per 1K tokens
        },
        'gpt-5-mini': {
            'prompt': 0.00015 / 1000,  # $0.15 per 1K tokens
            'completion': 0.0006 / 1000  # $0.60 per 1K tokens
        }
    }
    
    @classmethod
    def create_transaction(
        cls,
        user_id: int,
        conversation_id: Optional[int],
        provider: str,
        model: str,
        request_data: Dict[str, Any],
        endpoint: str = '/ai/generate'
    ) -> AITransaction:
        """Cria uma nova transação"""
        db = DBSession()
        try:
            transaction = AITransaction(
                user_id=user_id,
                conversation_id=conversation_id,
                provider=provider,
                model=model,
                endpoint=endpoint,
                request_data=request_data,
                status='pending'
            )
            
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            
            logger.info(f"Transação criada: {transaction.id}")
            return transaction
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao criar transação: {e}")
            raise
        finally:
            db.close()
    
    @classmethod
    def complete_transaction(
        cls,
        transaction_id: int,
        response_data: Dict[str, Any],
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ) -> AITransaction:
        """Completa uma transação com sucesso"""
        db = DBSession()
        try:
            transaction = db.query(AITransaction).filter(AITransaction.id == transaction_id).first()
            if not transaction:
                raise ValueError(f"Transação {transaction_id} não encontrada")
            
            # Calcular custo
            cost = cls.calculate_cost(transaction.model, prompt_tokens, completion_tokens)
            
            # Atualizar transação
            transaction.complete(
                response_data=response_data,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                total_cost=cost
            )
            
            # Atualizar métricas do usuário
            # TODO: Implementar modelo User ou integração com serviço de usuários
            # user = db.query(User).filter(User.id == transaction.user_id).first()
            # if user:
            #     user.update_metrics_from_transaction(transaction)
            
            # Atualizar métricas da conversa
            if transaction.conversation_id:
                conversation = db.query(Conversation).filter(Conversation.id == transaction.conversation_id).first()
                if conversation:
                    conversation.update_metrics_from_transaction(transaction)
            
            # Atualizar estatísticas de uso
            cls._update_usage_stats(db, transaction)
            
            db.commit()
            db.refresh(transaction)
            
            logger.info(f"Transação {transaction_id} completada com sucesso")
            return transaction
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao completar transação {transaction_id}: {e}")
            raise
        finally:
            db.close()
    
    @classmethod
    def fail_transaction(
        cls,
        transaction_id: int,
        error_message: str,
        error_code: Optional[str] = None
    ) -> AITransaction:
        """Marca uma transação como falha"""
        db = DBSession()
        try:
            transaction = db.query(AITransaction).filter(AITransaction.id == transaction_id).first()
            if not transaction:
                raise ValueError(f"Transação {transaction_id} não encontrada")
            
            transaction.mark_error(error_message, error_code)
            
            # Ainda atualizar contador de requests do usuário
            # TODO: Implementar modelo User ou integração com serviço de usuários
            # user = db.query(User).filter(User.id == transaction.user_id).first()
            # if user:
            #     user.total_requests += 1
            
            db.commit()
            db.refresh(transaction)
            
            logger.warning(f"Transação {transaction_id} marcada como falha: {error_message}")
            return transaction
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erro ao marcar transação {transaction_id} como falha: {e}")
            raise
        finally:
            db.close()
    
    @classmethod
    def calculate_cost(cls, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calcula o custo de uma transação baseado no modelo e tokens"""
        if model not in cls.TOKEN_PRICES:
            logger.warning(f"Modelo {model} não encontrado na tabela de preços")
            return 0.0
        
        prices = cls.TOKEN_PRICES[model]
        prompt_cost = prompt_tokens * prices['prompt']
        completion_cost = completion_tokens * prices['completion']
        
        total_cost = prompt_cost + completion_cost
        
        logger.debug(f"Custo calculado para {model}: prompt={prompt_cost:.6f}, completion={completion_cost:.6f}, total={total_cost:.6f}")
        return total_cost
    
    @classmethod
    def get_user_transactions(
        cls,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AITransaction]:
        """Busca transações de um usuário"""
        db = DBSession()
        try:
            query = db.query(AITransaction).filter(AITransaction.user_id == user_id)
            
            if status:
                query = query.filter(AITransaction.status == status)
            
            if start_date:
                query = query.filter(AITransaction.created_at >= start_date)
            
            if end_date:
                query = query.filter(AITransaction.created_at <= end_date)
            
            transactions = query.order_by(AITransaction.created_at.desc()).offset(offset).limit(limit).all()
            
            return transactions
            
        finally:
            db.close()
    
    @classmethod
    def get_usage_summary(
        cls,
        user_id: Optional[int] = None,
        model: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Gera resumo de uso"""
        db = DBSession()
        try:
            query = db.query(
                func.count(AITransaction.id).label('total_requests'),
                func.sum(AITransaction.total_tokens).label('total_tokens'),
                func.sum(AITransaction.prompt_tokens).label('total_prompt_tokens'),
                func.sum(AITransaction.completion_tokens).label('total_completion_tokens'),
                func.sum(AITransaction.total_cost).label('total_cost'),
                func.avg(AITransaction.response_time_ms).label('avg_response_time')
            ).filter(AITransaction.status == 'success')
            
            if user_id:
                query = query.filter(AITransaction.user_id == user_id)
            
            if model:
                query = query.filter(AITransaction.model == model)
            
            if start_date:
                query = query.filter(AITransaction.created_at >= start_date)
            
            if end_date:
                query = query.filter(AITransaction.created_at <= end_date)
            
            result = query.first()
            
            return {
                'total_requests': result.total_requests or 0,
                'total_tokens': result.total_tokens or 0,
                'total_prompt_tokens': result.total_prompt_tokens or 0,
                'total_completion_tokens': result.total_completion_tokens or 0,
                'total_cost': float(result.total_cost or 0.0),
                'avg_response_time_ms': float(result.avg_response_time or 0.0)
            }
            
        finally:
            db.close()
    
    @classmethod
    def _update_usage_stats(cls, db: Session, transaction: AITransaction):
        """Atualiza estatísticas de uso agregadas"""
        try:
            # Buscar ou criar registro de uso para hoje
            today = datetime.now().date()
            
            usage = db.query(Usage).filter(
                and_(
                    Usage.user_id == transaction.user_id,
                    Usage.model == transaction.model,
                    Usage.date == today
                )
            ).first()
            
            if not usage:
                usage = Usage(
                    user_id=transaction.user_id,
                    model=transaction.model,
                    provider=transaction.provider,
                    date=today
                )
                db.add(usage)
            
            # Atualizar métricas
            usage.total_requests += 1
            
            if transaction.status == 'success':
                usage.successful_requests += 1
                usage.total_tokens += transaction.total_tokens or 0
                usage.prompt_tokens += transaction.prompt_tokens or 0
                usage.completion_tokens += transaction.completion_tokens or 0
                usage.total_cost += transaction.total_cost or 0.0
                
                if transaction.response_time_ms:
                    # Calcular nova média de tempo de resposta
                    if usage.avg_response_time_ms == 0:
                        usage.avg_response_time_ms = transaction.response_time_ms
                    else:
                        usage.avg_response_time_ms = (
                            (usage.avg_response_time_ms * (usage.successful_requests - 1) + transaction.response_time_ms) /
                            usage.successful_requests
                        )
            else:
                usage.failed_requests += 1
            
            logger.debug(f"Estatísticas de uso atualizadas para usuário {transaction.user_id}, modelo {transaction.model}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas de uso: {e}")
            # Não fazer rollback aqui, apenas logar o erro