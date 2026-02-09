"""Endpoints para análise e relatórios de uso da API de IA"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from services.transaction_service import TransactionService
from models.transaction import Transaction
from models.usage import Usage
from models.user import User
from app.db import Session as DBSession
from sqlalchemy import func, and_, desc
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Modelos Pydantic para responses
class UsageSummaryResponse(BaseModel):
    total_requests: int
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost: float
    avg_response_time_ms: float
    success_rate: float

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    conversation_id: Optional[int]
    provider: str
    model: str
    endpoint: str
    status: str
    total_tokens: Optional[int]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_cost: Optional[float]
    response_time_ms: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

class ModelUsageResponse(BaseModel):
    model: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    total_cost: float
    avg_response_time_ms: float
    success_rate: float

class UserStatsResponse(BaseModel):
    user_id: int
    username: str
    total_requests: int
    total_tokens_used: int
    total_cost_spent: float
    total_conversations: int
    avg_cost_per_request: float
    avg_tokens_per_request: float
    avg_cost_per_conversation: float

class DailyUsageResponse(BaseModel):
    date: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    total_cost: float
    unique_users: int

# Dependency para obter sessão do banco
def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()

@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    user_id: Optional[int] = Query(None, description="ID do usuário específico"),
    model: Optional[str] = Query(None, description="Modelo específico"),
    start_date: Optional[datetime] = Query(None, description="Data de início (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Data de fim (ISO format)"),
    db: DBSession = Depends(get_db)
):
    """Retorna resumo geral de uso da API"""
    try:
        # Usar o serviço para obter resumo
        summary = TransactionService.get_usage_summary(
            user_id=user_id,
            model=model,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calcular taxa de sucesso
        query = db.query(
            func.count(Transaction.id).label('total'),
            func.sum(func.case([(Transaction.status == 'success', 1)], else_=0)).label('successful')
        )
        
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        if model:
            query = query.filter(Transaction.model == model)
        if start_date:
            query = query.filter(Transaction.created_at >= start_date)
        if end_date:
            query = query.filter(Transaction.created_at <= end_date)
        
        result = query.first()
        total_requests = result.total or 0
        successful_requests = result.successful or 0
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return UsageSummaryResponse(
            **summary,
            success_rate=success_rate
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter resumo de uso: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    user_id: Optional[int] = Query(None, description="ID do usuário"),
    status: Optional[str] = Query(None, description="Status da transação"),
    model: Optional[str] = Query(None, description="Modelo usado"),
    start_date: Optional[datetime] = Query(None, description="Data de início"),
    end_date: Optional[datetime] = Query(None, description="Data de fim"),
    limit: int = Query(50, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    db: DBSession = Depends(get_db)
):
    """Lista transações com filtros"""
    try:
        query = db.query(Transaction)
        
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        if status:
            query = query.filter(Transaction.status == status)
        if model:
            query = query.filter(Transaction.model == model)
        if start_date:
            query = query.filter(Transaction.created_at >= start_date)
        if end_date:
            query = query.filter(Transaction.created_at <= end_date)
        
        transactions = query.order_by(desc(Transaction.created_at)).offset(offset).limit(limit).all()
        
        return [TransactionResponse(
            id=t.id,
            user_id=t.user_id,
            conversation_id=t.conversation_id,
            provider=t.provider,
            model=t.model,
            endpoint=t.endpoint,
            status=t.status,
            total_tokens=t.total_tokens,
            prompt_tokens=t.prompt_tokens,
            completion_tokens=t.completion_tokens,
            total_cost=t.total_cost,
            response_time_ms=t.response_time_ms,
            created_at=t.created_at,
            completed_at=t.completed_at,
            error_message=t.error_message
        ) for t in transactions]
        
    except Exception as e:
        logger.error(f"Erro ao listar transações: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/models", response_model=List[ModelUsageResponse])
async def get_model_usage(
    start_date: Optional[datetime] = Query(None, description="Data de início"),
    end_date: Optional[datetime] = Query(None, description="Data de fim"),
    db: DBSession = Depends(get_db)
):
    """Estatísticas de uso por modelo"""
    try:
        query = db.query(
            Transaction.model,
            func.count(Transaction.id).label('total_requests'),
            func.sum(func.case([(Transaction.status == 'success', 1)], else_=0)).label('successful_requests'),
            func.sum(func.case([(Transaction.status != 'success', 1)], else_=0)).label('failed_requests'),
            func.sum(Transaction.total_tokens).label('total_tokens'),
            func.sum(Transaction.total_cost).label('total_cost'),
            func.avg(Transaction.response_time_ms).label('avg_response_time_ms')
        )
        
        if start_date:
            query = query.filter(Transaction.created_at >= start_date)
        if end_date:
            query = query.filter(Transaction.created_at <= end_date)
        
        results = query.group_by(Transaction.model).all()
        
        model_stats = []
        for result in results:
            total_requests = result.total_requests or 0
            successful_requests = result.successful_requests or 0
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            model_stats.append(ModelUsageResponse(
                model=result.model,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=result.failed_requests or 0,
                total_tokens=result.total_tokens or 0,
                total_cost=float(result.total_cost or 0.0),
                avg_response_time_ms=float(result.avg_response_time_ms or 0.0),
                success_rate=success_rate
            ))
        
        return model_stats
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas por modelo: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/users", response_model=List[UserStatsResponse])
async def get_user_stats(
    limit: int = Query(50, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    db: DBSession = Depends(get_db)
):
    """Estatísticas de uso por usuário"""
    try:
        users = db.query(User).offset(offset).limit(limit).all()
        
        user_stats = []
        for user in users:
            user_stats.append(UserStatsResponse(
                user_id=user.id,
                username=user.username,
                total_requests=user.total_requests,
                total_tokens_used=user.total_tokens_used,
                total_cost_spent=user.total_cost_spent,
                total_conversations=user.total_conversations,
                avg_cost_per_request=user.get_avg_cost_per_request(),
                avg_tokens_per_request=user.get_avg_tokens_per_request(),
                avg_cost_per_conversation=user.get_avg_cost_per_conversation()
            ))
        
        return user_stats
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de usuários: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/daily", response_model=List[DailyUsageResponse])
async def get_daily_usage(
    days: int = Query(30, ge=1, le=365, description="Número de dias para retornar"),
    db: DBSession = Depends(get_db)
):
    """Uso diário da API"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Usar a tabela Usage para dados agregados diários
        query = db.query(
            Usage.date,
            func.sum(Usage.total_requests).label('total_requests'),
            func.sum(Usage.successful_requests).label('successful_requests'),
            func.sum(Usage.failed_requests).label('failed_requests'),
            func.sum(Usage.total_tokens).label('total_tokens'),
            func.sum(Usage.total_cost).label('total_cost'),
            func.count(func.distinct(Usage.user_id)).label('unique_users')
        ).filter(Usage.date >= start_date.date())
        
        results = query.group_by(Usage.date).order_by(Usage.date).all()
        
        daily_stats = []
        for result in results:
            daily_stats.append(DailyUsageResponse(
                date=result.date.isoformat(),
                total_requests=result.total_requests or 0,
                successful_requests=result.successful_requests or 0,
                failed_requests=result.failed_requests or 0,
                total_tokens=result.total_tokens or 0,
                total_cost=float(result.total_cost or 0.0),
                unique_users=result.unique_users or 0
            ))
        
        return daily_stats
        
    except Exception as e:
        logger.error(f"Erro ao obter uso diário: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@router.get("/health")
async def analytics_health():
    """Health check para o módulo de analytics"""
    return {
        "status": "healthy",
        "module": "analytics",
        "timestamp": datetime.now().isoformat()
    }