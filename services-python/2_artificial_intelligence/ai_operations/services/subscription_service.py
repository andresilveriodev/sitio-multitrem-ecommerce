from sqlalchemy.orm import Session
from models.ai_subscription import AISubscription, BillingCycle
from models.user_subscription import UserSubscription, SubscriptionStatus
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Serviço para gerenciar subscrições de IA"""
    
    @staticmethod
    def get_all_plans(db: Session, active_only: bool = True) -> List[AISubscription]:
        """Busca todos os planos de assinatura"""
        query = db.query(AISubscription)
        if active_only:
            query = query.filter(AISubscription.is_active == True)
        return query.order_by(AISubscription.price).all()
    
    @staticmethod
    def get_plan_by_id(db: Session, plan_id: str) -> Optional[AISubscription]:
        """Busca plano por ID"""
        return db.query(AISubscription).filter(AISubscription.plan_id == plan_id).first()
    
    @staticmethod
    def get_user_subscription(db: Session, user_id: str) -> Optional[UserSubscription]:
        """Busca assinatura ativa do usuário (aceita UUID como string)"""
        return db.query(UserSubscription).filter(
            UserSubscription.user_id == user_id,
            UserSubscription.status == SubscriptionStatus.ACTIVE
        ).first()
    
    @staticmethod
    def subscribe_user(db: Session, user_id: str, username: str, plan_id: str) -> Optional[UserSubscription]:
        """Assina um usuário a um plano"""
        # Verifica se o plano existe
        plan = SubscriptionService.get_plan_by_id(db, plan_id)
        if not plan:
            return None
        
        # Cancela assinatura anterior se existir
        current_subscription = SubscriptionService.get_user_subscription(db, user_id)
        if current_subscription:
            current_subscription.status = SubscriptionStatus.CANCELLED
            db.commit()
        
        # Cria nova assinatura
        now = datetime.utcnow()
        if plan.billing_cycle == BillingCycle.MONTHLY:
            period_end = now + timedelta(days=30)
        else:  # YEARLY
            period_end = now + timedelta(days=365)
        
        subscription = UserSubscription(
            user_id=user_id,
            subscription_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=period_end,
            usage_limits=plan.limits,
            current_usage={
                'requests_used': 0,
                'tokens_used': 0,
                'cost_spent': 0.0
            }
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription
    
    @staticmethod
    def cancel_subscription(db: Session, user_id: str) -> bool:
        """Cancela a assinatura do usuário"""
        subscription = SubscriptionService.get_user_subscription(db, user_id)
        if not subscription:
            return False
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancel_at_period_end = True
        db.commit()
        return True
    
    @staticmethod
    def update_usage(db: Session, user_id: str, tokens_used: int, cost: float) -> bool:
        """Atualiza o uso da assinatura do usuário"""
        subscription = SubscriptionService.get_user_subscription(db, user_id)
        if not subscription:
            return False
        
        if subscription.current_usage is None:
            subscription.current_usage = {
                'requests_used': 0,
                'tokens_used': 0,
                'cost_spent': 0.0
            }
        
        subscription.current_usage['requests_used'] += 1
        subscription.current_usage['tokens_used'] += tokens_used
        subscription.current_usage['cost_spent'] += cost
        
        db.commit()
        return True
    
    @staticmethod
    def check_usage_limits(db: Session, user_id: str) -> Dict[str, Any]:
        """Verifica os limites de uso do usuário"""
        subscription = SubscriptionService.get_user_subscription(db, user_id)
        if not subscription:
            # Usuário sem assinatura - usar limites do plano gratuito
            free_plan = SubscriptionService.get_plan_by_id(db, 'free')
            if free_plan:
                limits = free_plan.limits or {}
                current_usage = {'requests_used': 0, 'tokens_used': 0, 'cost_spent': 0.0}
            else:
                return {'can_use': False, 'reason': 'No subscription plan found'}
        else:
            limits = subscription.usage_limits or {}
            current_usage = subscription.current_usage or {'requests_used': 0, 'tokens_used': 0, 'cost_spent': 0.0}
        
        # Verifica limites
        max_requests = limits.get('maxRequestsPerMonth', 0)
        max_tokens = limits.get('maxTokensPerMonth', 0)
        max_cost = limits.get('maxCostPerMonth', 0)
        
        can_use = True
        reason = None
        
        if max_requests > 0 and current_usage['requests_used'] >= max_requests:
            can_use = False
            reason = 'Monthly request limit exceeded'
        elif max_tokens > 0 and current_usage['tokens_used'] >= max_tokens:
            can_use = False
            reason = 'Monthly token limit exceeded'
        elif max_cost > 0 and current_usage['cost_spent'] >= max_cost:
            can_use = False
            reason = 'Monthly cost limit exceeded'
        
        return {
            'can_use': can_use,
            'reason': reason,
            'limits': limits,
            'current_usage': current_usage
        }

# Instância global do serviço
subscription_service = SubscriptionService()
