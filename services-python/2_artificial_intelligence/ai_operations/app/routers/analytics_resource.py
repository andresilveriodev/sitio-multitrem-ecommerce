"""Endpoints para consulta de estatísticas e relatórios de uso"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app.db import get_db
from models.transaction import AITransaction
from models.usage import Usage, UsageSummary
from models.conversation import Conversation
from services.transaction_service import TransactionService
from services.alert_service import alert_service
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Modelos Pydantic para responses
class UsageStatsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
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

class ModelStatsResponse(BaseModel):
    model: str
    provider: str
    total_requests: int
    total_tokens: int
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

@router.get("/health")
async def analytics_health():
    """Health check para o módulo de analytics"""
    return {"status": "ok", "module": "analytics"}

@router.get("/usage/summary", response_model=UsageStatsResponse)
async def get_usage_summary(
    user_id: Optional[int] = Query(None, description="ID do usuário (opcional)"),
    model: Optional[str] = Query(None, description="Modelo específico (opcional)"),
    provider: Optional[str] = Query(None, description="Provedor específico (opcional)"),
    start_date: Optional[datetime] = Query(None, description="Data de início (opcional)"),
    end_date: Optional[datetime] = Query(None, description="Data de fim (opcional)"),
    db: Session = Depends(get_db)
):
    """Retorna resumo de uso geral ou filtrado"""
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
            func.count(AITransaction.id).label('total'),
            func.sum(func.case([(AITransaction.status == 'success', 1)], else_=0)).label('successful')
        )
        
        if user_id:
            query = query.filter(AITransaction.user_id == user_id)
        if model:
            query = query.filter(AITransaction.model == model)
        if provider:
            query = query.filter(AITransaction.provider == provider)
        if start_date:
            query = query.filter(AITransaction.created_at >= start_date)
        if end_date:
            query = query.filter(AITransaction.created_at <= end_date)
        
        result = query.first()
        total_requests = result.total or 0
        successful_requests = result.successful or 0
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return UsageStatsResponse(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_tokens=summary['total_tokens'],
            total_prompt_tokens=summary['total_prompt_tokens'],
            total_completion_tokens=summary['total_completion_tokens'],
            total_cost=summary['total_cost'],
            avg_response_time_ms=summary['avg_response_time_ms'],
            success_rate=round(success_rate, 2)
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter resumo de uso: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/users/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Retorna estatísticas de uso de um usuário específico"""
    try:
        # Buscar transações do usuário
        transactions = db.query(AITransaction).filter(AITransaction.user_id == user_id).all()
        
        # Buscar conversas do usuário
        conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
        
        # Calcular estatísticas
        total_requests = len(transactions)
        successful_requests = len([t for t in transactions if t.status == 'success'])
        total_tokens_used = sum(t.total_tokens or 0 for t in transactions)
        total_cost_spent = sum(t.total_cost or 0.0 for t in transactions)
        total_conversations = len(conversations)
        
        # Calcular médias
        avg_cost_per_request = total_cost_spent / total_requests if total_requests > 0 else 0.0
        avg_tokens_per_request = total_tokens_used / total_requests if total_requests > 0 else 0.0
        avg_cost_per_conversation = total_cost_spent / total_conversations if total_conversations > 0 else 0.0
        
        # Buscar username (assumindo que está na primeira conversa ou usar padrão)
        username = "user_" + str(user_id)
        if conversations:
            username = conversations[0].username or username
        
        return UserStatsResponse(
            user_id=user_id,
            username=username,
            total_requests=total_requests,
            total_tokens_used=total_tokens_used,
            total_cost_spent=round(total_cost_spent, 4),
            total_conversations=total_conversations,
            avg_cost_per_request=round(avg_cost_per_request, 4),
            avg_tokens_per_request=round(avg_tokens_per_request, 2),
            avg_cost_per_conversation=round(avg_cost_per_conversation, 4)
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/users/stats", response_model=List[UserStatsResponse])
async def get_users_stats(
    limit: int = Query(50, description="Limite de usuários"),
    offset: int = Query(0, description="Offset para paginação"),
    order_by: str = Query("total_cost_spent", description="Campo para ordenação"),
    db: Session = Depends(get_db)
):
    """Retorna estatísticas de uso por usuário"""
    try:
        # Buscar todos os usuários únicos que têm transações
        user_ids = db.query(AITransaction.user_id).distinct().all()
        user_ids = [uid[0] for uid in user_ids if uid[0] is not None]
        
        # Limitar e paginar
        user_ids = user_ids[offset:offset + limit]
        
        result = []
        for uid in user_ids:
            # Buscar estatísticas de cada usuário
            user_stats = await get_user_stats(uid, db)
            result.append(user_stats)
        
        # Ordenar por campo especificado
        if order_by == 'total_requests':
            result.sort(key=lambda x: x.total_requests, reverse=True)
        elif order_by == 'total_tokens_used':
            result.sort(key=lambda x: x.total_tokens_used, reverse=True)
        elif order_by == 'total_conversations':
            result.sort(key=lambda x: x.total_conversations, reverse=True)
        else:  # total_cost_spent (padrão)
            result.sort(key=lambda x: x.total_cost_spent, reverse=True)
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de usuários: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/models/stats", response_model=List[ModelStatsResponse])
async def get_models_stats(
    start_date: Optional[datetime] = Query(None, description="Data de início (opcional)"),
    end_date: Optional[datetime] = Query(None, description="Data de fim (opcional)"),
    db: Session = Depends(get_db)
):
    """Retorna estatísticas de uso por modelo"""
    try:
        query = db.query(
            AITransaction.model,
            AITransaction.provider,
            func.count(AITransaction.id).label('total_requests'),
            func.sum(AITransaction.total_tokens).label('total_tokens'),
            func.sum(AITransaction.total_cost).label('total_cost'),
            func.avg(AITransaction.response_time_ms).label('avg_response_time_ms'),
            func.sum(func.case([(AITransaction.status == 'success', 1)], else_=0)).label('successful_requests')
        ).filter(AITransaction.status.in_(['success', 'error']))
        
        if start_date:
            query = query.filter(AITransaction.created_at >= start_date)
        if end_date:
            query = query.filter(AITransaction.created_at <= end_date)
        
        results = query.group_by(AITransaction.model, AITransaction.provider).all()
        
        model_stats = []
        for result in results:
            total_requests = result.total_requests or 0
            successful_requests = result.successful_requests or 0
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            model_stats.append(ModelStatsResponse(
                model=result.model,
                provider=result.provider,
                total_requests=total_requests,
                total_tokens=result.total_tokens or 0,
                total_cost=float(result.total_cost or 0.0),
                avg_response_time_ms=float(result.avg_response_time_ms or 0.0),
                success_rate=round(success_rate, 2)
            ))
        
        return model_stats
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de modelos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    user_id: Optional[int] = Query(None, description="ID do usuário (opcional)"),
    status: Optional[str] = Query(None, description="Status da transação (opcional)"),
    model: Optional[str] = Query(None, description="Modelo específico (opcional)"),
    limit: int = Query(50, description="Limite de transações"),
    offset: int = Query(0, description="Offset para paginação"),
    start_date: Optional[datetime] = Query(None, description="Data de início (opcional)"),
    end_date: Optional[datetime] = Query(None, description="Data de fim (opcional)"),
    db: Session = Depends(get_db)
):
    """Retorna lista de transações com filtros"""
    try:
        query = db.query(AITransaction)
        
        if user_id:
            query = query.filter(AITransaction.user_id == user_id)
        if status:
            query = query.filter(AITransaction.status == status)
        if model:
            query = query.filter(AITransaction.model == model)
        if start_date:
            query = query.filter(AITransaction.created_at >= start_date)
        if end_date:
            query = query.filter(AITransaction.created_at <= end_date)
        
        transactions = query.order_by(desc(AITransaction.created_at)).offset(offset).limit(limit).all()
        
        result = []
        for transaction in transactions:
            result.append(TransactionResponse(
                id=transaction.id,
                user_id=transaction.user_id,
                conversation_id=transaction.conversation_id,
                provider=transaction.provider,
                model=transaction.model,
                endpoint=transaction.endpoint,
                status=transaction.status,
                total_tokens=transaction.total_tokens,
                prompt_tokens=transaction.prompt_tokens,
                completion_tokens=transaction.completion_tokens,
                total_cost=transaction.total_cost,
                response_time_ms=transaction.response_time_ms,
                created_at=transaction.created_at,
                completed_at=transaction.completed_at
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao obter transações: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/usage/daily")
async def get_daily_usage(
    user_id: Optional[int] = Query(None, description="ID do usuário (opcional)"),
    model: Optional[str] = Query(None, description="Modelo específico (opcional)"),
    days: int = Query(30, description="Número de dias para buscar"),
    db: Session = Depends(get_db)
):
    """Retorna uso diário agregado"""
    try:
        start_date = datetime.now().date() - timedelta(days=days)
        
        query = db.query(
            Usage.date,
            func.sum(Usage.total_requests).label('total_requests'),
            func.sum(Usage.successful_requests).label('successful_requests'),
            func.sum(Usage.failed_requests).label('failed_requests'),
            func.sum(Usage.total_tokens).label('total_tokens'),
            func.sum(Usage.total_cost).label('total_cost')
        ).filter(Usage.date >= start_date)
        
        if user_id:
            query = query.filter(Usage.user_id == user_id)
        if model:
            query = query.filter(Usage.model == model)
        
        results = query.group_by(Usage.date).order_by(Usage.date).all()
        
        daily_usage = []
        for result in results:
            daily_usage.append({
                'date': result.date.isoformat(),
                'total_requests': result.total_requests or 0,
                'successful_requests': result.successful_requests or 0,
                'failed_requests': result.failed_requests or 0,
                'total_tokens': result.total_tokens or 0,
                'total_cost': float(result.total_cost or 0.0)
            })
        
        return {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'daily_usage': daily_usage
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter uso diário: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/costs/breakdown")
async def get_costs_breakdown(
    user_id: Optional[int] = Query(None, description="ID do usuário (opcional)"),
    start_date: Optional[datetime] = Query(None, description="Data de início (opcional)"),
    end_date: Optional[datetime] = Query(None, description="Data de fim (opcional)"),
    db: Session = Depends(get_db)
):
    """Retorna breakdown de custos por modelo e provedor"""
    try:
        query = db.query(
            AITransaction.provider,
            AITransaction.model,
            func.sum(AITransaction.total_cost).label('total_cost'),
            func.sum(AITransaction.total_tokens).label('total_tokens'),
            func.count(AITransaction.id).label('total_requests')
        ).filter(AITransaction.status == 'success')
        
        if user_id:
            query = query.filter(AITransaction.user_id == user_id)
        if start_date:
            query = query.filter(AITransaction.created_at >= start_date)
        if end_date:
            query = query.filter(AITransaction.created_at <= end_date)
        
        results = query.group_by(AITransaction.provider, AITransaction.model).all()
        
        breakdown = []
        total_cost = 0
        
        for result in results:
            cost = float(result.total_cost or 0.0)
            total_cost += cost
            
            breakdown.append({
                'provider': result.provider,
                'model': result.model,
                'total_cost': cost,
                'total_tokens': result.total_tokens or 0,
                'total_requests': result.total_requests or 0,
                'avg_cost_per_request': cost / (result.total_requests or 1)
            })
        
        # Adicionar percentuais
        for item in breakdown:
            item['cost_percentage'] = (item['total_cost'] / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_cost': total_cost,
            'breakdown': sorted(breakdown, key=lambda x: x['total_cost'], reverse=True)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter breakdown de custos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


# Modelos para alertas
class AlertResponse(BaseModel):
    type: str
    severity: str
    message: str
    user_id: int
    current_value: float
    limit_value: float
    period: str
    timestamp: datetime

class UsageSummaryResponse(BaseModel):
    user_id: int
    daily: Dict[str, Any]
    monthly: Dict[str, Any]
    timestamp: datetime


@router.get("/alerts/user/{user_id}", response_model=List[AlertResponse])
def get_user_alerts(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Obter alertas de limites para um usuário específico
    """
    try:
        alerts = alert_service.check_user_limits(user_id, db)
        return alerts
        
    except Exception as e:
        logger.error(f"Erro ao obter alertas do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/alerts/all")
def get_all_alerts(
    db: Session = Depends(get_db)
):
    """
    Obter alertas de limites para todos os usuários ativos
    """
    try:
        all_alerts = alert_service.check_all_users_limits(db)
        return all_alerts
        
    except Exception as e:
        logger.error(f"Erro ao obter alertas de todos os usuários: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/usage/summary/{user_id}", response_model=UsageSummaryResponse)
def get_usage_summary(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Obter resumo de uso atual do usuário com limites
    """
    try:
        summary = alert_service.get_usage_summary(user_id, db)
        if not summary:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter resumo de uso do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/limits/check/{user_id}")
def check_user_limits(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Verificar se um usuário pode fazer novas requisições
    """
    try:
        should_block, reason = alert_service.should_block_request(user_id, db)
        
        return {
            "user_id": user_id,
            "blocked": should_block,
            "reason": reason,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar limites do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/alerts/critical")
def get_critical_alerts(
    db: Session = Depends(get_db)
):
    """
    Obter apenas alertas críticos de todos os usuários
    """
    try:
        all_alerts = alert_service.check_all_users_limits(db)
        critical_alerts = {}
        
        for user_id, alerts in all_alerts.items():
            critical = [a for a in alerts if a["severity"] == "critical"]
            if critical:
                critical_alerts[user_id] = critical
        
        return critical_alerts
        
    except Exception as e:
        logger.error(f"Erro ao obter alertas críticos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/cost/analysis")
async def get_cost_analysis(
    user_id: Optional[int] = Query(None, description="ID do usuário (opcional)"),
    start_date: Optional[datetime] = Query(None, description="Data de início (opcional)"),
    end_date: Optional[datetime] = Query(None, description="Data de fim (opcional)"),
    db: Session = Depends(get_db)
):
    """Retorna análise detalhada de custos"""
    try:
        query = db.query(AITransaction)
        
        # Aplicar filtros
        if user_id:
            query = query.filter(AITransaction.user_id == user_id)
        if start_date:
            query = query.filter(AITransaction.created_at >= start_date)
        if end_date:
            query = query.filter(AITransaction.created_at <= end_date)
        
        transactions = query.all()
        
        # Calcular custos por provedor
        cost_by_provider = {}
        cost_by_model = {}
        total_cost = 0.0
        
        for tx in transactions:
            if tx.total_cost:
                # Por provedor
                provider = tx.provider
                cost_by_provider[provider] = cost_by_provider.get(provider, 0.0) + tx.total_cost
                
                # Por modelo
                model = tx.model
                cost_by_model[model] = cost_by_model.get(model, 0.0) + tx.total_cost
                
                total_cost += tx.total_cost
        
        # Calcular breakdown mensal (últimos 6 meses)
        monthly_breakdown = []
        for i in range(6):
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30*i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            month_transactions = [tx for tx in transactions 
                                if month_start <= tx.created_at <= month_end]
            
            month_cost = sum(tx.total_cost or 0.0 for tx in month_transactions)
            monthly_breakdown.append({
                "month": month_start.strftime("%Y-%m"),
                "cost": round(month_cost, 4),
                "transactions": len(month_transactions)
            })
        
        return {
            "user_id": user_id,
            "total_cost": round(total_cost, 4),
            "cost_by_provider": {k: round(v, 4) for k, v in cost_by_provider.items()},
            "cost_by_model": {k: round(v, 4) for k, v in cost_by_model.items()},
            "monthly_breakdown": monthly_breakdown,
            "total_transactions": len(transactions)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter análise de custos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")