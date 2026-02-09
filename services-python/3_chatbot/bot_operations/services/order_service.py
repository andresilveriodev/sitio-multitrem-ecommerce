"""
Serviço para gerenciamento de pedidos e entregas
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import structlog
from enum import Enum

from models.order_models import (
    Order, OrderStatus, OrderItem, DeliveryAddress,
    PaymentStatus, PaymentMethod, OrderStage, OrderUpdate, OrderQuery
)
from services.ai_integration import ai_integration

logger = structlog.get_logger(__name__)


class OrderService:
    """Serviço para gerenciar pedidos e entregas"""
    
    def __init__(self):
        # Em produção, isso seria um banco de dados
        # Por enquanto, usamos um dicionário em memória
        self.orders: Dict[str, Order] = {}
        self.order_stages: Dict[str, List[OrderStage]] = {}
        self.order_counter = 0
    
    def _generate_order_number(self) -> str:
        """Gera número único do pedido"""
        self.order_counter += 1
        year = datetime.utcnow().year
        return f"PED-{year}-{self.order_counter:04d}"
    
    async def create_order(
        self,
        user_id: str,
        items: List[OrderItem],
        delivery_address: Optional[DeliveryAddress] = None,
        notes: Optional[str] = None,
        payment_method: Optional[PaymentMethod] = None
    ) -> Order:
        """
        Cria um novo pedido
        
        Args:
            user_id: ID do usuário
            items: Lista de itens do pedido
            delivery_address: Endereço de entrega
            notes: Observações do pedido
            payment_method: Método de pagamento
            
        Returns:
            Pedido criado
        """
        try:
            order_id = str(uuid.uuid4())
            order_number = self._generate_order_number()
            
            # Calcula total
            total_amount = sum(item.total_price for item in items)
            
            order = Order(
                id=order_id,
                user_id=user_id,
                order_number=order_number,
                status=OrderStatus.PENDING,
                items=items,
                total_amount=total_amount,
                delivery_address=delivery_address,
                payment_status=PaymentStatus.PENDING,
                payment_method=payment_method,
                notes=notes,
                metadata={
                    "created_by": "chatbot",
                    "source": "telegram" if "telegram" in user_id else "web"
                }
            )
            
            self.orders[order_id] = order
            self.order_stages[order_id] = []
            
            # Inicia etapa de pedido
            await self._add_stage(order_id, "pedido", "completed")
            
            logger.info(
                "Pedido criado",
                order_id=order_id,
                order_number=order_number,
                user_id=user_id,
                total_amount=total_amount,
                items_count=len(items)
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Erro ao criar pedido: {e}", exc_info=True)
            raise
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Busca pedido por ID"""
        return self.orders.get(order_id)
    
    async def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Busca pedido por número"""
        for order in self.orders.values():
            if order.order_number == order_number:
                return order
        return None
    
    async def get_user_orders(
        self,
        user_id: str,
        status: Optional[OrderStatus] = None,
        limit: int = 50
    ) -> List[Order]:
        """Busca pedidos do usuário"""
        orders = [
            order for order in self.orders.values()
            if order.user_id == user_id
        ]
        
        if status:
            orders = [order for order in orders if order.status == status]
        
        # Ordena por data (mais recente primeiro)
        orders.sort(key=lambda x: x.created_at, reverse=True)
        
        return orders[:limit]
    
    async def update_order(
        self,
        order_id: str,
        update: OrderUpdate
    ) -> Optional[Order]:
        """
        Atualiza pedido
        
        Args:
            order_id: ID do pedido
            update: Dados de atualização
            
        Returns:
            Pedido atualizado
        """
        try:
            order = self.orders.get(order_id)
            if not order:
                logger.warning(f"Pedido não encontrado: {order_id}")
                return None
            
            # Atualiza status se fornecido
            if update.status:
                order.status = update.status
            
            # Atualiza status de pagamento se fornecido
            if update.payment_status:
                order.payment_status = update.payment_status
            
            # Atualiza notas se fornecido
            if update.notes:
                order.notes = update.notes
            
            # Atualiza metadados se fornecido
            if update.metadata:
                order.metadata.update(update.metadata)
            
            order.updated_at = datetime.utcnow()
            
            # Se há uma nova etapa, adiciona
            if update.stage:
                await self._add_stage(order_id, update.stage, "in_progress")
            
            logger.info(
                "Pedido atualizado",
                order_id=order_id,
                status=order.status,
                payment_status=order.payment_status
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Erro ao atualizar pedido: {e}", exc_info=True)
            raise
    
    async def process_order_with_ai(
        self,
        order_id: str,
        user_message: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Processa pedido usando IA para entender intenções e atualizar status
        
        Args:
            order_id: ID do pedido
            user_message: Mensagem do usuário
            context: Contexto adicional
            
        Returns:
            Resposta da IA e ações a serem executadas
        """
        try:
            order = await self.get_order(order_id)
            if not order:
                return {
                    "success": False,
                    "error": "Pedido não encontrado"
                }
            
            # Prepara contexto para a IA
            ai_context = {
                "order_id": order_id,
                "order_number": order.order_number,
                "order_status": order.status.value,
                "payment_status": order.payment_status.value,
                "total_amount": order.total_amount,
                "items": [
                    {
                        "product_name": item.product_name,
                        "quantity": item.quantity,
                        "total_price": item.total_price
                    }
                    for item in order.items
                ],
                "current_stages": await self.get_order_stages(order_id),
                "user_message": user_message
            }
            
            if context:
                ai_context.update(context)
            
            # Cria prompt para a IA processar o pedido
            prompt = self._create_order_processing_prompt(order, user_message, ai_context)
            
            # Chama IA para processar
            ai_response = await ai_integration.generate_response(
                user_id=order.user_id,
                message=prompt,
                context_summary=f"Processando pedido {order.order_number}. Status: {order.status.value}",
                user_preferences=None
            )
            
            if not ai_response:
                return {
                    "success": False,
                    "error": "Erro ao processar com IA"
                }
            
            # Extrai ações da resposta da IA
            actions = self._extract_actions_from_ai_response(
                ai_response.get("response", ""),
                order
            )
            
            return {
                "success": True,
                "response": ai_response.get("response", ""),
                "actions": actions,
                "order": order.dict()
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar pedido com IA: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_order_processing_prompt(
        self,
        order: Order,
        user_message: str,
        context: Dict
    ) -> str:
        """Cria prompt para a IA processar o pedido"""
        stages_info = "\n".join([
            f"- {stage.stage}: {stage.status}"
            for stage in context.get("current_stages", [])
        ])
        
        prompt = f"""
Você é um assistente de e-commerce especializado em processar pedidos e gerenciar entregas.

PEDIDO ATUAL:
- Número: {order.order_number}
- Status: {order.status.value}
- Status de Pagamento: {order.payment_status.value}
- Valor Total: R$ {order.total_amount:.2f}
- Itens: {len(order.items)} item(s)

ETAPAS DO PROCESSO:
{stages_info}

MENSAGEM DO USUÁRIO:
{user_message}

INSTRUÇÕES:
1. Analise a mensagem do usuário e determine a intenção
2. Identifique se o usuário quer:
   - Acompanhar o pedido
   - Atualizar informações
   - Cancelar o pedido
   - Verificar status de pagamento
   - Solicitar informações sobre entrega
   - Outra ação relacionada ao pedido

3. Se necessário, sugira próximas etapas do processo:
   - pedido: Pedido criado
   - colheita: Colheita dos produtos (se aplicável)
   - compra_fornecedor: Compra no fornecedor (se necessário)
   - separacao: Separação dos produtos
   - envio: Envio do pedido
   - pagamento: Processamento do pagamento

4. Responda de forma clara e amigável, fornecendo informações úteis sobre o pedido.

Responda em português brasileiro.
"""
        return prompt
    
    def _extract_actions_from_ai_response(
        self,
        ai_response: str,
        order: Order
    ) -> List[Dict[str, Any]]:
        """
        Extrai ações da resposta da IA
        Por enquanto, retorna ações básicas baseadas em palavras-chave
        Em produção, a IA poderia retornar JSON estruturado
        """
        actions = []
        response_lower = ai_response.lower()
        
        # Detecta intenção de atualizar status
        if "próxima etapa" in response_lower or "avançar" in response_lower:
            next_stage = self._get_next_stage(order.status)
            if next_stage:
                actions.append({
                    "type": "update_stage",
                    "stage": next_stage,
                    "order_id": order.id
                })
        
        # Detecta intenção de cancelar
        if "cancelar" in response_lower or "cancelamento" in response_lower:
            actions.append({
                "type": "cancel_order",
                "order_id": order.id
            })
        
        return actions
    
    def _get_next_stage(self, current_status: OrderStatus) -> Optional[str]:
        """Determina próxima etapa baseado no status atual"""
        stage_mapping = {
            OrderStatus.PENDING: "pagamento",
            OrderStatus.PAYMENT_CONFIRMED: "colheita",
            OrderStatus.IN_HARVEST: "separacao",
            OrderStatus.IN_PURCHASE: "separacao",
            OrderStatus.IN_SEPARATION: "envio",
            OrderStatus.READY_TO_SHIP: "envio",
            OrderStatus.SHIPPED: None,  # Já enviado
        }
        return stage_mapping.get(current_status)
    
    async def _add_stage(
        self,
        order_id: str,
        stage: str,
        status: str
    ):
        """Adiciona etapa ao pedido"""
        if order_id not in self.order_stages:
            self.order_stages[order_id] = []
        
        stage_obj = OrderStage(
            order_id=order_id,
            stage=stage,
            status=status,
            started_at=datetime.utcnow() if status == "in_progress" else None,
            completed_at=datetime.utcnow() if status == "completed" else None
        )
        
        self.order_stages[order_id].append(stage_obj)
    
    async def get_order_stages(self, order_id: str) -> List[OrderStage]:
        """Busca etapas do pedido"""
        return self.order_stages.get(order_id, [])
    
    async def advance_order_stage(
        self,
        order_id: str,
        stage: str
    ) -> Optional[Order]:
        """
        Avança pedido para próxima etapa
        
        Args:
            order_id: ID do pedido
            stage: Nome da etapa (colheita, separacao, envio, etc.)
            
        Returns:
            Pedido atualizado
        """
        try:
            order = await self.get_order(order_id)
            if not order:
                return None
            
            # Mapeia etapa para status
            stage_to_status = {
                "colheita": OrderStatus.IN_HARVEST,
                "compra_fornecedor": OrderStatus.IN_PURCHASE,
                "separacao": OrderStatus.IN_SEPARATION,
                "envio": OrderStatus.READY_TO_SHIP,
                "pagamento": OrderStatus.PAYMENT_PENDING
            }
            
            new_status = stage_to_status.get(stage)
            if new_status:
                await self.update_order(
                    order_id,
                    OrderUpdate(
                        order_id=order_id,
                        status=new_status,
                        stage=stage
                    )
                )
            
            # Marca etapa anterior como completa e inicia nova
            stages = await self.get_order_stages(order_id)
            if stages:
                last_stage = stages[-1]
                if last_stage.status == "in_progress":
                    last_stage.status = "completed"
                    last_stage.completed_at = datetime.utcnow()
            
            await self._add_stage(order_id, stage, "in_progress")
            
            return await self.get_order(order_id)
            
        except Exception as e:
            logger.error(f"Erro ao avançar etapa do pedido: {e}", exc_info=True)
            raise
    
    async def cancel_order(self, order_id: str) -> Optional[Order]:
        """Cancela pedido"""
        return await self.update_order(
            order_id,
            OrderUpdate(
                order_id=order_id,
                status=OrderStatus.CANCELLED
            )
        )


# Instância global do serviço
order_service = OrderService()
