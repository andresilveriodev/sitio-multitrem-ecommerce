"""
Processador de comandos de investimento - gera frontend_action conforme especificação
"""

from typing import Dict, Optional, Any
from datetime import datetime
import uuid
import structlog

from services.investment_extractor import investment_extractor
from services.market_service import market_service

logger = structlog.get_logger(__name__)


class InvestmentProcessor:
    """Processa comandos de investimento e gera frontend_action"""
    
    async def process_investment_command(
        self,
        message: str,
        ai_response: Optional[str],
        user_id: str,
        plan_id: Optional[str] = None,
        periodo_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa comando de investimento e retorna frontend_action
        
        Returns:
            Dict com response e frontend_action (se dados completos) ou None
        """
        try:
            # Extrair dados da mensagem e resposta da IA
            extracted = investment_extractor.extract_investment_data(message, ai_response)
            
            if not extracted:
                return None
            
            action_type = extracted.get("action_type")
            
            # Processar conforme o tipo de ação
            if action_type == "adicionar":
                return await self._process_add_investment(extracted, user_id, plan_id, periodo_id)
            elif action_type == "remover":
                return await self._process_remove_investment(extracted, user_id, plan_id, periodo_id)
            elif action_type == "atualizar":
                return await self._process_update_investment(extracted, user_id, plan_id, periodo_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao processar comando de investimento: {e}", exc_info=True)
            return None
    
    async def _process_add_investment(
        self,
        extracted: Dict[str, Any],
        user_id: str,
        plan_id: Optional[str],
        periodo_id: Optional[str]
    ) -> Dict[str, Any]:
        """Processa comando de adicionar investimento"""
        
        # Validar campos obrigatórios
        missing_fields = extracted.get("missing_fields", [])
        
        # Se falta informação crítica, perguntar ao usuário
        if missing_fields:
            return {
                "response": {
                    "response": self._generate_missing_fields_message(extracted, missing_fields),
                    "frontend_action": None,
                    "confirmation_required": False,
                    "needs_user_input": True,
                    "missing_fields": missing_fields
                }
            }
        
        # Buscar preço de mercado se não fornecido
        ticker = extracted.get("ticker")
        price = extracted.get("price")
        quantity = extracted.get("quantity")
        valor = extracted.get("valor")
        
        if ticker and not price:
            # Tentar buscar preço de mercado (nunca falha, retorna None se não conseguir)
            try:
                market_price = await market_service.get_ticker_price(ticker)
                if market_price:
                    price = market_price
                    extracted["price"] = price
                    extracted["price_from_market"] = True
                else:
                    # Se não conseguiu buscar (serviço instável ou ticker não encontrado), perguntar
                    return {
                        "response": {
                            "response": f"Para adicionar {quantity or 'o investimento'} de {ticker}, preciso saber o preço de compra. Qual foi o preço?",
                            "frontend_action": None,
                            "confirmation_required": False,
                            "needs_user_input": True,
                            "missing_fields": ["price"]
                        }
                    }
            except Exception:
                # Se houver qualquer erro (não deveria, mas garantia), perguntar ao usuário
                return {
                    "response": {
                        "response": f"Para adicionar {quantity or 'o investimento'} de {ticker}, preciso saber o preço de compra. Qual foi o preço?",
                        "frontend_action": None,
                        "confirmation_required": False,
                        "needs_user_input": True,
                        "missing_fields": ["price"]
                    }
                }
        
        # Calcular valores faltantes
        extracted = investment_extractor.calculate_missing_values(extracted)
        
        # Validar dados finais
        validation_result = self._validate_investment_data(extracted)
        if not validation_result["valid"]:
            return {
                "response": {
                    "response": validation_result["message"],
                    "frontend_action": None,
                    "confirmation_required": False,
                    "needs_user_input": True,
                    "missing_fields": validation_result["missing_fields"]
                }
            }
        
        # Gerar frontend_action
        frontend_action = {
            "type": "add_investment",
            "parameters": {
                "categoryName": extracted.get("category_name") or "Ações",
                "ticker": ticker,
                "quantity": extracted.get("quantity"),
                "price": extracted.get("price"),
                "valor": extracted.get("valor"),
                "isShort": extracted.get("is_short", False),
                "dataAquisicao": extracted.get("data_aquisicao") or datetime.now().strftime("%Y-%m-%d"),
                "rentabilidade": extracted.get("rentabilidade") or 0,
                "observacoes": f"Adicionado via chat"
            },
            "command_id": str(uuid.uuid4())
        }
        
        # Adicionar planId e periodoId se disponíveis
        if plan_id:
            frontend_action["parameters"]["planId"] = plan_id
        if periodo_id:
            frontend_action["parameters"]["periodoId"] = periodo_id
        
        # Gerar mensagem de resposta
        response_message = self._generate_add_investment_message(extracted, frontend_action)
        
        return {
            "response": {
                "response": response_message,
                "frontend_action": frontend_action,
                "confirmation_required": True,
                "needs_user_input": False,
                "missing_fields": []
            }
        }
    
    async def _process_remove_investment(
        self,
        extracted: Dict[str, Any],
        user_id: str,
        plan_id: Optional[str],
        periodo_id: Optional[str]
    ) -> Dict[str, Any]:
        """Processa comando de remover investimento"""
        
        ticker = extracted.get("ticker")
        
        if not ticker:
            return {
                "response": {
                    "response": "Para remover um investimento, preciso saber qual ticker ou investimento você quer remover.",
                    "frontend_action": None,
                    "confirmation_required": False,
                    "needs_user_input": True,
                    "missing_fields": ["ticker"]
                }
            }
        
        # Gerar frontend_action
        frontend_action = {
            "type": "remove_investment",
            "parameters": {
                "ticker": ticker,
                "categoryName": extracted.get("category_name"),
                "allFromCategory": False,
            },
            "command_id": str(uuid.uuid4())
        }
        
        if plan_id:
            frontend_action["parameters"]["planId"] = plan_id
        if periodo_id:
            frontend_action["parameters"]["periodoId"] = periodo_id
        
        return {
            "response": {
                "response": f"Remover investimento {ticker}?",
                "frontend_action": frontend_action,
                "confirmation_required": True,
                "needs_user_input": False
            }
        }
    
    async def _process_update_investment(
        self,
        extracted: Dict[str, Any],
        user_id: str,
        plan_id: Optional[str],
        periodo_id: Optional[str]
    ) -> Dict[str, Any]:
        """Processa comando de atualizar investimento"""
        
        ticker = extracted.get("ticker")
        
        if not ticker:
            return {
                "response": {
                    "response": "Para atualizar um investimento, preciso saber qual ticker você quer atualizar.",
                    "frontend_action": None,
                    "confirmation_required": False,
                    "needs_user_input": True,
                    "missing_fields": ["ticker"]
                }
            }
        
        # Verificar se tem pelo menos um campo para atualizar
        update_fields = {}
        if extracted.get("quantity"):
            update_fields["quantity"] = extracted["quantity"]
        if extracted.get("price"):
            update_fields["price"] = extracted["price"]
        if extracted.get("valor"):
            update_fields["valor"] = extracted["valor"]
        if extracted.get("rentabilidade"):
            update_fields["rentabilidade"] = extracted["rentabilidade"]
        
        if not update_fields:
            return {
                "response": {
                    "response": f"Para atualizar {ticker}, preciso saber o que você quer atualizar (quantidade, preço, valor ou rentabilidade).",
                    "frontend_action": None,
                    "confirmation_required": False,
                    "needs_user_input": True,
                    "missing_fields": ["update_fields"]
                }
            }
        
        # Gerar frontend_action
        frontend_action = {
            "type": "update_investment",
            "parameters": {
                "ticker": ticker,
                **update_fields
            },
            "command_id": str(uuid.uuid4())
        }
        
        if plan_id:
            frontend_action["parameters"]["planId"] = plan_id
        
        return {
            "response": {
                "response": f"Atualizar {ticker} com os novos valores?",
                "frontend_action": frontend_action,
                "confirmation_required": True,
                "needs_user_input": False
            }
        }
    
    def _validate_investment_data(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados de investimento"""
        missing = []
        
        # Validar ticker
        ticker = extracted.get("ticker")
        if not ticker:
            missing.append("ticker")
        
        # Validar quantidade ou valor
        quantity = extracted.get("quantity")
        valor = extracted.get("valor")
        if not quantity and not valor:
            missing.append("quantity ou valor")
        
        # Validar preço (se tem quantity)
        if quantity and not extracted.get("price"):
            missing.append("price")
        
        if missing:
            return {
                "valid": False,
                "message": f"Faltam informações: {', '.join(missing)}",
                "missing_fields": missing
            }
        
        # Validar valores numéricos
        if quantity and quantity == 0:
            return {
                "valid": False,
                "message": "Quantidade não pode ser zero",
                "missing_fields": []
            }
        
        if extracted.get("price") and extracted["price"] <= 0:
            return {
                "valid": False,
                "message": "Preço deve ser maior que zero",
                "missing_fields": []
            }
        
        return {
            "valid": True,
            "message": "Dados válidos",
            "missing_fields": []
        }
    
    def _generate_missing_fields_message(
        self,
        extracted: Dict[str, Any],
        missing_fields: list
    ) -> str:
        """Gera mensagem perguntando campos faltantes"""
        action_type = extracted.get("action_type", "adicionar")
        ticker = extracted.get("ticker", "")
        
        base_message = f"Para {action_type}"
        if ticker:
            base_message += f" {ticker}"
        base_message += ", preciso saber:\n"
        
        messages = []
        for field in missing_fields:
            if field == "ticker ou nome do investimento":
                messages.append("• Qual o ticker ou nome do investimento?")
            elif field == "quantity ou valor total":
                messages.append("• Quantas ações/cotas ou qual o valor total?")
            elif field == "price":
                messages.append("• Qual foi o preço de compra? (ou posso usar o preço atual de mercado)")
            elif field == "dataAquisicao":
                messages.append("• Qual a data de aquisição? (ou uso a data de hoje)")
        
        return base_message + "\n".join(messages)
    
    def _generate_add_investment_message(
        self,
        extracted: Dict[str, Any],
        frontend_action: Dict[str, Any]
    ) -> str:
        """Gera mensagem de resposta para adicionar investimento"""
        ticker = extracted.get("ticker")
        quantity = extracted.get("quantity")
        price = extracted.get("price")
        valor = extracted.get("valor")
        is_short = extracted.get("is_short", False)
        price_from_market = extracted.get("price_from_market", False)
        
        message = "Adicionei"
        
        if is_short:
            message = "Operação vendida detectada:"
            message += f"\n• Ticker: {ticker}"
            message += f"\n• Quantidade: {quantity} (negativa = posição vendida)"
        else:
            message += f" {abs(quantity) if quantity else 'o investimento'} de {ticker}"
        
        if price:
            if price_from_market:
                message += f"\n• Preço: R$ {price:.2f} (preço atual de mercado)"
            else:
                message += f"\n• Preço: R$ {price:.2f}"
        
        if valor:
            message += f"\n• Valor total: R$ {abs(valor):.2f}"
        
        message += "\n\nDeseja confirmar a adição?"
        
        return message


# Instância global
investment_processor = InvestmentProcessor()

