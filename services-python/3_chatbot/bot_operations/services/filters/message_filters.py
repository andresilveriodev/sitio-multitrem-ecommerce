"""
Filtros de mensagens para otimização de custos
"""

import re
from typing import Dict, Optional, Tuple
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class MessageFilters:
    """Filtros para mensagens do usuário"""
    
    def __init__(self):
        # Respostas automáticas para perguntas frequentes
        self.auto_responses = {
            # Saudações
            r"\b(oi|olá|ola|hey|hi|hello)\b": {
                "response": "Olá! Como posso ajudá-lo hoje?",
                "confidence": 0.95,
                "category": "greeting"
            },
            
            # Saudações alternativas
            r"\b(tudo bem|tudo bom|td bem|td bom|tudo certo)\b\??": {
                "response": "Tudo bem, sim! Como posso ajudá-lo hoje?",
                "confidence": 0.95,
                "category": "greeting"
            },
            
            # Perguntas sobre o sistema
            r"\b(como você está|como vc está|como vai)\b": {
                "response": "Estou funcionando perfeitamente! Pronto para ajudá-lo com suas dúvidas sobre investimentos e trading.",
                "confidence": 0.90,
                "category": "system_status"
            },
            
            r"\b(qual é o seu nome|como você se chama|quem é você)\b": {
                "response": "Sou o assistente de IA do B3-Trader, especializado em ajudar com investimentos, análise de ações e estratégias de trading.",
                "confidence": 0.95,
                "category": "identity"
            },
            
            # Perguntas sobre funcionalidades
            r"\b(que horas são|que horas|horário)\b": {
                "response": f"Agora são {datetime.now().strftime('%H:%M')}.",
                "confidence": 0.98,
                "category": "time"
            },
            
            r"\b(obrigado|obrigada|valeu|thanks|thank you)\b": {
                "response": "Por nada! Estou aqui para ajudar. Se precisar de mais alguma coisa, é só perguntar!",
                "confidence": 0.95,
                "category": "gratitude"
            },
            
            r"\b(tchau|adeus|até logo|bye|goodbye)\b": {
                "response": "Até logo! Tenha um ótimo dia de trading!",
                "confidence": 0.95,
                "category": "farewell"
            },
            
            r"\b(você pode me ajudar|pode me ajudar|ajuda)\b": {
                "response": "Claro! Posso ajudá-lo com análise de ações, estratégias de trading, informações sobre empresas, indicadores técnicos e muito mais. O que você gostaria de saber?",
                "confidence": 0.90,
                "category": "help_request"
            },
            
            # Perguntas sobre o sistema
            r"\b(como funciona|como usar|funcionalidades)\b": {
                "response": "Posso ajudá-lo com análise de ações, informações sobre empresas, estratégias de trading, indicadores técnicos e fundamentais. Basta me fazer perguntas específicas sobre o que você quer saber!",
                "confidence": 0.85,
                "category": "system_info"
            }
        }
        
        # Palavras-chave que indicam necessidade de IA
        self.ai_keywords = [
            "análise", "ação", "ações", "bolsa", "investir", "compra", "venda",
            "preço", "indicador", "gráfico", "tendência", "suporte", "resistência",
            "empresa", "lucro", "receita", "dividendo", "balanço", "relatório",
            "estratégia", "portfolio", "risco", "retorno", "mercado", "cotações",
            "ibovespa", "petrobras", "vale", "itub", "bbas3", "petr4", "vale3"
        ]
        
        # Padrões de spam
        self.spam_patterns = [
            r"\b(compre agora|oferta limitada|ganhe dinheiro|riqueza rápida)\b",
            r"\b(bitcoin|criptomoeda|mineração)\b.*\b(ganhe|lucro|dinheiro)\b",
            r"\b(www\.|http://|https://)\b",
            r"\b\d{10,}\b",  # Muitos números
            r"\b[A-Z]{10,}\b",  # Muitas letras maiúsculas
        ]
    
    def should_auto_respond(self, message: str) -> Tuple[bool, Optional[Dict]]:
        """Verifica se deve responder automaticamente"""
        message_lower = message.lower().strip()
        
        # Verifica padrões de resposta automática
        for pattern, response_data in self.auto_responses.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.info(f"Resposta automática aplicada: {response_data['category']}")
                return True, response_data
        
        return False, None
    
    def is_spam(self, message: str) -> bool:
        """Verifica se a mensagem é spam"""
        message_lower = message.lower()
        
        for pattern in self.spam_patterns:
            if re.search(pattern, message_lower):
                logger.warning(f"Mensagem detectada como spam: {message[:50]}...")
                return True
        
        return False
    
    def requires_ai(self, message: str) -> bool:
        """Verifica se a mensagem requer IA"""
        message_lower = message.lower()
        
        # Se tem palavras-chave de IA, provavelmente precisa de IA
        for keyword in self.ai_keywords:
            if keyword in message_lower:
                return True
        
        # Se é uma pergunta complexa
        if self._is_complex_question(message):
            return True
        
        return False
    
    def _is_complex_question(self, message: str) -> bool:
        """Verifica se é uma pergunta complexa"""
        # Perguntas que começam com palavras interrogativas
        question_words = ["como", "quando", "onde", "por que", "porque", "qual", "quais", "quem"]
        message_lower = message.lower()
        
        for word in question_words:
            if message_lower.startswith(word) and len(message) > 20:
                return True
        
        # Perguntas com múltiplas frases
        if message.count("?") > 1 or len(message.split()) > 10:
            return True
        
        return False
    
    def classify_urgency(self, message: str) -> str:
        """Classifica urgência da mensagem"""
        message_lower = message.lower()
        
        # Alta urgência - palavras relacionadas a perdas ou problemas
        high_urgency = ["perdendo", "perda", "prejuízo", "queda", "crash", "emergência", "urgente"]
        for word in high_urgency:
            if word in message_lower:
                return "high"
        
        # Média urgência - perguntas sobre investimentos ativos
        medium_urgency = ["ação", "ações", "investimento", "portfolio", "carteira", "análise"]
        for word in medium_urgency:
            if word in message_lower:
                return "medium"
        
        return "low"
    
    def extract_context_keywords(self, message: str) -> list:
        """Extrai palavras-chave para contexto"""
        message_lower = message.lower()
        keywords = []
        
        for keyword in self.ai_keywords:
            if keyword in message_lower:
                keywords.append(keyword)
        
        return keywords
    
    def validate_message(self, message: str) -> Dict:
        """Valida mensagem e retorna análise completa"""
        if not message or not message.strip():
            return {
                "valid": False,
                "reason": "Mensagem vazia",
                "requires_ai": False,
                "urgency": "low"
            }
        
        if len(message) > 1000:
            return {
                "valid": False,
                "reason": "Mensagem muito longa",
                "requires_ai": False,
                "urgency": "low"
            }
        
        if self.is_spam(message):
            return {
                "valid": False,
                "reason": "Mensagem detectada como spam",
                "requires_ai": False,
                "urgency": "low"
            }
        
        auto_respond, auto_response = self.should_auto_respond(message)
        
        return {
            "valid": True,
            "auto_respond": auto_respond,
            "auto_response": auto_response,
            "requires_ai": self.requires_ai(message),
            "urgency": self.classify_urgency(message),
            "keywords": self.extract_context_keywords(message),
            "length": len(message)
        }


# Instância global dos filtros
message_filters = MessageFilters()


