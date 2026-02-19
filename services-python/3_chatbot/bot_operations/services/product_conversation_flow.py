"""
Fluxo conversacional para CRUD de produtos via Telegram
"""

from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime
import structlog

from models.product_models import ProductCreate, ProductUpdate
from services.product_service import product_service

logger = structlog.get_logger(__name__)


class ProductFlowState(str, Enum):
    """Estados do fluxo de cadastro de produtos"""
    IDLE = "idle"  # Aguardando comando
    AWAITING_NAME = "awaiting_name"
    AWAITING_DESCRIPTION = "awaiting_description"
    AWAITING_PRICE = "awaiting_price"
    AWAITING_STOCK = "awaiting_stock"
    AWAITING_SKU = "awaiting_sku"
    AWAITING_CATEGORY = "awaiting_category"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_UPDATE_FIELD = "awaiting_update_field"
    AWAITING_UPDATE_VALUE = "awaiting_update_value"
    AWAITING_DELETE_CONFIRMATION = "awaiting_delete_confirmation"


class ProductConversationFlow:
    """Gerencia o fluxo conversacional para CRUD de produtos"""
    
    def __init__(self):
        # Armazena o estado atual de cada usuário
        self.user_states: Dict[str, ProductFlowState] = {}
        # Armazena dados temporários durante o cadastro
        self.user_data: Dict[str, Dict[str, Any]] = {}
        # Armazena o produto sendo editado
        self.user_editing: Dict[str, int] = {}
    
    def get_state(self, user_id: str) -> ProductFlowState:
        """Retorna o estado atual do usuário"""
        return self.user_states.get(user_id, ProductFlowState.IDLE)
    
    def set_state(self, user_id: str, state: ProductFlowState):
        """Define o estado do usuário"""
        self.user_states[user_id] = state
        logger.info(f"Estado do usuário {user_id} alterado para {state.value}")
    
    def reset_user(self, user_id: str):
        """Reseta o estado e dados do usuário"""
        self.user_states.pop(user_id, None)
        self.user_data.pop(user_id, None)
        self.user_editing.pop(user_id, None)
        logger.info(f"Estado do usuário {user_id} resetado")
    
    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Retorna os dados temporários do usuário"""
        return self.user_data.get(user_id, {})
    
    def set_user_data(self, user_id: str, data: Dict[str, Any]):
        """Define dados temporários do usuário"""
        if user_id not in self.user_data:
            self.user_data[user_id] = {}
        self.user_data[user_id].update(data)
    
    async def process_message(
        self, 
        user_id: str, 
        message: str
    ) -> Dict[str, Any]:
        """
        Processa mensagem do usuário e retorna resposta e próximo estado
        Retorna: {
            "response": str,
            "state": ProductFlowState,
            "completed": bool,
            "product": Optional[ProductResponse]
        }
        """
        message_lower = message.lower().strip()
        state = self.get_state(user_id)
        
        # Comandos principais
        if message_lower in ["/produto", "/cadastrar", "/novo produto", "cadastrar produto"]:
            return await self._start_create_flow(user_id)
        
        if message_lower in ["/listar", "/produtos", "listar produtos", "meus produtos"]:
            return await self._list_products(user_id)
        
        if message_lower in ["/editar", "/atualizar", "editar produto"]:
            return await self._start_edit_flow(user_id)
        
        if message_lower in ["/deletar", "/remover", "deletar produto"]:
            return await self._start_delete_flow(user_id)
        
        if message_lower in ["/cancelar", "cancelar", "sair"]:
            return await self._cancel_flow(user_id)
        
        # Processamento baseado no estado atual
        if state == ProductFlowState.AWAITING_NAME:
            return await self._handle_name(user_id, message)
        
        elif state == ProductFlowState.AWAITING_DESCRIPTION:
            return await self._handle_description(user_id, message)
        
        elif state == ProductFlowState.AWAITING_PRICE:
            return await self._handle_price(user_id, message)
        
        elif state == ProductFlowState.AWAITING_STOCK:
            return await self._handle_stock(user_id, message)
        
        elif state == ProductFlowState.AWAITING_SKU:
            return await self._handle_sku(user_id, message)
        
        elif state == ProductFlowState.AWAITING_CATEGORY:
            return await self._handle_category(user_id, message)
        
        elif state == ProductFlowState.AWAITING_CONFIRMATION:
            return await self._handle_confirmation(user_id, message)
        
        elif state == ProductFlowState.AWAITING_UPDATE_FIELD:
            return await self._handle_update_field(user_id, message)
        
        elif state == ProductFlowState.AWAITING_UPDATE_VALUE:
            return await self._handle_update_value(user_id, message)
        
        elif state == ProductFlowState.AWAITING_DELETE_CONFIRMATION:
            return await self._handle_delete_confirmation(user_id, message)
        
        # Estado IDLE - não está em nenhum fluxo
        return {
            "response": (
                "Olá! Como posso ajudar com produtos?\n\n"
                "Comandos disponíveis:\n"
                "/produto - Cadastrar novo produto\n"
                "/listar - Listar meus produtos\n"
                "/editar - Editar um produto\n"
                "/deletar - Deletar um produto\n"
                "/cancelar - Cancelar operação atual"
            ),
            "state": ProductFlowState.IDLE,
            "completed": False,
            "product": None
        }
    
    async def _start_create_flow(self, user_id: str) -> Dict[str, Any]:
        """Inicia fluxo de criação de produto"""
        self.reset_user(user_id)
        self.set_state(user_id, ProductFlowState.AWAITING_NAME)
        return {
            "response": (
                "Vamos cadastrar um novo produto!\n\n"
                "Por favor, informe o NOME do produto:"
            ),
            "state": ProductFlowState.AWAITING_NAME,
            "completed": False,
            "product": None
        }
    
    async def _handle_name(self, user_id: str, message: str) -> Dict[str, Any]:
        """Processa nome do produto"""
        if len(message.strip()) < 2:
            return {
                "response": "Nome muito curto. Por favor, informe um nome válido:",
                "state": ProductFlowState.AWAITING_NAME,
                "completed": False,
                "product": None
            }
        
        self.set_user_data(user_id, {"name": message.strip()})
        self.set_state(user_id, ProductFlowState.AWAITING_DESCRIPTION)
        return {
            "response": (
                f"Ótimo! Nome: {message.strip()}\n\n"
                "Agora informe a DESCRIÇÃO do produto (ou digite 'pular' para pular):"
            ),
            "state": ProductFlowState.AWAITING_DESCRIPTION,
            "completed": False,
            "product": None
        }
    
    async def _handle_description(self, user_id: str, message: str) -> Dict[str, Any]:
        """Processa descrição do produto"""
        if message.lower() != "pular":
            self.set_user_data(user_id, {"description": message.strip()})
        else:
            self.set_user_data(user_id, {"description": None})
        
        self.set_state(user_id, ProductFlowState.AWAITING_PRICE)
        return {
            "response": "Agora informe o PREÇO do produto (ex: 99.90):",
            "state": ProductFlowState.AWAITING_PRICE,
            "completed": False,
            "product": None
        }
    
    async def _handle_price(self, user_id: str, message: str) -> Dict[str, Any]:
        """Processa preço do produto"""
        try:
            price = float(message.replace(",", ".").strip())
            if price <= 0:
                return {
                    "response": "Preço deve ser maior que zero. Informe novamente:",
                    "state": ProductFlowState.AWAITING_PRICE,
                    "completed": False,
                    "product": None
                }
            
            self.set_user_data(user_id, {"price": price})
            self.set_state(user_id, ProductFlowState.AWAITING_STOCK)
            return {
                "response": (
                    f"Preço: R$ {price:.2f}\n\n"
                    "Agora informe a QUANTIDADE EM ESTOQUE (ou digite '0'):"
                ),
                "state": ProductFlowState.AWAITING_STOCK,
                "completed": False,
                "product": None
            }
        except ValueError:
            return {
                "response": "Preço inválido. Informe um número (ex: 99.90):",
                "state": ProductFlowState.AWAITING_PRICE,
                "completed": False,
                "product": None
            }
    
    async def _handle_stock(self, user_id: str, message: str) -> Dict[str, Any]:
        """Processa estoque do produto"""
        try:
            stock = int(message.strip())
            if stock < 0:
                return {
                    "response": "Quantidade não pode ser negativa. Informe novamente:",
                    "state": ProductFlowState.AWAITING_STOCK,
                    "completed": False,
                    "product": None
                }
            
            self.set_user_data(user_id, {"stock_quantity": stock})
            self.set_state(user_id, ProductFlowState.AWAITING_SKU)
            return {
                "response": (
                    f"Estoque: {stock} unidades\n\n"
                    "Agora informe o SKU do produto (ou digite 'pular' para pular):"
                ),
                "state": ProductFlowState.AWAITING_SKU,
                "completed": False,
                "product": None
            }
        except ValueError:
            return {
                "response": "Quantidade inválida. Informe um número inteiro:",
                "state": ProductFlowState.AWAITING_STOCK,
                "completed": False,
                "product": None
            }
    
    async def _handle_sku(self, user_id: str, message: str) -> Dict[str, Any]:
        """Processa SKU do produto"""
        if message.lower() != "pular":
            self.set_user_data(user_id, {"sku": message.strip()})
        else:
            self.set_user_data(user_id, {"sku": None})
        
        self.set_state(user_id, ProductFlowState.AWAITING_CATEGORY)
        return {
            "response": "Agora informe a CATEGORIA do produto (ou digite 'pular' para pular):",
            "state": ProductFlowState.AWAITING_CATEGORY,
            "completed": False,
            "product": None
        }
    
    async def _handle_category(self, user_id: str, message: str) -> Dict[str, Any]:
        """Processa categoria do produto"""
        if message.lower() != "pular":
            self.set_user_data(user_id, {"category": message.strip()})
        else:
            self.set_user_data(user_id, {"category": None})
        
        # Todos os dados coletados, pede confirmação
        data = self.get_user_data(user_id)
        self.set_state(user_id, ProductFlowState.AWAITING_CONFIRMATION)
        
        summary = (
            f"Resumo do produto:\n\n"
            f"Nome: {data.get('name')}\n"
            f"Descrição: {data.get('description', 'Não informada')}\n"
            f"Preço: R$ {data.get('price', 0):.2f}\n"
            f"Estoque: {data.get('stock_quantity', 0)} unidades\n"
            f"SKU: {data.get('sku', 'Não informado')}\n"
            f"Categoria: {data.get('category', 'Não informada')}\n\n"
            "Confirma o cadastro? (sim/não)"
        )
        
        return {
            "response": summary,
            "state": ProductFlowState.AWAITING_CONFIRMATION,
            "completed": False,
            "product": None
        }
    
    async def _handle_confirmation(self, user_id: str, message: str) -> Dict[str, Any]:
        """Processa confirmação de cadastro"""
        if message.lower() in ["sim", "s", "yes", "y", "confirmar"]:
            data = self.get_user_data(user_id)
            try:
                product_create = ProductCreate(**data)
                product = await product_service.create_product(product_create, user_id)
                
                self.reset_user(user_id)
                
                return {
                    "response": (
                        f"✅ Produto cadastrado com sucesso!\n\n"
                        f"ID: {product.id}\n"
                        f"Nome: {product.name}\n"
                        f"Preço: R$ {product.price:.2f}\n\n"
                        "Deseja cadastrar outro produto? (/produto)"
                    ),
                    "state": ProductFlowState.IDLE,
                    "completed": True,
                    "product": product
                }
            except Exception as e:
                logger.error(f"Erro ao criar produto: {e}", exc_info=True)
                return {
                    "response": f"❌ Erro ao cadastrar produto: {str(e)}\n\nTente novamente com /produto",
                    "state": ProductFlowState.IDLE,
                    "completed": False,
                    "product": None
                }
        else:
            self.reset_user(user_id)
            return {
                "response": "Cadastro cancelado. Use /produto para começar novamente.",
                "state": ProductFlowState.IDLE,
                "completed": False,
                "product": None
            }
    
    async def _list_products(self, user_id: str) -> Dict[str, Any]:
        """Lista produtos do usuário"""
        try:
            products = await product_service.list_products(user_id=user_id, is_active=True)
            
            if not products:
                return {
                    "response": "Você ainda não tem produtos cadastrados.\n\nUse /produto para cadastrar.",
                    "state": ProductFlowState.IDLE,
                    "completed": False,
                    "product": None
                }
            
            response = f"📦 Seus produtos ({len(products)}):\n\n"
            for p in products[:10]:  # Limita a 10 produtos
                response += (
                    f"ID: {p.id} | {p.name}\n"
                    f"Preço: R$ {p.price:.2f} | Estoque: {p.stock_quantity}\n"
                    f"SKU: {p.sku or 'N/A'} | Categoria: {p.category or 'N/A'}\n\n"
                )
            
            if len(products) > 10:
                response += f"... e mais {len(products) - 10} produtos."
            
            return {
                "response": response,
                "state": ProductFlowState.IDLE,
                "completed": False,
                "product": None
            }
        except Exception as e:
            logger.error(f"Erro ao listar produtos: {e}", exc_info=True)
            return {
                "response": f"❌ Erro ao listar produtos: {str(e)}",
                "state": ProductFlowState.IDLE,
                "completed": False,
                "product": None
            }
    
    async def _start_edit_flow(self, user_id: str) -> Dict[str, Any]:
        """Inicia fluxo de edição"""
        try:
            products = await product_service.list_products(user_id=user_id, is_active=True)
            
            if not products:
                return {
                    "response": "Você não tem produtos para editar.\n\nUse /produto para cadastrar.",
                    "state": ProductFlowState.IDLE,
                    "completed": False,
                    "product": None
                }
            
            response = "Qual produto deseja editar? Informe o ID:\n\n"
            for p in products[:10]:
                response += f"ID {p.id}: {p.name} - R$ {p.price:.2f}\n"
            
            self.set_state(user_id, ProductFlowState.AWAITING_UPDATE_FIELD)
            return {
                "response": response,
                "state": ProductFlowState.AWAITING_UPDATE_FIELD,
                "completed": False,
                "product": None
            }
        except Exception as e:
            logger.error(f"Erro ao iniciar edição: {e}", exc_info=True)
            return {
                "response": f"❌ Erro: {str(e)}",
                "state": ProductFlowState.IDLE,
                "completed": False,
                "product": None
            }
    
    async def _handle_update_field(self, user_id: str, message: str) -> Dict[str, Any]:
        """Processa seleção de produto para editar"""
        try:
            product_id = int(message.strip())
            product = await product_service.get_product(product_id)
            
            if not product or product.created_by != user_id:
                return {
                    "response": "Produto não encontrado ou não pertence a você. Tente novamente:",
                    "state": ProductFlowState.AWAITING_UPDATE_FIELD,
                    "completed": False,
                    "product": None
                }
            
            self.user_editing[user_id] = product_id
            self.set_state(user_id, ProductFlowState.AWAITING_UPDATE_VALUE)
            
            return {
                "response": (
                    f"Editando produto: {product.name}\n\n"
                    "Qual campo deseja editar?\n"
                    "1. Nome\n"
                    "2. Descrição\n"
                    "3. Preço\n"
                    "4. Estoque\n"
                    "5. SKU\n"
                    "6. Categoria\n\n"
                    "Digite o número ou nome do campo:"
                ),
                "state": ProductFlowState.AWAITING_UPDATE_VALUE,
                "completed": False,
                "product": product
            }
        except ValueError:
            return {
                "response": "ID inválido. Informe um número:",
                "state": ProductFlowState.AWAITING_UPDATE_FIELD,
                "completed": False,
                "product": None
            }
    
    async def _handle_update_value(self, user_id: str, message: str) -> Dict[str, Any]:
        """Processa atualização de campo"""
        product_id = self.user_editing.get(user_id)
        if not product_id:
            self.reset_user(user_id)
            return {
                "response": "Sessão expirada. Use /editar para começar novamente.",
                "state": ProductFlowState.IDLE,
                "completed": False,
                "product": None
            }
        
        user_data = self.get_user_data(user_id)
        update_field = user_data.get("update_field")
        
        # Se ainda não escolheu o campo, processa escolha
        if not update_field:
            field_map = {
                "1": "name", "nome": "name",
                "2": "description", "descrição": "description", "descricao": "description",
                "3": "price", "preço": "price", "preco": "price",
                "4": "stock_quantity", "estoque": "stock_quantity",
                "5": "sku", "SKU": "sku",
                "6": "category", "categoria": "category"
            }
            
            field = field_map.get(message.lower().strip())
            if not field:
                return {
                    "response": "Campo inválido. Escolha 1-6 ou digite o nome do campo:",
                    "state": ProductFlowState.AWAITING_UPDATE_VALUE,
                    "completed": False,
                    "product": None
                }
            
            # Salva o campo escolhido e pede o valor
            self.set_user_data(user_id, {"update_field": field})
            field_names = {
                "name": "nome",
                "description": "descrição",
                "price": "preço",
                "stock_quantity": "quantidade em estoque",
                "sku": "SKU",
                "category": "categoria"
            }
            
            return {
                "response": f"Informe o novo valor para {field_names.get(field, field)}:",
                "state": ProductFlowState.AWAITING_UPDATE_VALUE,
                "completed": False,
                "product": None
            }
        
        # Já tem o campo, processa o valor
        try:
            update_data = {}
            
            if update_field == "price":
                value = float(message.replace(",", ".").strip())
                if value <= 0:
                    return {
                        "response": "Preço deve ser maior que zero. Informe novamente:",
                        "state": ProductFlowState.AWAITING_UPDATE_VALUE,
                        "completed": False,
                        "product": None
                    }
                update_data["price"] = value
            elif update_field == "stock_quantity":
                value = int(message.strip())
                if value < 0:
                    return {
                        "response": "Quantidade não pode ser negativa. Informe novamente:",
                        "state": ProductFlowState.AWAITING_UPDATE_VALUE,
                        "completed": False,
                        "product": None
                    }
                update_data["stock_quantity"] = value
            elif update_field == "name":
                if len(message.strip()) < 2:
                    return {
                        "response": "Nome muito curto. Informe novamente:",
                        "state": ProductFlowState.AWAITING_UPDATE_VALUE,
                        "completed": False,
                        "product": None
                    }
                update_data["name"] = message.strip()
            else:
                update_data[update_field] = message.strip() if message.strip() else None
            
            # Atualiza o produto
            product_update = ProductUpdate(**update_data)
            updated_product = await product_service.update_product(
                product_id, 
                product_update, 
                user_id
            )
            
            if updated_product:
                self.reset_user(user_id)
                return {
                    "response": (
                        f"✅ Produto atualizado com sucesso!\n\n"
                        f"ID: {updated_product.id}\n"
                        f"Nome: {updated_product.name}\n"
                        f"Preço: R$ {updated_product.price:.2f}\n\n"
                        "Deseja editar outro produto? (/editar)"
                    ),
                    "state": ProductFlowState.IDLE,
                    "completed": True,
                    "product": updated_product
                }
            else:
                self.reset_user(user_id)
                return {
                    "response": "❌ Erro ao atualizar produto. Produto não encontrado ou não pertence a você.",
                    "state": ProductFlowState.IDLE,
                    "completed": False,
                    "product": None
                }
        except ValueError as e:
            return {
                "response": f"Valor inválido. {str(e)}\n\nInforme novamente:",
                "state": ProductFlowState.AWAITING_UPDATE_VALUE,
                "completed": False,
                "product": None
            }
        except Exception as e:
            logger.error(f"Erro ao atualizar produto: {e}", exc_info=True)
            self.reset_user(user_id)
            return {
                "response": f"❌ Erro ao atualizar produto: {str(e)}",
                "state": ProductFlowState.IDLE,
                "completed": False,
                "product": None
            }
    
    async def _start_delete_flow(self, user_id: str) -> Dict[str, Any]:
        """Inicia fluxo de deleção"""
        try:
            products = await product_service.list_products(user_id=user_id, is_active=True)
            
            if not products:
                return {
                    "response": "Você não tem produtos para deletar.",
                    "state": ProductFlowState.IDLE,
                    "completed": False,
                    "product": None
                }
            
            response = "Qual produto deseja deletar? Informe o ID:\n\n"
            for p in products[:10]:
                response += f"ID {p.id}: {p.name} - R$ {p.price:.2f}\n"
            
            self.set_state(user_id, ProductFlowState.AWAITING_DELETE_CONFIRMATION)
            return {
                "response": response,
                "state": ProductFlowState.AWAITING_DELETE_CONFIRMATION,
                "completed": False,
                "product": None
            }
        except Exception as e:
            logger.error(f"Erro ao iniciar deleção: {e}", exc_info=True)
            return {
                "response": f"❌ Erro: {str(e)}",
                "state": ProductFlowState.IDLE,
                "completed": False,
                "product": None
            }
    
    async def _handle_delete_confirmation(self, user_id: str, message: str) -> Dict[str, Any]:
        """Processa confirmação de deleção"""
        try:
            product_id = int(message.strip())
            product = await product_service.get_product(product_id)
            
            if not product or product.created_by != user_id:
                return {
                    "response": "Produto não encontrado. Informe um ID válido:",
                    "state": ProductFlowState.AWAITING_DELETE_CONFIRMATION,
                    "completed": False,
                    "product": None
                }
            
            # Pede confirmação
            if "confirmar" not in self.get_user_data(user_id):
                self.set_user_data(user_id, {"delete_id": product_id, "confirmar": False})
                return {
                    "response": (
                        f"Tem certeza que deseja deletar o produto?\n\n"
                        f"ID: {product.id}\n"
                        f"Nome: {product.name}\n"
                        f"Preço: R$ {product.price:.2f}\n\n"
                        "Digite 'sim' para confirmar ou 'não' para cancelar:"
                    ),
                    "state": ProductFlowState.AWAITING_DELETE_CONFIRMATION,
                    "completed": False,
                    "product": product
                }
            
            # Confirma deleção
            if message.lower() in ["sim", "s", "yes", "y"]:
                success = await product_service.delete_product(product_id, user_id)
                self.reset_user(user_id)
                
                if success:
                    return {
                        "response": f"✅ Produto {product.name} deletado com sucesso!",
                        "state": ProductFlowState.IDLE,
                        "completed": True,
                        "product": None
                    }
                else:
                    return {
                        "response": "❌ Erro ao deletar produto.",
                        "state": ProductFlowState.IDLE,
                        "completed": False,
                        "product": None
                    }
            else:
                self.reset_user(user_id)
                return {
                    "response": "Deleção cancelada.",
                    "state": ProductFlowState.IDLE,
                    "completed": False,
                    "product": None
                }
        except ValueError:
            data = self.get_user_data(user_id)
            if "delete_id" in data:
                # Já tem ID, está esperando confirmação
                if message.lower() in ["sim", "s", "yes", "y"]:
                    product_id = data["delete_id"]
                    success = await product_service.delete_product(product_id, user_id)
                    self.reset_user(user_id)
                    return {
                        "response": "✅ Produto deletado com sucesso!" if success else "❌ Erro ao deletar.",
                        "state": ProductFlowState.IDLE,
                        "completed": success,
                        "product": None
                    }
                else:
                    self.reset_user(user_id)
                    return {
                        "response": "Deleção cancelada.",
                        "state": ProductFlowState.IDLE,
                        "completed": False,
                        "product": None
                    }
            return {
                "response": "ID inválido. Informe um número:",
                "state": ProductFlowState.AWAITING_DELETE_CONFIRMATION,
                "completed": False,
                "product": None
            }
    
    async def _cancel_flow(self, user_id: str) -> Dict[str, Any]:
        """Cancela fluxo atual"""
        self.reset_user(user_id)
        return {
            "response": "Operação cancelada. Como posso ajudar?",
            "state": ProductFlowState.IDLE,
            "completed": False,
            "product": None
        }


# Instância global do fluxo
product_flow = ProductConversationFlow()
