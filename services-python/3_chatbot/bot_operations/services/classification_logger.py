"""
Logger de Classificação - Registra decisões do firewall para auditoria e melhoria
"""

from typing import Dict, Optional
from datetime import datetime
import structlog
import json

logger = structlog.get_logger(__name__)


class ClassificationLogger:
    """Registra logs de classificação para auditoria e treinamento"""
    
    def __init__(self):
        # Em produção, isso seria salvo no banco de dados
        # Por enquanto, apenas loga
        self.logs: list = []  # Cache em memória (pode ser movido para DB)
    
    async def log_classification(
        self,
        conversation_id: str,
        inbound_message_id: Optional[str],
        message: str,
        intent: str,
        score: int,
        rules_hit: list,
        decision: str,
        requires_ai: bool,
        user_id: Optional[str] = None
    ):
        """
        Registra classificação de mensagem
        
        Args:
            conversation_id: ID da conversa
            inbound_message_id: ID da mensagem recebida (opcional)
            message: Texto da mensagem
            intent: Intent classificado
            score: Score da classificação
            rules_hit: Lista de regras que bateram
            decision: Decisão tomada (ALLOW_AI, NO_AI_TEMPLATE, BLOCK, ASK_CLARIFY)
            requires_ai: Se chamou IA ou não
            user_id: ID do usuário (opcional)
        """
        log_entry = {
            "conversation_id": conversation_id,
            "inbound_message_id": inbound_message_id,
            "user_id": user_id,
            "message": message[:200],  # Limita tamanho
            "intent": intent,
            "score": score,
            "rules_hit": rules_hit,
            "decision": decision,
            "requires_ai": requires_ai,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Adiciona ao cache (em produção, salvaria no banco)
        self.logs.append(log_entry)
        
        # Mantém apenas últimos 1000 logs em memória
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]
        
        # Log estruturado
        logger.info(
            "Classificação registrada",
            conversation_id=conversation_id,
            intent=intent,
            score=score,
            decision=decision,
            requires_ai=requires_ai,
            rules_hit_count=len(rules_hit)
        )
    
    def get_classification_stats(self, limit: int = 100) -> Dict:
        """Retorna estatísticas de classificação"""
        if not self.logs:
            return {
                "total": 0,
                "by_intent": {},
                "by_decision": {},
                "ai_usage_rate": 0.0
            }
        
        recent_logs = self.logs[-limit:]
        
        by_intent = {}
        by_decision = {}
        ai_calls = 0
        
        for log in recent_logs:
            intent = log.get("intent", "UNKNOWN")
            decision = log.get("decision", "UNKNOWN")
            
            by_intent[intent] = by_intent.get(intent, 0) + 1
            by_decision[decision] = by_decision.get(decision, 0) + 1
            
            if log.get("requires_ai", False):
                ai_calls += 1
        
        total = len(recent_logs)
        
        return {
            "total": total,
            "by_intent": by_intent,
            "by_decision": by_decision,
            "ai_usage_rate": ai_calls / total if total > 0 else 0.0,
            "ai_calls": ai_calls,
            "no_ai_calls": total - ai_calls
        }


# Instância global do logger
classification_logger = ClassificationLogger()
