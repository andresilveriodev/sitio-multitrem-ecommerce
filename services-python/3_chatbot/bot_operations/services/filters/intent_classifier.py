"""
Classificador de Intents - Firewall de Conversa
Classifica mensagens em intents do e-commerce sem usar IA
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class Intent(Enum):
    """Intents válidos do e-commerce"""
    # Intents que PASSAM (válidos)
    CATALOG = "CATALOG"  # cardápio, disponibilidade, preço
    ORDER_CREATE = "ORDER_CREATE"  # quero pedir, adicionar
    ORDER_UPDATE = "ORDER_UPDATE"  # remover, alterar quantidade
    ORDER_STATUS = "ORDER_STATUS"  # meu pedido, status
    DELIVERY = "DELIVERY"  # entrega, rota, horário, endereço
    PAYMENT = "PAYMENT"  # pix, pagamento, comprovante
    ACCOUNT = "ACCOUNT"  # cadastro, atualizar dados
    COMPLAINT = "COMPLAINT"  # reclamação, troca, produto ruim
    SUPPORT = "SUPPORT"  # ajuda, como usar
    
    # Intents que NÃO PASSAM
    OFFTOPIC = "OFFTOPIC"  # assunto fora do contexto
    DANGEROUS = "DANGEROUS"  # conteúdo perigoso
    ABUSE = "ABUSE"  # abuso, spam
    UNKNOWN = "UNKNOWN"  # não identificado claramente


class IntentClassifier:
    """Classificador de intents usando regras e heurísticas"""
    
    def __init__(self):
        # Whitelist: Produtos do e-commerce
        self.product_keywords = {
            # Verduras e hortaliças
            "alface", "rúcula", "rucula", "coentro", "cebolinha", "cheiro-verde",
            "cheiro verde", "salsa", "couve", "espinafre", "agrião", "agriao",
            "almeirão", "almeirao", "repolho", "brócolis", "brocolis", "couve-flor",
            "couve flor", "acelga", "mostarda", "rabanete", "nabo", "cenoura",
            "beterraba", "tomate", "cebola", "alho", "pimentão", "pimentao",
            "pimenta", "berinjela", "beringela", "abobrinha", "abóbora", "abobora",
            "chuchu", "quiabo", "jiló", "jilo", "maxixe", "pepino",
            
            # Ovos e derivados
            "ovo", "ovos", "cartela", "dúzia", "duzia", "meia dúzia", "meia duzia",
            
            # Outros produtos
            "produto", "produtos", "item", "itens", "kit", "cesta", "box"
        }
        
        # Whitelist: Ações do e-commerce
        self.action_keywords = {
            # Pedidos
            "pedir", "pedido", "pedidos", "comprar", "compra", "quero", "preciso",
            "manda", "envia", "adicionar", "add", "remover", "rem", "tirar",
            "confirmar", "confirmar pedido", "finalizar", "cancelar", "cancelar pedido",
            
            # Catálogo
            "cardápio", "cardapio", "catálogo", "catalogo", "menu", "produtos",
            "disponível", "disponivel", "tem", "tem disponível", "tem disponivel",
            "preço", "preco", "preços", "precos", "valor", "quanto custa",
            
            # Entrega
            "entrega", "entregar", "delivery", "frete", "envio", "horário", "horario",
            "quando chega", "quando chegará", "quando chegara", "rota", "endereço",
            "endereco", "local", "onde entregar",
            
            # Pagamento
            "pagar", "pagamento", "pix", "cartão", "cartao", "boleto", "dinheiro",
            "comprovante", "recibo", "nota fiscal", "nf",
            
            # Conta
            "cadastro", "cadastrar", "conta", "perfil", "dados", "atualizar",
            "telefone", "celular", "email", "nome", "endereço", "endereco",
            
            # Status
            "meu pedido", "status", "rastrear", "rastreamento", "onde está",
            "onde esta", "já saiu", "ja saiu", "foi entregue", "entregue",
            
            # Reclamação/Suporte
            "reclamação", "reclamacao", "reclamar", "problema", "erro", "faltou",
            "veio errado", "trocado", "troca", "devolução", "devolucao",
            "produto ruim", "estragado", "vencido", "ajuda", "suporte", "como usar"
        }
        
        # Quantificadores
        self.quantity_keywords = {
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            "um", "dois", "três", "tres", "quatro", "cinco", "seis", "sete",
            "oito", "nove", "dez", "dúzia", "duzia", "meia dúzia", "meia duzia",
            "cartela", "maço", "maco", "palito", "unidade", "un", "unid"
        }
        
        # Blacklist: Palavras que indicam off-topic (EXCLUINDO saudações/despedidas)
        # Saudações e despedidas são permitidas e respondidas automaticamente (SEM IA)
        self.off_topic_keywords = {
            # Clima
            "clima", "tempo", "chuva", "sol", "temperatura", "previsão", "previsao",
            "frio", "calor", "vento", "umidade",
            
            # Notícias/Política
            "notícia", "noticia", "jornal", "política", "politica", "eleição",
            "eleicao", "presidente", "governo", "congresso",
            
            # Entretenimento
            "filme", "cinema", "série", "serie", "música", "musica", "futebol",
            "time", "jogo", "esporte",
            
            # Educação
            "história", "historia", "geografia", "matemática", "matematica",
            "física", "fisica", "química", "quimica",
            
            # Saúde
            "medicina", "médico", "medico", "doença", "doenca", "remédio",
            "remedio", "hospital",
            
            # Tecnologia geral
            "programação", "programacao", "código", "codigo", "python", "javascript",
            
            # Assuntos pessoais profundos (mas permite saudações básicas)
            "onde você mora", "qual sua idade", "você tem sentimentos",
            
            # Homebroker (removido do contexto)
            "ação", "ações", "bolsa", "investir", "trading", "ibovespa", "petrobras"
        }
        
        # Saudações e despedidas permitidas (respondidas automaticamente SEM IA)
        self.greeting_keywords = {
            "oi", "olá", "ola", "hey", "hi", "hello",
            "tudo bem", "tudo bom", "td bem", "td bom", "tudo certo",
            "como você está", "como vc está", "como vai",
            "bom dia", "boa tarde", "boa noite",
            "obrigado", "obrigada", "valeu", "thanks", "thank you",
            "tchau", "adeus", "até logo", "bye", "goodbye", "até mais"
        }
        
        # Padrões de mensagens perigosas/abusivas
        self.dangerous_patterns = [
            r"\b(matar|matar-se|suicídio|suicidio)\b",
            r"\b(bomba|explosão|explosao|terrorismo)\b",
            r"\b(droga|maconha|cocaína|cocaina)\b",
            r"\b(prostituição|prostituicao|sexo|pornografia)\b"
        ]
        
        # Padrões de spam
        self.spam_patterns = [
            r"\b(www\.|http://|https://)\b",
            r"\b(compre agora|oferta limitada|ganhe dinheiro|riqueza rápida)\b",
            r"\b\d{10,}\b",  # Muitos números
            r"\b[A-Z]{10,}\b",  # Muitas letras maiúsculas
        ]
        
        # Respostas padrão para off-topic
        self.off_topic_responses = [
            "🌱 Aqui é o bot do Sítio Multitrem.\nEu ajudo com pedidos, cardápio, entrega e pagamento.\nDigite *cardapio* ou *pedido*.",
            "Olá! Sou o assistente do Sítio Multitrem 🌱\nSó consigo ajudar com pedidos, cardápio, entrega e pagamento.\nDigite *cardapio* ou *pedido*.",
            "Oi! Aqui é o bot do Sítio Multitrem.\nPosso ajudar com pedidos, cardápio, entrega e pagamento.\nDigite *cardapio* ou *pedido*."
        ]
    
    def normalize_message(self, message: str) -> str:
        """Normaliza mensagem: lowercase, remove acentos, limpa espaços"""
        import unicodedata
        
        # Lowercase
        normalized = message.lower().strip()
        
        # Remove acentos
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
        
        # Limpa espaços múltiplos
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def extract_commands(self, message: str) -> List[str]:
        """Extrai comandos da mensagem"""
        commands = []
        normalized = self.normalize_message(message)
        
        # Comandos simples
        command_patterns = [
            r'\b(cardapio|catalogo|menu)\b',
            r'\b(pedido|meu pedido)\b',
            r'\b(confirmar|cancelar)\b',
            r'\b(endereco|endereço|trocar endereco)\b',
            r'\b(pix|pagar|pagamento)\b',
            r'\b(entrega|horario|frete)\b',
            r'\b(ajuda|suporte|como usar)\b'
        ]
        
        for pattern in command_patterns:
            if re.search(pattern, normalized):
                commands.append(pattern)
        
        return commands
    
    def classify_intent(self, message: str) -> Tuple[Intent, Dict[str, Any]]:
        """
        Classifica intent da mensagem usando modelo de 3 etapas:
        1. Regras fortes (ganham na hora)
        2. Score por intenção
        3. Fallback (se necessário)
        
        Returns:
            Tuple[Intent, Dict]: (intent, metadata com score e regras que bateram)
        """
        normalized = self.normalize_message(message)
        metadata = {
            "score": 0,
            "rules_hit": [],
            "confidence": 0.0,
            "method": "unknown"  # "strong_rule", "score", "fallback"
        }
        
        # ============================================================
        # ETAPA 1: REGRAS FORTES (ganham na hora - sem pensar)
        # ============================================================
        strong_rule_intent = self._check_strong_rules(normalized, metadata)
        if strong_rule_intent:
            metadata["method"] = "strong_rule"
            metadata["confidence"] = 0.95
            return strong_rule_intent, metadata
        
        # ============================================================
        # ETAPA 2: SCORE POR INTENÇÃO (barato e escalável)
        # ============================================================
        
        # 1. Verifica padrões perigosos/abusivos (prioridade máxima)
        for pattern in self.dangerous_patterns:
            if re.search(pattern, normalized):
                logger.warning("Mensagem detectada como perigosa/abusiva", pattern=pattern)
                metadata["rules_hit"].append(f"dangerous_pattern:{pattern}")
                metadata["method"] = "strong_rule"
                return Intent.DANGEROUS, metadata
        
        # 2. Verifica spam
        for pattern in self.spam_patterns:
            if re.search(pattern, normalized):
                logger.warning("Mensagem detectada como spam", pattern=pattern)
                metadata["rules_hit"].append(f"spam_pattern:{pattern}")
                metadata["method"] = "strong_rule"
                return Intent.ABUSE, metadata
        
        # 3. Calcula scores por intent
        intent_scores = self._calculate_intent_scores(normalized, metadata)
        
        # 4. Encontra intent com maior score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        best_intent_name, best_score = best_intent
        
        metadata["score"] = best_score
        metadata["method"] = "score"
        metadata["intent_scores"] = intent_scores
        
        # Se score é muito baixo ou empate, vai para fallback
        if best_score < 2 or self._has_tie(intent_scores, best_score):
            metadata["method"] = "fallback"
            metadata["confidence"] = 0.3
            return Intent.UNKNOWN, metadata
        
        # Determina intent baseado no melhor score
        intent = self._score_to_intent(best_intent_name, best_score, normalized)
        
        # Calcula confiança baseada no score
        if best_score >= 5:
            metadata["confidence"] = min(0.95, 0.6 + (best_score / 30))
        elif best_score >= 3:
            metadata["confidence"] = 0.7
        else:
            metadata["confidence"] = 0.5
        
        return intent, metadata
    
    def _check_strong_rules(self, normalized: str, metadata: Dict) -> Optional[Intent]:
        """
        ETAPA 1: Regras fortes - padrões muito claros que ganham na hora
        """
        # Comandos explícitos
        if re.search(r'^\s*/(start|inicio|comecar)', normalized):
            metadata["rules_hit"].append("strong_rule:/start")
            return Intent.ACCOUNT
        
        if re.search(r'\b(confirmar|confirmar pedido)\b', normalized):
            metadata["rules_hit"].append("strong_rule:confirmar")
            return Intent.ORDER_CREATE
        
        if re.search(r'\b(cardapio|catalogo|menu|produtos)\b', normalized):
            metadata["rules_hit"].append("strong_rule:cardapio")
            return Intent.CATALOG
        
        if re.search(r'\b(pix|comprovante|pagamento|pagar)\b', normalized):
            metadata["rules_hit"].append("strong_rule:pix")
            return Intent.PAYMENT
        
        if re.search(r'\b(meu pedido|status|rastrear|rastreamento)\b', normalized):
            metadata["rules_hit"].append("strong_rule:status")
            return Intent.ORDER_STATUS
        
        # Padrão: quantidade + item (ex: "2 alfaces", "1 cartela ovos")
        if re.search(r'\b(\d+|um|dois|três|tres|quatro|cinco)\s+(alface|rúcula|rucula|ovo|cartela|maço|maco|palito|coentro|cebolinha)', normalized):
            metadata["rules_hit"].append("strong_rule:produto+quantidade")
            return Intent.ORDER_CREATE
        
        # Padrão: verbo de ação + item
        if re.search(r'\b(add|adicionar|quero|preciso|manda)\s+.*(alface|rúcula|rucula|ovo|cartela)', normalized):
            metadata["rules_hit"].append("strong_rule:acao+produto")
            return Intent.ORDER_CREATE
        
        # Padrão: remover/alterar
        if re.search(r'\b(rem|remover|tirar|alterar|mudar)\s+.*(alface|rúcula|rucula|ovo|cartela)', normalized):
            metadata["rules_hit"].append("strong_rule:remover")
            return Intent.ORDER_UPDATE
        
        return None
    
    def _calculate_intent_scores(self, normalized: str, metadata: Dict) -> Dict[str, int]:
        """
        ETAPA 2: Calcula scores por intent usando sinais
        """
        scores = {
            "CATALOG": 0,
            "ORDER_CREATE": 0,
            "ORDER_UPDATE": 0,
            "ORDER_STATUS": 0,
            "DELIVERY": 0,
            "PAYMENT": 0,
            "ACCOUNT": 0,
            "COMPLAINT": 0,
            "SUPPORT": 0,
            "OFFTOPIC": 0
        }
        
        # Sinais para CATALOG
        catalog_signals = ["cardapio", "catalogo", "menu", "produtos", "preço", "preco", "disponível", "disponivel", "tem", "tem disponível"]
        for signal in catalog_signals:
            if signal in normalized:
                scores["CATALOG"] += 2
                metadata["rules_hit"].append(f"catalog_signal:{signal}")
        
        # Sinais para ORDER_CREATE
        order_create_signals = ["pedir", "pedido", "comprar", "quero", "preciso", "manda", "adicionar", "add"]
        for signal in order_create_signals:
            if signal in normalized:
                scores["ORDER_CREATE"] += 2
                metadata["rules_hit"].append(f"order_create_signal:{signal}")
        
        # Padrão regex: quantidade + item
        if re.search(r'\b(\d+|um|dois|três|tres)\s+(alface|rúcula|rucula|ovo|cartela)', normalized):
            scores["ORDER_CREATE"] += 5
            metadata["rules_hit"].append("order_pattern:quantidade+item")
        
        # Sinais para ORDER_UPDATE
        order_update_signals = ["remover", "rem", "tirar", "alterar", "mudar", "cancelar"]
        for signal in order_update_signals:
            if signal in normalized:
                scores["ORDER_UPDATE"] += 2
                metadata["rules_hit"].append(f"order_update_signal:{signal}")
        
        # Sinais para ORDER_STATUS
        status_signals = ["meu pedido", "status", "rastrear", "rastreamento", "onde está", "onde esta", "já saiu", "ja saiu"]
        for signal in status_signals:
            if signal in normalized:
                scores["ORDER_STATUS"] += 3
                metadata["rules_hit"].append(f"status_signal:{signal}")
        
        # Sinais para DELIVERY
        delivery_signals = ["entrega", "entregar", "delivery", "frete", "horário", "horario", "quando chega", "endereço", "endereco"]
        # Presença de data + "entrega"
        if re.search(r'\b(hoje|amanhã|amanha|agora)\s+.*(entrega|entregar)', normalized):
            scores["DELIVERY"] += 5
            metadata["rules_hit"].append("delivery_pattern:data+entrega")
        for signal in delivery_signals:
            if signal in normalized:
                scores["DELIVERY"] += 2
                metadata["rules_hit"].append(f"delivery_signal:{signal}")
        
        # Sinais para PAYMENT
        payment_signals = ["pix", "pagar", "pagamento", "cartão", "cartao", "boleto", "comprovante"]
        for signal in payment_signals:
            if signal in normalized:
                scores["PAYMENT"] += 3
                metadata["rules_hit"].append(f"payment_signal:{signal}")
        
        # Sinais para ACCOUNT
        account_signals = ["cadastro", "cadastrar", "conta", "perfil", "atualizar", "telefone", "email", "endereço", "endereco"]
        for signal in account_signals:
            if signal in normalized:
                scores["ACCOUNT"] += 2
                metadata["rules_hit"].append(f"account_signal:{signal}")
        
        # Sinais para COMPLAINT
        complaint_signals = ["reclamação", "reclamacao", "reclamar", "problema", "erro", "faltou", "troca", "devolução", "devolucao"]
        for signal in complaint_signals:
            if signal in normalized:
                scores["COMPLAINT"] += 2
                metadata["rules_hit"].append(f"complaint_signal:{signal}")
        
        # Sinais para SUPPORT
        support_signals = ["ajuda", "suporte", "como usar", "como funciona"]
        for signal in support_signals:
            if signal in normalized:
                scores["SUPPORT"] += 2
                metadata["rules_hit"].append(f"support_signal:{signal}")
        
        # Sinais para OFFTOPIC (penaliza)
        for signal in self.off_topic_keywords:
            if signal in normalized:
                scores["OFFTOPIC"] += 3
                # Penaliza outros intents
                for intent in scores:
                    if intent != "OFFTOPIC":
                        scores[intent] -= 1
                metadata["rules_hit"].append(f"offtopic_signal:{signal}")
        
        # Palavras de produtos (aumenta score de ORDER_CREATE/UPDATE)
        product_matches = [kw for kw in self.product_keywords if kw in normalized]
        if product_matches:
            scores["ORDER_CREATE"] += len(product_matches) * 2
            scores["ORDER_UPDATE"] += len(product_matches)
            metadata["rules_hit"].append(f"products:{product_matches[:3]}")
        
        return scores
    
    def _has_tie(self, scores: Dict[str, int], best_score: int) -> bool:
        """Verifica se há empate (múltiplos intents com mesmo score)"""
        count = sum(1 for score in scores.values() if score == best_score)
        return count > 1
    
    def _score_to_intent(self, intent_name: str, score: int, normalized: str) -> Intent:
        """Converte nome do intent em Enum Intent"""
        intent_map = {
            "CATALOG": Intent.CATALOG,
            "ORDER_CREATE": Intent.ORDER_CREATE,
            "ORDER_UPDATE": Intent.ORDER_UPDATE,
            "ORDER_STATUS": Intent.ORDER_STATUS,
            "DELIVERY": Intent.DELIVERY,
            "PAYMENT": Intent.PAYMENT,
            "ACCOUNT": Intent.ACCOUNT,
            "COMPLAINT": Intent.COMPLAINT,
            "SUPPORT": Intent.SUPPORT,
            "OFFTOPIC": Intent.OFFTOPIC
        }
        
        return intent_map.get(intent_name, Intent.UNKNOWN)
    
    
    def get_escape_response(self, intent: Intent) -> Optional[str]:
        """Retorna resposta de escape baseada no intent"""
        import random
        
        if intent == Intent.OFFTOPIC:
            return random.choice(self.off_topic_responses)
        
        if intent == Intent.DANGEROUS or intent == Intent.ABUSE:
            return "Mensagem bloqueada. Por favor, use o bot apenas para pedidos e dúvidas sobre o e-commerce."
        
        if intent == Intent.UNKNOWN:
            # ETAPA 3: FALLBACK - Pergunta curta com opções (SEM IA)
            return "Não entendi. Você quer:\n\n📋 *Produtos* (cardápio)\n🧺 *Fazer pedido*\n🚚 *Entrega*\n💰 *Pagamento*\n\nDigite uma das opções acima."
        
        return None
    
    def should_call_ai(self, intent: Intent, score: int, message: str) -> bool:
        """
        Decide se deve chamar a IA baseado no intent e contexto
        
        Regras:
        - OFFTOPIC, DANGEROUS, ABUSE: NUNCA chama IA
        - UNKNOWN com score baixo: NÃO chama IA (usa template)
        - Intents válidos com score alto: pode chamar IA se necessário
        - Mensagens muito naturais/ambíguas: chama IA
        """
        # Nunca chama IA para intents bloqueados
        if intent in [Intent.OFFTOPIC, Intent.DANGEROUS, Intent.ABUSE]:
            return False
        
        # UNKNOWN com score baixo: não chama IA
        if intent == Intent.UNKNOWN and score < 2:
            return False
        
        # Intents válidos: chama IA apenas se:
        # 1. Mensagem é muito natural/ambígua (ex: "monta um kit pra 4 pessoas")
        # 2. É reclamação complexa
        # 3. Não conseguiu extrair pedido por regras
        
        if intent in [Intent.ORDER_CREATE, Intent.ORDER_UPDATE]:
            # Verifica se tem padrão claro de pedido
            has_clear_pattern = bool(re.search(r'(\d+)\s*(alface|rúcula|rucula|ovo|cartela)', message.lower()))
            if has_clear_pattern:
                return False  # Pode extrair por regra, não precisa IA
        
        if intent == Intent.COMPLAINT:
            # Reclamações complexas podem precisar de IA
            if len(message.split()) > 10:
                return True
        
        # Para outros intents válidos, geralmente não precisa de IA
        # (podem ser respondidos com templates ou chamadas a APIs)
        return False


# Instância global do classificador
intent_classifier = IntentClassifier()
