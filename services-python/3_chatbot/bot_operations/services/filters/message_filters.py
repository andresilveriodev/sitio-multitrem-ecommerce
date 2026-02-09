"""
Filtros de mensagens para otimização de custos
"""

import re
import random
from typing import Dict, Optional, Tuple
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class MessageFilters:
    """Filtros para mensagens do usuário"""
    
    def __init__(self):
        # Respostas automáticas para perguntas frequentes
        self.auto_responses = {
            # Saudações - mais amigáveis
            r"^\s*(oi|olá|ola|hey|hi|hello)\s*$": {
                "response": "Olá! 😊 Como posso ajudá-lo hoje com nossos produtos e pedidos?",
                "confidence": 0.95,
                "category": "greeting"
            },
            
            # Saudações com contexto
            r"\b(oi|olá|ola|hey|hi|hello)\b.*": {
                "response": "Olá! Como posso ajudá-lo hoje?",
                "confidence": 0.90,
                "category": "greeting"
            },
            
            # Saudações alternativas
            r"\b(tudo bem|tudo bom|td bem|td bom|tudo certo)\b\??": {
                "response": "Tudo bem, sim! 😊 Como posso ajudá-lo hoje com o e-commerce?",
                "confidence": 0.95,
                "category": "greeting"
            },
            
            # Bom dia/tarde/noite
            r"\b(bom dia|boa tarde|boa noite)\b": {
                "response": "Bom dia! 😊 Como posso ajudá-lo hoje com nossos produtos?",
                "confidence": 0.95,
                "category": "greeting"
            },
            
            # Perguntas sobre o sistema (amigáveis)
            r"\b(como você está|como vc está|como vai)\b": {
                "response": "Estou muito bem, obrigado! 😊 Pronto para ajudá-lo com suas compras no nosso e-commerce.",
                "confidence": 0.90,
                "category": "system_status"
            },
            
            r"\b(qual é o seu nome|como você se chama|quem é você)\b": {
                "response": "Olá! Sou o assistente do e-commerce, especializado em ajudar com produtos, pedidos e compras. Como posso ajudá-lo hoje?",
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
                "response": "Por nada! 😊 Estou aqui para ajudar. Se precisar de mais alguma coisa sobre nossos produtos, é só perguntar!",
                "confidence": 0.95,
                "category": "gratitude"
            },
            
            r"\b(tchau|adeus|até logo|até mais|bye|goodbye)\b": {
                "response": "Até logo! 😊 Volte sempre para conferir nossos produtos!",
                "confidence": 0.95,
                "category": "farewell"
            },
            
            r"\b(você pode me ajudar|pode me ajudar|ajuda)\b": {
                "response": "Claro! Posso ajudá-lo com produtos, pedidos, compras, entregas e dúvidas sobre nosso e-commerce. O que você gostaria de saber?",
                "confidence": 0.90,
                "category": "help_request"
            },
            
            # Perguntas sobre o sistema
            r"\b(como funciona|como usar|funcionalidades)\b": {
                "response": "Posso ajudá-lo com produtos, pedidos, compras, carrinho, entregas e dúvidas sobre nosso e-commerce. Basta me fazer perguntas sobre produtos ou pedidos!",
                "confidence": 0.85,
                "category": "system_info"
            }
        }
        
        # Palavras-chave relacionadas ao E-COMMERCE (contexto válido)
        self.ecommerce_keywords = [
            # Produtos e compras
            "produto", "produtos", "comprar", "compra", "carrinho", "cesta",
            "pedido", "pedidos", "encomenda", "entrega", "frete", "envio",
            "preço", "preços", "valor", "desconto", "promoção", "oferta",
            "categoria", "categorias", "buscar", "busca", "pesquisar", "procurar",
            "estoque", "disponível", "disponibilidade", "adicionar", "remover",
            "quantidade", "unidade", "parcelamento", "pagamento", "cartão",
            "boleto", "pix", "cupom", "código", "desconto",
            
            # Pedidos e histórico
            "meu pedido", "meus pedidos", "rastrear", "rastreamento", "status",
            "cancelar", "cancelamento", "troca", "devolução", "reembolso",
            "nota fiscal", "nf", "fatura", "recibo",
            
            # Conta e perfil
            "minha conta", "perfil", "endereço", "endereços", "telefone",
            "email", "senha", "cadastro", "dados pessoais",
            
            # Suporte e dúvidas sobre produtos
            "dúvida", "dúvidas", "ajuda", "informação", "especificação",
            "tamanho", "cor", "modelo", "marca", "garantia", "manual",
            "instrução", "como usar", "funciona"
        ]
        
        # Palavras-chave que indicam necessidade de IA (apenas para contexto de e-commerce)
        self.ai_keywords = self.ecommerce_keywords.copy()
        
        # Assuntos FORA DO CONTEXTO do e-commerce (devem receber escape)
        self.off_topic_keywords = [
            # Clima e tempo
            "clima", "tempo", "chuva", "sol", "temperatura", "previsão do tempo",
            "meteorologia", "frio", "calor", "vento", "umidade",
            
            # Notícias gerais
            "notícia", "notícias", "jornal", "jornalismo", "política", "eleição",
            "presidente", "governo", "congresso", "senado",
            
            # Entretenimento
            "filme", "filmes", "cinema", "série", "netflix", "streaming",
            "música", "músicas", "artista", "cantor", "banda", "show",
            "futebol", "time", "jogo", "jogos", "esporte", "esportes",
            
            # Educação e conhecimento geral
            "história", "geografia", "matemática", "física", "química",
            "biologia", "literatura", "livro", "livros", "estudar",
            
            # Saúde e medicina
            "medicina", "médico", "doutor", "doença", "sintoma", "tratamento",
            "remédio", "medicamento", "hospital", "clínica",
            
            # Tecnologia geral (não relacionada a produtos)
            "programação", "código", "python", "javascript", "desenvolvimento",
            "aplicativo", "app", "software", "hardware", "computador",
            
            # Conversas casuais
            "como você está", "o que você faz", "onde você mora", "qual sua idade",
            "você tem sentimentos", "você é humano", "você gosta",
            
            # Assuntos pessoais
            "família", "amigos", "relacionamento", "namoro", "casamento",
            "filhos", "filho", "filha", "pais", "mãe", "pai"
        ]
        
        # Respostas simpáticas de escape para assuntos fora do contexto
        self.off_topic_responses = [
            "Olá! Sou especializado em ajudar com produtos, pedidos e dúvidas sobre compras no nosso e-commerce. Como posso ajudá-lo com isso hoje?",
            "Oi! Estou aqui para ajudar você com produtos, compras e pedidos. Tem alguma dúvida sobre nossos produtos ou serviços?",
            "Olá! Fico feliz em ajudar, mas meu foco é em produtos, pedidos e compras. Como posso ajudá-lo com isso?",
            "Oi! Sou o assistente do e-commerce e posso ajudar com produtos, pedidos e compras. O que você gostaria de saber sobre nossos produtos?",
            "Olá! Estou aqui para ajudar com questões relacionadas ao e-commerce - produtos, pedidos, entregas e compras. Como posso ajudar?"
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
    
    def is_off_topic(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica se a mensagem está fora do contexto do e-commerce
        
        Returns:
            Tuple[bool, Optional[str]]: (é off-topic, resposta de escape)
        """
        message_lower = message.lower()
        
        # Verifica se tem palavras-chave de e-commerce primeiro
        has_ecommerce_keyword = any(keyword in message_lower for keyword in self.ecommerce_keywords)
        
        # Se tem palavra-chave de e-commerce, não é off-topic
        if has_ecommerce_keyword:
            return False, None
        
        # Verifica se tem palavras-chave de assuntos fora do contexto
        for keyword in self.off_topic_keywords:
            if keyword in message_lower:
                # Retorna resposta de escape aleatória
                escape_response = random.choice(self.off_topic_responses)
                logger.info(f"Mensagem detectada como fora do contexto: {keyword}")
                return True, escape_response
        
        # Se é uma pergunta complexa sem contexto de e-commerce, pode ser off-topic
        if self._is_complex_question(message) and not has_ecommerce_keyword:
            # Verifica se parece ser sobre e-commerce mesmo sem palavras-chave explícitas
            # Perguntas sobre "isso", "aquilo", "produto" podem ser sobre e-commerce
            if any(word in message_lower for word in ["isso", "aquilo", "produto", "item", "coisa"]):
                return False, None
            
            # Se não tem contexto claro, é off-topic
            escape_response = random.choice(self.off_topic_responses)
            return True, escape_response
        
        return False, None
    
    def requires_ai(self, message: str) -> bool:
        """Verifica se a mensagem requer IA (apenas para contexto de e-commerce)"""
        message_lower = message.lower()
        
        # Primeiro verifica se é off-topic - se for, NÃO precisa de IA
        is_off, _ = self.is_off_topic(message)
        if is_off:
            return False
        
        # Se tem palavras-chave de e-commerce, provavelmente precisa de IA
        for keyword in self.ai_keywords:
            if keyword in message_lower:
                return True
        
        # Se é uma pergunta complexa sobre e-commerce
        if self._is_complex_question(message):
            # Verifica se tem algum contexto de e-commerce
            if any(word in message_lower for word in ["produto", "pedido", "compra", "carrinho", "entrega"]):
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
                "urgency": "low",
                "is_off_topic": False
            }
        
        if len(message) > 1000:
            return {
                "valid": False,
                "reason": "Mensagem muito longa",
                "requires_ai": False,
                "urgency": "low",
                "is_off_topic": False
            }
        
        if self.is_spam(message):
            return {
                "valid": False,
                "reason": "Mensagem detectada como spam",
                "requires_ai": False,
                "urgency": "low",
                "is_off_topic": False
            }
        
        # Verifica se é off-topic ANTES de outras validações
        is_off_topic, escape_response = self.is_off_topic(message)
        if is_off_topic:
            return {
                "valid": True,
                "is_off_topic": True,
                "escape_response": escape_response,
                "auto_respond": True,
                "auto_response": {
                    "response": escape_response,
                    "confidence": 0.90,
                    "category": "off_topic_escape"
                },
                "requires_ai": False,  # NÃO chama IA para assuntos off-topic
                "urgency": "low",
                "keywords": [],
                "length": len(message)
            }
        
        auto_respond, auto_response = self.should_auto_respond(message)
        
        return {
            "valid": True,
            "is_off_topic": False,
            "auto_respond": auto_respond,
            "auto_response": auto_response,
            "requires_ai": self.requires_ai(message),
            "urgency": self.classify_urgency(message),
            "keywords": self.extract_context_keywords(message),
            "length": len(message)
        }


# Instância global dos filtros
message_filters = MessageFilters()


