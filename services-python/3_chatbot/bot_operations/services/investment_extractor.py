"""
Serviço para extrair dados de investimentos da resposta da IA e mensagens do usuário
"""

import re
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class InvestmentDataExtractor:
    """Extrai dados de investimentos de mensagens e respostas da IA"""
    
    def __init__(self):
        # Padrões para extração
        self.ticker_pattern = re.compile(r'\b([A-Z]{4}\d)\b', re.IGNORECASE)
        self.number_pattern = re.compile(r'\b(\d+(?:[.,]\d+)?)\b')
        self.currency_pattern = re.compile(r'R\$\s*(\d+(?:[.,]\d+)?)')
        self.percentage_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s*%')
        
        # Palavras-chave para identificar ações
        self.action_keywords = {
            "adicionar": ["adiciona", "adicionar", "adicionar", "adiciona", "add", "comprar", "comprei", "compre"],
            "remover": ["remove", "remover", "remova", "excluir", "exclua", "delete", "vender", "vendi", "venda"],
            "atualizar": ["atualiza", "atualizar", "atualize", "mudar", "mude", "alterar", "altere", "update"],
            "quantidade": ["quantidade", "qtd", "qty", "ações", "cotas", "unidades"],
            "preço": ["preço", "price", "valor unitário", "cotação"],
            "valor": ["valor", "value", "total", "montante", "quantia"],
            "categoria": ["categoria", "category", "tipo", "classe"],
            "rentabilidade": ["rentabilidade", "yield", "retorno", "rendimento"]
        }
        
        # Tipos de investimento conhecidos
        self.investment_types = {
            "ações": ["ação", "ações", "stock", "stocks", "equity"],
            "cdb": ["cdb", "certificado de depósito bancário"],
            "lci": ["lci", "letra de crédito imobiliário"],
            "lca": ["lca", "letra de crédito do agronegócio"],
            "fii": ["fii", "fundos imobiliários", "fundo imobiliário"],
            "tesouro": ["tesouro", "tesouro direto", "td", "titulo público"],
            "criptomoedas": ["criptomoeda", "bitcoin", "btc", "ethereum", "eth", "crypto"]
        }
    
    def extract_investment_data(
        self, 
        message: str, 
        ai_response: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extrai dados de investimento da mensagem e resposta da IA
        
        Returns:
            Dict com dados extraídos ou None se não for comando de investimento
        """
        try:
            # Normalizar mensagem
            normalized = message.lower().strip()
            
            # Verificar se é comando de investimento
            action_type = self._detect_action_type(normalized)
            if not action_type:
                return None
            
            # Extrair dados básicos
            extracted = {
                "action_type": action_type,
                "ticker": self._extract_ticker(normalized),
                "quantity": self._extract_quantity(normalized),
                "price": self._extract_price(normalized),
                "valor": self._extract_valor(normalized),
                "category_name": self._extract_category(normalized),
                "data_aquisicao": self._extract_date(normalized),
                "rentabilidade": self._extract_rentabilidade(normalized),
                "is_short": self._detect_short_selling(normalized),
                "missing_fields": []
            }
            
            # Validar dados obrigatórios
            extracted["missing_fields"] = self._validate_required_fields(extracted, action_type)
            
            # Processar resposta da IA se disponível
            if ai_response:
                extracted = self._merge_ai_response(extracted, ai_response)
            
            return extracted
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados de investimento: {e}", exc_info=True)
            return None
    
    def _detect_action_type(self, message: str) -> Optional[str]:
        """Detecta o tipo de ação (adicionar, remover, atualizar)"""
        message_lower = message.lower()
        
        for action, keywords in self.action_keywords.items():
            if action in ["adicionar", "remover", "atualizar"]:
                for keyword in keywords:
                    if keyword in message_lower:
                        return action
        
        return None
    
    def _extract_ticker(self, message: str) -> Optional[str]:
        """Extrai ticker da mensagem"""
        match = self.ticker_pattern.search(message.upper())
        if match:
            return match.group(1)
        return None
    
    def _extract_quantity(self, message: str) -> Optional[float]:
        """Extrai quantidade da mensagem"""
        # Procurar por números que parecem quantidade
        numbers = self.number_pattern.findall(message)
        
        for num_str in numbers:
            try:
                # Normalizar vírgula para ponto
                num_str = num_str.replace(',', '.')
                quantity = float(num_str)
                
                # Verificar se parece quantidade (não preço)
                # Quantidades geralmente são inteiras ou números grandes
                if quantity > 0 and (quantity == int(quantity) or quantity >= 10):
                    # Se tem palavras relacionadas a quantidade
                    if any(kw in message for kw in ["quantidade", "qtd", "ações", "cotas", "unidades"]):
                        return quantity
                    # Se o número está próximo de palavras de ação
                    num_pos = message.find(num_str)
                    context = message[max(0, num_pos-20):num_pos+20]
                    if any(kw in context for kw in ["adiciona", "comprar", "vender", "remove"]):
                        return quantity
            except (ValueError, TypeError):
                continue
        
        return None
    
    def _extract_price(self, message: str) -> Optional[float]:
        """Extrai preço da mensagem"""
        # Procurar por padrões de preço
        price_patterns = [
            r'preço[:\s]+R\$\s*(\d+(?:[.,]\d+)?)',
            r'preço[:\s]+(\d+(?:[.,]\d+)?)',
            r'a\s+R\$\s*(\d+(?:[.,]\d+)?)',
            r'por\s+R\$\s*(\d+(?:[.,]\d+)?)',
            r'R\$\s*(\d+(?:[.,]\d+)?)\s*por',
            r'(\d+(?:[.,]\d+)?)\s*reais'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    price_str = match.group(1).replace(',', '.')
                    price = float(price_str)
                    if 0.01 <= price <= 10000:  # Range razoável
                        return price
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_valor(self, message: str) -> Optional[float]:
        """Extrai valor total da mensagem"""
        # Procurar por padrões de valor total
        valor_patterns = [
            r'valor[:\s]+total[:\s]+R\$\s*(\d+(?:[.,]\d+)?)',
            r'valor[:\s]+R\$\s*(\d+(?:[.,]\d+)?)',
            r'total[:\s]+R\$\s*(\d+(?:[.,]\d+)?)',
            r'R\$\s*(\d+(?:[.,]\d+)?)\s*em',
            r'investi[:\s]+R\$\s*(\d+(?:[.,]\d+)?)'
        ]
        
        for pattern in valor_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    valor_str = match.group(1).replace(',', '.')
                    valor = float(valor_str)
                    if valor > 0:
                        return valor
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_category(self, message: str) -> Optional[str]:
        """Extrai categoria do investimento"""
        message_lower = message.lower()
        
        for category, keywords in self.investment_types.items():
            for keyword in keywords:
                if keyword in message_lower:
                    # Normalizar nome da categoria
                    if category == "ações":
                        return "Ações"
                    elif category == "fii":
                        return "FIIs"
                    elif category == "tesouro":
                        return "Tesouro Direto"
                    elif category == "criptomoedas":
                        return "Criptomoedas"
                    else:
                        return category.upper()
        
        # Se tem ticker, provavelmente é ação
        if self._extract_ticker(message):
            return "Ações"
        
        return None
    
    def _extract_date(self, message: str) -> Optional[str]:
        """Extrai data de aquisição"""
        # Padrões de data
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 3:
                        # Formato padrão: YYYY-MM-DD
                        if '/' in match.group(0):
                            day, month, year = match.groups()
                            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        elif '-' in match.group(0):
                            return match.group(0)
                except (ValueError, TypeError):
                    continue
        
        # Se não encontrou, retorna None (será usado data atual)
        return None
    
    def _extract_rentabilidade(self, message: str) -> Optional[float]:
        """Extrai rentabilidade"""
        match = self.percentage_pattern.search(message)
        if match:
            try:
                rent_str = match.group(1).replace(',', '.')
                rent = float(rent_str)
                if 0 <= rent <= 100:
                    return rent
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _detect_short_selling(self, message: str) -> bool:
        """Detecta se é operação vendida (short selling)"""
        message_lower = message.lower()
        
        # Palavras-chave de venda
        sell_keywords = ["vender", "vendi", "venda", "operação vendida", "short", "vendeu"]
        negative_keywords = ["-", "menos", "negativo", "negativa"]
        
        # Verificar se tem quantidade negativa
        if any(kw in message_lower for kw in sell_keywords):
            # Verificar se tem sinal negativo
            if any(kw in message_lower for kw in negative_keywords):
                return True
            
            # Verificar se tem número negativo
            negative_pattern = re.compile(r'-\s*(\d+(?:[.,]\d+)?)')
            if negative_pattern.search(message):
                return True
        
        return False
    
    def _validate_required_fields(
        self, 
        extracted: Dict[str, Any], 
        action_type: str
    ) -> List[str]:
        """Valida campos obrigatórios e retorna lista de campos faltantes"""
        missing = []
        
        if action_type == "adicionar":
            # Para adicionar: ticker OU nome, quantity OU valor
            if not extracted.get("ticker") and not extracted.get("category_name"):
                missing.append("ticker ou nome do investimento")
            
            if not extracted.get("quantity") and not extracted.get("valor"):
                missing.append("quantity ou valor total")
        
        elif action_type == "remover":
            # Para remover: ticker OU investmentId
            if not extracted.get("ticker"):
                missing.append("ticker ou investmentId")
        
        elif action_type == "atualizar":
            # Para atualizar: ticker OU investmentId, e pelo menos um campo para atualizar
            if not extracted.get("ticker"):
                missing.append("ticker ou investmentId")
            
            if not any([
                extracted.get("quantity"),
                extracted.get("price"),
                extracted.get("valor"),
                extracted.get("rentabilidade")
            ]):
                missing.append("pelo menos um campo para atualizar (quantity, price, valor, rentabilidade)")
        
        return missing
    
    def _merge_ai_response(
        self, 
        extracted: Dict[str, Any], 
        ai_response: str
    ) -> Dict[str, Any]:
        """Mescla dados extraídos com informações da resposta da IA"""
        # Tentar extrair dados adicionais da resposta da IA
        ai_lower = ai_response.lower()
        
        # Se a IA mencionou preço
        if not extracted.get("price"):
            price = self._extract_price(ai_response)
            if price:
                extracted["price"] = price
                extracted["price_from_ai"] = True
        
        # Se a IA mencionou valor
        if not extracted.get("valor"):
            valor = self._extract_valor(ai_response)
            if valor:
                extracted["valor"] = valor
                extracted["valor_from_ai"] = True
        
        # Se a IA mencionou categoria
        if not extracted.get("category_name"):
            category = self._extract_category(ai_response)
            if category:
                extracted["category_name"] = category
        
        return extracted
    
    def calculate_missing_values(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula valores faltantes quando possível"""
        # Se tem quantity e price, calcular valor
        if extracted.get("quantity") and extracted.get("price") and not extracted.get("valor"):
            quantity = extracted["quantity"]
            price = extracted["price"]
            # Se é operação vendida, valor é negativo
            if extracted.get("is_short"):
                extracted["valor"] = -(abs(quantity) * price)
            else:
                extracted["valor"] = abs(quantity) * price
            extracted["valor_calculated"] = True
        
        # Se tem valor e price, calcular quantity
        elif extracted.get("valor") and extracted.get("price") and not extracted.get("quantity"):
            valor = abs(extracted["valor"])
            price = extracted["price"]
            if price > 0:
                quantity = valor / price
                extracted["quantity"] = quantity if not extracted.get("is_short") else -quantity
                extracted["quantity_calculated"] = True
        
        # Se tem valor e quantity, calcular price
        elif extracted.get("valor") and extracted.get("quantity") and not extracted.get("price"):
            valor = abs(extracted["valor"])
            quantity = abs(extracted["quantity"])
            if quantity > 0:
                extracted["price"] = valor / quantity
                extracted["price_calculated"] = True
        
        return extracted


# Instância global
investment_extractor = InvestmentDataExtractor()

