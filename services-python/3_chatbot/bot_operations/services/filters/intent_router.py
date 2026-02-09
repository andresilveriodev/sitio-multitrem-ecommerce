"""
Roteador de Intents - Roteia mensagens baseado em intents classificados
"""

from typing import Dict, Optional, Any
from .intent_classifier import Intent, intent_classifier
import structlog

logger = structlog.get_logger(__name__)


class IntentRouter:
    """Roteia mensagens baseado em intents"""
    
    def __init__(self):
        self.intent_handlers = {
            Intent.CATALOG: self._handle_catalog,
            Intent.ORDER_CREATE: self._handle_order_create,
            Intent.ORDER_UPDATE: self._handle_order_update,
            Intent.ORDER_STATUS: self._handle_order_status,
            Intent.DELIVERY: self._handle_delivery,
            Intent.PAYMENT: self._handle_payment,
            Intent.ACCOUNT: self._handle_account,
            Intent.COMPLAINT: self._handle_complaint,
            Intent.SUPPORT: self._handle_support,
            Intent.OFFTOPIC: self._handle_offtopic,
            Intent.DANGEROUS: self._handle_blocked,
            Intent.ABUSE: self._handle_blocked,
            Intent.UNKNOWN: self._handle_unknown,
        }
    
    async def route(self, intent: Intent, message: str, metadata: Dict[str, Any], 
                   user_id: str) -> Dict[str, Any]:
        """
        Roteia mensagem baseado no intent
        
        Returns:
            Dict com decision (ALLOW_AI, NO_AI_TEMPLATE, BLOCK, ASK_CLARIFY)
            e response se aplicável
        """
        handler = self.intent_handlers.get(intent)
        if handler:
            return await handler(message, metadata, user_id)
        
        # Fallback
        return {
            "decision": "ALLOW_AI",
            "requires_ai": True,
            "response": None
        }
    
    async def _handle_catalog(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle CATALOG intent"""
        # Se foi detectado por regra forte, responde com template (SEM IA)
        if metadata.get("method") == "strong_rule":
            return {
                "decision": "NO_AI_TEMPLATE",
                "requires_ai": False,
                "intent": "CATALOG",
                "response": "📋 Aqui está nosso cardápio de produtos frescos do Sítio Multitrem!\n\n🌱 *Verduras e Hortaliças:*\n- Alface\n- Rúcula\n- Coentro\n- Cebolinha\n- Cheiro-verde\n- Couve\n- Espinafre\n\n🥚 *Ovos:*\n- Cartela de ovos (dúzia)\n\nDigite *pedido* para fazer um pedido ou *preço* para ver valores."
            }
        
        # Se score alto, pode chamar IA para respostas mais detalhadas
        return {
            "decision": "ALLOW_AI",
            "requires_ai": True,
            "intent": "CATALOG",
            "response": None
        }
    
    async def _handle_order_create(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle ORDER_CREATE intent"""
        # Tenta extrair pedido por regras primeiro
        # Se não conseguir, chama IA
        should_call_ai = intent_classifier.should_call_ai(
            Intent.ORDER_CREATE, 
            metadata.get("score", 0),
            message
        )
        
        if not should_call_ai:
            # Pode extrair por regras - não precisa IA
            return {
                "decision": "NO_AI_TEMPLATE",
                "requires_ai": False,
                "intent": "ORDER_CREATE",
                "response": "Pedido identificado! Processando...",
                "can_extract_order": True
            }
        
        return {
            "decision": "ALLOW_AI",
            "requires_ai": True,
            "intent": "ORDER_CREATE",
            "response": None
        }
    
    async def _handle_order_update(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle ORDER_UPDATE intent"""
        should_call_ai = intent_classifier.should_call_ai(
            Intent.ORDER_UPDATE,
            metadata.get("score", 0),
            message
        )
        
        if not should_call_ai:
            return {
                "decision": "NO_AI_TEMPLATE",
                "requires_ai": False,
                "intent": "ORDER_UPDATE",
                "response": "Alteração identificada! Processando...",
                "can_extract_order": True
            }
        
        return {
            "decision": "ALLOW_AI",
            "requires_ai": True,
            "intent": "ORDER_UPDATE",
            "response": None
        }
    
    async def _handle_order_status(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle ORDER_STATUS intent"""
        # Se foi detectado por regra forte, responde com template (SEM IA)
        if metadata.get("method") == "strong_rule":
            return {
                "decision": "NO_AI_TEMPLATE",
                "requires_ai": False,
                "intent": "ORDER_STATUS",
                "response": "📦 Para verificar o status do seu pedido, preciso do número do pedido.\n\nDigite *meus pedidos* para ver sua lista de pedidos ou informe o número do pedido."
            }
        
        return {
            "decision": "ALLOW_AI",
            "requires_ai": True,
            "intent": "ORDER_STATUS",
            "response": None
        }
    
    async def _handle_delivery(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle DELIVERY intent"""
        return {
            "decision": "ALLOW_AI",
            "requires_ai": True,
            "intent": "DELIVERY",
            "response": None
        }
    
    async def _handle_payment(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle PAYMENT intent"""
        # Se foi detectado por regra forte, responde com template (SEM IA)
        method = metadata.get("method", "")
        logger.info(f"PAYMENT handler - method: {method}, metadata keys: {list(metadata.keys())}")
        
        if method == "strong_rule":
            logger.info("PAYMENT: Usando template (regra forte detectada)")
            return {
                "decision": "NO_AI_TEMPLATE",
                "requires_ai": False,
                "intent": "PAYMENT",
                "response": "💰 *Formas de Pagamento:*\n\n💳 *PIX* - Pagamento instantâneo\n📄 *Boleto* - Pagamento em até 3 dias\n💳 *Cartão* - Crédito ou débito\n\nPara gerar o PIX ou boleto, digite *gerar pagamento* após finalizar seu pedido."
            }
        
        logger.info("PAYMENT: Chamando IA (não foi regra forte)")
        return {
            "decision": "ALLOW_AI",
            "requires_ai": True,
            "intent": "PAYMENT",
            "response": None
        }
    
    async def _handle_account(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle ACCOUNT intent"""
        return {
            "decision": "ALLOW_AI",
            "requires_ai": True,
            "intent": "ACCOUNT",
            "response": None
        }
    
    async def _handle_complaint(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle COMPLAINT intent"""
        # Reclamações complexas podem precisar de IA
        should_call_ai = intent_classifier.should_call_ai(
            Intent.COMPLAINT,
            metadata.get("score", 0),
            message
        )
        
        return {
            "decision": "ALLOW_AI" if should_call_ai else "NO_AI_TEMPLATE",
            "requires_ai": should_call_ai,
            "intent": "COMPLAINT",
            "response": None if should_call_ai else "Reclamação registrada. Nossa equipe entrará em contato."
        }
    
    async def _handle_support(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle SUPPORT intent"""
        return {
            "decision": "NO_AI_TEMPLATE",
            "requires_ai": False,
            "intent": "SUPPORT",
            "response": "Para ajuda, digite:\n*cardapio* - Ver produtos\n*pedido* - Fazer pedido\n*ajuda* - Mais informações"
        }
    
    async def _handle_offtopic(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle OFFTOPIC intent - NUNCA chama IA"""
        escape_response = intent_classifier.get_escape_response(Intent.OFFTOPIC)
        return {
            "decision": "NO_AI_TEMPLATE",
            "requires_ai": False,
            "intent": "OFFTOPIC",
            "response": escape_response,
            "blocked": False  # Não bloqueia, apenas redireciona
        }
    
    async def _handle_blocked(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle DANGEROUS/ABUSE intent - BLOQUEIA"""
        escape_response = intent_classifier.get_escape_response(Intent.DANGEROUS)
        return {
            "decision": "BLOCK",
            "requires_ai": False,
            "intent": metadata.get("intent", "DANGEROUS"),
            "response": escape_response,
            "blocked": True
        }
    
    async def _handle_unknown(self, message: str, metadata: Dict, user_id: str) -> Dict:
        """Handle UNKNOWN intent - Pergunta de esclarecimento"""
        escape_response = intent_classifier.get_escape_response(Intent.UNKNOWN)
        return {
            "decision": "ASK_CLARIFY",
            "requires_ai": False,
            "intent": "UNKNOWN",
            "response": escape_response
        }


# Instância global do roteador
intent_router = IntentRouter()
