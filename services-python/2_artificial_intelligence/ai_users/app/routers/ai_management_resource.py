"""Endpoints para gerenciamento de IA - modelos, configurações, subscrições"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import get_db
from services.ai_models_service import ai_models_service
from services.subscription_service import subscription_service
from services.ai_settings_service import ai_settings_service
from models.ai_model import AIModel
from models.ai_subscription import AISubscription
from models.user_subscription import UserSubscription
from models.user_ai_settings import UserAISettings
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Management"])

# Modelos Pydantic para requests/responses
class AIModelResponse(BaseModel):
    id: int
    model_id: str
    name: str
    provider: str
    is_paid: bool
    cost_per_1k_tokens: float
    max_tokens_per_request: int
    is_available: bool
    description: Optional[str]
    features: Optional[Dict[str, Any]]
    rate_limits: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class AISubscriptionResponse(BaseModel):
    id: int
    plan_id: str
    name: str
    price: float
    currency: str
    billing_cycle: str
    is_active: bool
    features: Optional[Dict[str, Any]]
    limits: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class UserSubscriptionResponse(BaseModel):
    id: int
    user_id: str  # UUID como string
    subscription_id: int
    status: str
    current_period_start: Optional[str]
    current_period_end: Optional[str]
    cancel_at_period_end: bool
    usage_limits: Optional[Dict[str, Any]]
    current_usage: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class AISettingsResponse(BaseModel):
    id: int
    user_id: int
    default_model: str
    preferred_models: Optional[List[str]]
    auto_fallback: bool
    notifications: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class AISettingsUpdate(BaseModel):
    default_model: Optional[str] = None
    preferred_models: Optional[List[str]] = None
    auto_fallback: Optional[bool] = None
    notifications: Optional[Dict[str, Any]] = None

# Endpoints para Modelos de IA
@router.get("/models", response_model=List[AIModelResponse])
async def get_ai_models(
    available_only: bool = Query(True, description="Apenas modelos disponíveis"),
    provider: Optional[str] = Query(None, description="Filtrar por provedor"),
    db: Session = Depends(get_db)
):
    """Lista todos os modelos de IA disponíveis"""
    try:
        if provider:
            models = ai_models_service.get_models_by_provider(db, provider, available_only)
        else:
            models = ai_models_service.get_all_models(db, available_only)
        
        return models
    except Exception as e:
        logger.error(f"Erro ao buscar modelos de IA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}", response_model=AIModelResponse)
async def get_ai_model(model_id: str, db: Session = Depends(get_db)):
    """Obtém detalhes de um modelo específico"""
    try:
        model = ai_models_service.get_model_by_id(db, model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Modelo não encontrado")
        
        return model
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar modelo {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints para Subscrições
@router.get("/subscriptions", response_model=List[AISubscriptionResponse])
async def get_subscriptions(
    active_only: bool = Query(True, description="Apenas planos ativos"),
    db: Session = Depends(get_db)
):
    """Lista todos os planos de assinatura disponíveis"""
    try:
        plans = subscription_service.get_all_plans(db, active_only)
        return plans
    except Exception as e:
        logger.error(f"Erro ao buscar planos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscriptions/{plan_id}", response_model=AISubscriptionResponse)
async def get_subscription(plan_id: str, db: Session = Depends(get_db)):
    """Obtém detalhes de um plano específico"""
    try:
        plan = subscription_service.get_plan_by_id(db, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plano não encontrado")
        
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar plano {plan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscriptions/{plan_id}/subscribe")
async def subscribe_to_plan(
    plan_id: str,
    user_id: str = Query(..., description="ID do usuário (UUID)"),
    username: str = Query(..., description="Username do usuário"),
    db: Session = Depends(get_db)
):
    """Assina um usuário a um plano"""
    try:
        subscription = subscription_service.subscribe_user(db, user_id, username, plan_id)
        if not subscription:
            raise HTTPException(status_code=400, detail="Não foi possível assinar o plano")
        
        return {"message": "Assinatura criada com sucesso", "subscription": subscription.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao assinar plano {plan_id} para usuário {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/subscriptions/cancel")
async def cancel_subscription(
    user_id: str = Query(..., description="ID do usuário (UUID)"),
    db: Session = Depends(get_db)
):
    """Cancela a assinatura do usuário"""
    try:
        success = subscription_service.cancel_subscription(db, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Assinatura não encontrada")
        
        return {"message": "Assinatura cancelada com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao cancelar assinatura do usuário {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints para Configurações de IA
@router.get("/settings", response_model=AISettingsResponse)
async def get_ai_settings(
    user_id: int = Query(..., description="ID do usuário"),
    username: str = Query(..., description="Username do usuário"),
    db: Session = Depends(get_db)
):
    """Obtém configurações de IA do usuário"""
    try:
        settings = ai_settings_service.get_user_settings(db, user_id)
        if not settings:
            # Cria configurações padrão se não existirem
            settings = ai_settings_service.create_or_update_settings(db, user_id, username, {
                'default_model': 'ollama',
                'preferred_models': ['ollama', 'deepseek'],
                'auto_fallback': True,
                'notifications': {
                    'usage_alerts': True,
                    'cost_alerts': True,
                    'limit_alerts': True,
                    'email_notifications': False
                }
            })
        
        return settings
    except Exception as e:
        logger.error(f"Erro ao buscar configurações do usuário {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings", response_model=AISettingsResponse)
async def update_ai_settings(
    settings_update: AISettingsUpdate,
    user_id: int = Query(..., description="ID do usuário"),
    username: str = Query(..., description="Username do usuário"),
    db: Session = Depends(get_db)
):
    """Atualiza configurações de IA do usuário"""
    try:
        # Remove campos None do update
        update_data = {k: v for k, v in settings_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
        
        settings = ai_settings_service.create_or_update_settings(db, user_id, username, update_data)
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar configurações do usuário {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints para Uso e Limites
@router.get("/usage/limits")
async def get_usage_limits(
    user_id: int = Query(..., description="ID do usuário"),
    db: Session = Depends(get_db)
):
    """Obtém limites de uso do usuário"""
    try:
        limits_info = subscription_service.check_usage_limits(db, user_id)
        return limits_info
    except Exception as e:
        logger.error(f"Erro ao buscar limites do usuário {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def ai_management_health():
    """Health check para o módulo de gerenciamento de IA"""
    return {"status": "ok", "module": "ai_management"}
