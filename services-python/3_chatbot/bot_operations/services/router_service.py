"""
Router Service - Classificação barata de intents
Decide se mensagem vai para Tools (determinístico) ou AI Service (conversa/ambíguo)
"""

import re
from typing import Dict, Optional, Any, Tuple
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class RouteType(str, Enum):
    """Tipo de rota"""
    TOOLS = "TOOLS"  # Funções determinísticas do sistema
    AI = "AI"  # Conversa natural ou parsing complexo


class IntentType(str, Enum):
    """Intents do business da horta"""
    PEDIDOS = "pedidos"
    CRIAR_PEDIDO = "criar_pedido"  # Registrar/novo pedido → IA extrai dados
    ESTOQUE = "estoque"
    FINANCEIRO = "financeiro"
    CADASTRO = "cadastro"
    MENU = "menu"
    HOJE = "hoje"
    CLIENTE = "cliente"
    PRODUTO = "produto"
    CONVERSA = "conversa"  # Conversa natural
    CUMPRIMENTO = "cumprimento"  # Oi, olá, etc
    DUVIDA = "duvida"  # Quando não tem certeza
    UNKNOWN = "unknown"


class RouterService:
    """Router que classifica mensagens com custo baixo"""
    
    def __init__(self):
        # Padrões de comandos (regras duras - zero erro)
        self.command_patterns = {
            IntentType.MENU: [r"^/menu", r"menu", r"início", r"inicio"],
            IntentType.PEDIDOS: [r"^/pedidos", r"pedidos", r"pedido", r"encomenda"],
            IntentType.ESTOQUE: [r"^/estoque", r"estoque", r"inventário", r"inventario"],
            IntentType.FINANCEIRO: [r"^/financeiro", r"financeiro", r"financeiro", r"dinheiro"],
            IntentType.HOJE: [r"^/hoje", r"hoje", r"resumo do dia", r"resumo hoje"],
            IntentType.CLIENTE: [r"^/cliente", r"cliente", r"cadastro cliente"],
            IntentType.PRODUTO: [r"^/produto", r"produto", r"cadastrar produto"],
        }
        
        # Palavras-chave para intents (heurística leve)
        self.keyword_patterns = {
            IntentType.PEDIDOS: [
                r"\bpedido\w*\b", r"\bencomenda\w*\b", r"\bvenda\w*\b",
                r"\bcomprar\b", r"\bcompras\b", r"\bentrega\w*\b"
            ],
            IntentType.ESTOQUE: [
                r"\bestoque\w*\b", r"\binventário\b", r"\binventario\b",
                r"\bquantidade\b", r"\bdisponível\b", r"\bdisponivel\b",
                r"\btem\s+\w+\s+em\s+estoque\b"
            ],
            IntentType.FINANCEIRO: [
                r"\bfinanceiro\w*\b", r"\bdinheiro\b", r"\bvalor\b",
                r"\bpreço\b", r"\bpreco\b", r"\bfaturamento\b",
                r"\breceita\b", r"\bdespesa\w*\b"
            ],
            IntentType.CLIENTE: [
                r"\bcliente\w*\b", r"\bcadastro\w*\s+cliente\b",
                r"\bbuscar\s+cliente\b", r"\bprocurar\s+cliente\b"
            ],
            IntentType.PRODUTO: [
                r"\bcadastrar\s+produto\b", r"\bnovo\s+produto\b",
                r"\beditar\s+produto\b", r"\bdeletar\s+produto\b"
            ],
        }
        
        # Padrões de cumprimento (sempre vai para AI para naturalidade)
        self.greeting_patterns = [
            r"^(oi|olá|ola|hey|hi|hello)\s*!?\s*$",
            r"^(tudo\s+bem|tudo\s+bom|td\s+bem|td\s+bom)\s*\??\s*$",
            r"^(bom\s+dia|boa\s+tarde|boa\s+noite)\s*!?\s*$",
            r"^(e\s+aí|e\s+ai|eae|fala)\s*!?\s*$",
        ]
        
        # Padrões de conversa natural
        self.conversation_patterns = [
            r"\b(quero|preciso|gostaria|pode|poderia)\s+",
            r"\b(como|quando|onde|por que|porque)\s+",
            r"\b(obrigado|obrigada|valeu|thanks)\s*",
            r"\b(tchau|até|ate|bye)\s*",
        ]
    
    def route(
        self,
        message: str,
        user_id: str,
        user_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Roteia mensagem para Tools ou AI Service
        
        Returns:
            {
                "route": RouteType,
                "intent": IntentType,
                "confidence": float (0.0-1.0),
                "reason": str,
                "context_keys": List[str],
                "should_ask_ai_for_intent": bool  # Se deve perguntar ao AI para classificar
            }
        """
        message_lower = message.lower().strip()
        
        # 1. Verificar estado ativo (fluxo de formulário)
        if user_state and user_state.get("active_flow"):
            flow_name = user_state.get("active_flow")
            logger.info(
                "Roteando para fluxo ativo",
                user_id=user_id,
                flow=flow_name,
                message_preview=message[:50]
            )
            return {
                "route": RouteType.TOOLS,
                "intent": IntentType.UNKNOWN,
                "confidence": 1.0,
                "reason": f"active_flow:{flow_name}",
                "context_keys": ["active_flow", "flow_data"],
                "should_ask_ai_for_intent": False
            }
        
        # 2. Verificar intenção óbvia de CRIAR/REGISTRAR pedido ANTES de comandos (evita que "pedido" em "registrar o pedido" vire listar)
        if self._is_create_order_intent(message_lower):
            logger.info(
                "Roteando intenção criar pedido para AI (extract_order)",
                user_id=user_id,
                message_preview=message[:50]
            )
            return {
                "route": RouteType.AI,
                "intent": IntentType.CRIAR_PEDIDO,
                "confidence": 0.92,
                "reason": "create_order_intent",
                "context_keys": ["order_extraction"],
                "should_ask_ai_for_intent": False
            }
        
        # 3. Verificar comandos explícitos (regras duras)
        command_result = self._check_commands(message_lower)
        if command_result:
            return {
                "route": RouteType.TOOLS,
                "intent": command_result["intent"],
                "confidence": 1.0,
                "reason": f"command:{command_result['match']}",
                "context_keys": [],
                "should_ask_ai_for_intent": False
            }
        
        # 4. Verificar cumprimentos (sempre AI para naturalidade)
        if self._is_greeting(message_lower):
            logger.info(
                "Roteando cumprimento para AI",
                user_id=user_id,
                message=message
            )
            return {
                "route": RouteType.AI,
                "intent": IntentType.CUMPRIMENTO,
                "confidence": 0.95,
                "reason": "greeting",
                "context_keys": [],
                "should_ask_ai_for_intent": False
            }
        
        # 5. Verificar padrões de pedido (texto livre como "Dona Dilma: 08 Couve")
        if self._is_order_text(message_lower):
            logger.info(
                "Roteando texto de pedido para AI (parsing)",
                user_id=user_id,
                message_preview=message[:50]
            )
            return {
                "route": RouteType.AI,
                "intent": IntentType.PEDIDOS,
                "confidence": 0.90,
                "reason": "order_text_pattern",
                "context_keys": ["order_parsing"],
                "should_ask_ai_for_intent": False
            }
        
        # 6. Verificar palavras-chave (heurística leve)
        keyword_result = self._check_keywords(message_lower)
        if keyword_result and keyword_result["confidence"] >= 0.75:
            return {
                "route": RouteType.TOOLS,
                "intent": keyword_result["intent"],
                "confidence": keyword_result["confidence"],
                "reason": f"keyword:{keyword_result['match']}",
                "context_keys": [],
                "should_ask_ai_for_intent": False
            }
        
        # 7. Verificar se é conversa natural
        if self._is_conversation(message_lower):
            logger.info(
                "Roteando conversa natural para AI",
                user_id=user_id,
                message_preview=message[:50]
            )
            return {
                "route": RouteType.AI,
                "intent": IntentType.CONVERSA,
                "confidence": 0.80,
                "reason": "conversation_pattern",
                "context_keys": [],
                "should_ask_ai_for_intent": False
            }
        
        # 8. Fallback: dúvida - perguntar ao AI Service para classificar
        logger.info(
            "Intent não clara, perguntando ao AI Service",
            user_id=user_id,
            message_preview=message[:50]
        )
        return {
            "route": RouteType.AI,
            "intent": IntentType.DUVIDA,
            "confidence": 0.50,
            "reason": "unclear_intent",
            "context_keys": [],
            "should_ask_ai_for_intent": True  # Flag para perguntar ao AI
        }
    
    def _check_commands(self, message_lower: str) -> Optional[Dict[str, Any]]:
        """Verifica comandos explícitos (regras duras)"""
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return {
                        "intent": intent,
                        "match": pattern
                    }
        return None
    
    def _check_keywords(self, message_lower: str) -> Optional[Dict[str, Any]]:
        """Verifica palavras-chave (heurística leve)"""
        best_match = None
        best_confidence = 0.0
        
        for intent, patterns in self.keyword_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    matches += 1
            
            if matches > 0:
                # Confidence baseado em quantos padrões bateram
                confidence = min(0.5 + (matches * 0.15), 0.95)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = {
                        "intent": intent,
                        "confidence": confidence,
                        "match": f"{matches} patterns"
                    }
        
        return best_match
    
    def _is_greeting(self, message_lower: str) -> bool:
        """Verifica se é cumprimento"""
        for pattern in self.greeting_patterns:
            if re.match(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_conversation(self, message_lower: str) -> bool:
        """Verifica se é conversa natural"""
        for pattern in self.conversation_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_create_order_intent(self, message_lower: str) -> bool:
        """
        Detecta intenção óbvia de criar/registrar pedido (nível 1).
        "Registrar" = criar; deve ter prioridade sobre listar/consultar pedidos.
        """
        patterns = [
            r"\bquero\s+registr",  # registrar, registra, registro
            r"\bregistrar\s+(o\s+)?pedido\b",
            r"\bregistra\s+(o\s+)?pedido\b",
            r"\bregistro\s+(do\s+)?pedido\b",
            r"\bnovo\s+pedido\b",
            r"\bcriar\s+pedido\b",
            r"\bpedido\s+do\s+\w+",  # "pedido do Adriano"
            r"\bpedido\s+da\s+\w+",
            r"\badiciona?\s+item\b",
            r"\badicionar\s+item\b",
            r"\bfazer\s+pedido\b",
            r"\blançar\s+pedido\b",
            r"\blancar\s+pedido\b",
            r"\banotar\s+pedido\b",
        ]
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    def _is_order_text(self, message_lower: str) -> bool:
        """
        Detecta padrão de texto de pedido
        Ex: "Dona Dilma: 08 Couve 04 Coentros"
        """
        # Padrão: nome seguido de dois pontos e números/produtos
        order_pattern = r"^[a-záàâãéêíóôõúç\s]+:\s*\d+\s+[a-záàâãéêíóôõúç\s]+"
        if re.search(order_pattern, message_lower, re.IGNORECASE):
            return True
        
        # Padrão alternativo: números seguidos de nomes de produtos
        product_number_pattern = r"\d{2,}\s+[a-záàâãéêíóôõúç\s]{3,}"
        matches = len(re.findall(product_number_pattern, message_lower))
        if matches >= 2:  # Pelo menos 2 produtos
            return True
        
        return False


# Instância global
router_service = RouterService()
