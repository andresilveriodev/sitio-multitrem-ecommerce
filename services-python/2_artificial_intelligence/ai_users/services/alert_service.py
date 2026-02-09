from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db import get_db
from models.transaction import AITransaction
from models.usage import Usage
from sqlalchemy import func, and_
import logging

logger = logging.getLogger(__name__)

class AlertType:
    """Tipos de alertas disponíveis"""
    TOKEN_LIMIT = "token_limit"
    COST_LIMIT = "cost_limit"
    DAILY_USAGE = "daily_usage"
    MONTHLY_USAGE = "monthly_usage"
    ERROR_RATE = "error_rate"

class AlertSeverity:
    """Níveis de severidade dos alertas"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertService:
    """Serviço para gerenciamento de alertas e limites de uso"""
    
    def __init__(self):
        self.default_limits = {
            "daily_tokens": 100000,
            "monthly_tokens": 2000000,
            "daily_cost": 50.0,
            "monthly_cost": 1000.0,
            "error_rate_threshold": 0.1  # 10%
        }
    
    def check_user_limits(self, user_id: int, db: Session) -> List[Dict]:
        """Verifica todos os limites para um usuário específico"""
        alerts = []
        
        # Verificar limites diários
        daily_alerts = self._check_daily_limits(user_id, db)
        alerts.extend(daily_alerts)
        
        # Verificar limites mensais
        monthly_alerts = self._check_monthly_limits(user_id, db)
        alerts.extend(monthly_alerts)
        
        # Verificar taxa de erro
        error_alerts = self._check_error_rate(user_id, db)
        alerts.extend(error_alerts)
        
        return alerts
    
    def _check_daily_limits(self, user_id: int, db: Session) -> List[Dict]:
        """Verifica limites diários de tokens e custos"""
        alerts = []
        today = datetime.now().date()
        
        # Buscar uso diário
        daily_usage = db.query(
            func.sum(AITransaction.total_tokens).label('total_tokens'),
            func.sum(AITransaction.total_cost).label('total_cost')
        ).filter(
            and_(
                AITransaction.user_id == user_id,
                func.date(AITransaction.created_at) == today,
                AITransaction.status == 'completed'
            )
        ).first()
        
        if daily_usage:
            tokens_used = daily_usage.total_tokens or 0
            cost_spent = daily_usage.total_cost or 0.0
            
            # Verificar limite de tokens diários
            token_limit = self.default_limits["daily_tokens"]
            if tokens_used >= token_limit * 0.9:  # 90% do limite
                severity = AlertSeverity.CRITICAL if tokens_used >= token_limit else AlertSeverity.WARNING
                alerts.append({
                    "type": AlertType.TOKEN_LIMIT,
                    "severity": severity,
                    "message": f"Uso diário de tokens: {tokens_used:,}/{token_limit:,} ({(tokens_used/token_limit)*100:.1f}%)",
                    "user_id": user.id,
                    "current_value": tokens_used,
                    "limit_value": token_limit,
                    "period": "daily",
                    "timestamp": datetime.now()
                })
            
            # Verificar limite de custo diário
            cost_limit = self.default_limits["daily_cost"]
            if cost_spent >= cost_limit * 0.9:  # 90% do limite
                severity = AlertSeverity.CRITICAL if cost_spent >= cost_limit else AlertSeverity.WARNING
                alerts.append({
                    "type": AlertType.COST_LIMIT,
                    "severity": severity,
                    "message": f"Custo diário: ${cost_spent:.2f}/${cost_limit:.2f} ({(cost_spent/cost_limit)*100:.1f}%)",
                    "user_id": user.id,
                    "current_value": cost_spent,
                    "limit_value": cost_limit,
                    "period": "daily",
                    "timestamp": datetime.now()
                })
        
        return alerts
    
    def _check_monthly_limits(self, user_id: int, db: Session) -> List[Dict]:
        """Verifica limites mensais de tokens e custos"""
        alerts = []
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Buscar uso mensal
        monthly_usage = db.query(
            func.sum(Transaction.total_tokens).label('total_tokens'),
            func.sum(Transaction.total_cost).label('total_cost')
        ).filter(
            and_(
                Transaction.user_id == user.id,
                Transaction.created_at >= month_start,
                Transaction.status == 'completed'
            )
        ).first()
        
        if monthly_usage:
            tokens_used = monthly_usage.total_tokens or 0
            cost_spent = monthly_usage.total_cost or 0.0
            
            # Verificar limite de tokens mensais
            token_limit = self.default_limits["monthly_tokens"]
            if tokens_used >= token_limit * 0.8:  # 80% do limite
                severity = AlertSeverity.CRITICAL if tokens_used >= token_limit else AlertSeverity.WARNING
                alerts.append({
                    "type": AlertType.TOKEN_LIMIT,
                    "severity": severity,
                    "message": f"Uso mensal de tokens: {tokens_used:,}/{token_limit:,} ({(tokens_used/token_limit)*100:.1f}%)",
                    "user_id": user.id,
                    "current_value": tokens_used,
                    "limit_value": token_limit,
                    "period": "monthly",
                    "timestamp": datetime.now()
                })
            
            # Verificar limite de custo mensal
            cost_limit = self.default_limits["monthly_cost"]
            if cost_spent >= cost_limit * 0.8:  # 80% do limite
                severity = AlertSeverity.CRITICAL if cost_spent >= cost_limit else AlertSeverity.WARNING
                alerts.append({
                    "type": AlertType.COST_LIMIT,
                    "severity": severity,
                    "message": f"Custo mensal: ${cost_spent:.2f}/${cost_limit:.2f} ({(cost_spent/cost_limit)*100:.1f}%)",
                    "user_id": user.id,
                    "current_value": cost_spent,
                    "limit_value": cost_limit,
                    "period": "monthly",
                    "timestamp": datetime.now()
                })
        
        return alerts
    
    def _check_error_rate(self, user_id: int, db: Session) -> List[Dict]:
        """Verifica taxa de erro nas últimas 24 horas"""
        alerts = []
        yesterday = datetime.now() - timedelta(hours=24)
        
        # Contar transações totais e com erro
        total_transactions = db.query(Transaction).filter(
            and_(
                Transaction.user_id == user.id,
                Transaction.created_at >= yesterday
            )
        ).count()
        
        error_transactions = db.query(Transaction).filter(
            and_(
                Transaction.user_id == user.id,
                Transaction.created_at >= yesterday,
                Transaction.status == 'failed'
            )
        ).count()
        
        if total_transactions > 0:
            error_rate = error_transactions / total_transactions
            threshold = self.default_limits["error_rate_threshold"]
            
            if error_rate >= threshold:
                alerts.append({
                    "type": AlertType.ERROR_RATE,
                    "severity": AlertSeverity.WARNING,
                    "message": f"Taxa de erro elevada: {error_rate*100:.1f}% ({error_transactions}/{total_transactions} transações)",
                    "user_id": user.id,
                    "current_value": error_rate,
                    "limit_value": threshold,
                    "period": "24h",
                    "timestamp": datetime.now()
                })
        
        return alerts
    
    def check_all_users_limits(self, db: Session) -> Dict[int, List[Dict]]:
        """Verifica limites para todos os usuários ativos"""
        all_alerts = {}
        
        # Buscar usuários ativos (com transações nos últimos 30 dias)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        active_users = db.query(User).join(Transaction).filter(
            Transaction.created_at >= thirty_days_ago
        ).distinct().all()
        
        for user in active_users:
            user_alerts = self.check_user_limits(user.id, db)
            if user_alerts:
                all_alerts[user.id] = user_alerts
        
        return all_alerts
    
    def get_usage_summary(self, user_id: int, db: Session) -> Dict:
        """Retorna resumo de uso atual do usuário"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        now = datetime.now()
        today = now.date()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Uso diário
        daily_usage = db.query(
            func.sum(Transaction.total_tokens).label('tokens'),
            func.sum(Transaction.total_cost).label('cost'),
            func.count(Transaction.id).label('requests')
        ).filter(
            and_(
                Transaction.user_id == user_id,
                func.date(Transaction.created_at) == today,
                Transaction.status == 'completed'
            )
        ).first()
        
        # Uso mensal
        monthly_usage = db.query(
            func.sum(Transaction.total_tokens).label('tokens'),
            func.sum(Transaction.total_cost).label('cost'),
            func.count(Transaction.id).label('requests')
        ).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.created_at >= month_start,
                Transaction.status == 'completed'
            )
        ).first()
        
        return {
            "user_id": user_id,
            "daily": {
                "tokens": daily_usage.tokens or 0,
                "cost": float(daily_usage.cost or 0),
                "requests": daily_usage.requests or 0,
                "limits": {
                    "tokens": self.default_limits["daily_tokens"],
                    "cost": self.default_limits["daily_cost"]
                }
            },
            "monthly": {
                "tokens": monthly_usage.tokens or 0,
                "cost": float(monthly_usage.cost or 0),
                "requests": monthly_usage.requests or 0,
                "limits": {
                    "tokens": self.default_limits["monthly_tokens"],
                    "cost": self.default_limits["monthly_cost"]
                }
            },
            "timestamp": now
        }
    
    def should_block_request(self, user_id: int, db: Session) -> tuple[bool, str]:
        """Verifica se uma requisição deve ser bloqueada por excesso de uso"""
        alerts = self.check_user_limits(user_id, db)
        
        # Bloquear se houver alertas críticos de limite
        critical_alerts = [a for a in alerts if a["severity"] == AlertSeverity.CRITICAL]
        
        if critical_alerts:
            # Priorizar bloqueio por custo, depois por tokens
            cost_alerts = [a for a in critical_alerts if a["type"] == AlertType.COST_LIMIT]
            if cost_alerts:
                alert = cost_alerts[0]
                return True, f"Limite de custo {alert['period']} excedido: ${alert['current_value']:.2f}/${alert['limit_value']:.2f}"
            
            token_alerts = [a for a in critical_alerts if a["type"] == AlertType.TOKEN_LIMIT]
            if token_alerts:
                alert = token_alerts[0]
                return True, f"Limite de tokens {alert['period']} excedido: {alert['current_value']:,}/{alert['limit_value']:,}"
        
        return False, ""

# Instância global do serviço
alert_service = AlertService()