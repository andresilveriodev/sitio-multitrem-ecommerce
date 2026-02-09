"""
Comandos para processamento de pedidos e entregas
"""

from typing import Dict, Any
import structlog
from .types import CommandResult
from services.order_service import order_service
from models.order_models import (
    OrderItem, DeliveryAddress, PaymentMethod, OrderStatus
)

logger = structlog.get_logger(__name__)


async def create_order_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para criar um novo pedido"""
    try:
        user_id = params.get('user_id')
        items_data = params.get('items', [])
        delivery_address_data = params.get('delivery_address')
        notes = params.get('notes')
        payment_method_str = params.get('payment_method')
        
        if not user_id:
            return CommandResult(
                success=False,
                message="ID do usuário é obrigatório",
                error="user_id_required"
            )
        
        if not items_data or len(items_data) == 0:
            return CommandResult(
                success=False,
                message="É necessário adicionar pelo menos um item ao pedido",
                error="items_required"
            )
        
        # Converte itens
        items = []
        for item_data in items_data:
            item = OrderItem(
                product_id=item_data.get('product_id', ''),
                product_name=item_data.get('product_name', 'Produto'),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price', 0.0),
                total_price=item_data.get('total_price', item_data.get('unit_price', 0.0) * item_data.get('quantity', 1)),
                notes=item_data.get('notes')
            )
            items.append(item)
        
        # Converte endereço de entrega se fornecido
        delivery_address = None
        if delivery_address_data:
            delivery_address = DeliveryAddress(
                street=delivery_address_data.get('street', ''),
                number=delivery_address_data.get('number', ''),
                complement=delivery_address_data.get('complement'),
                neighborhood=delivery_address_data.get('neighborhood', ''),
                city=delivery_address_data.get('city', ''),
                state=delivery_address_data.get('state', ''),
                zip_code=delivery_address_data.get('zip_code', ''),
                reference=delivery_address_data.get('reference')
            )
        
        # Converte método de pagamento
        payment_method = None
        if payment_method_str:
            try:
                payment_method = PaymentMethod(payment_method_str)
            except ValueError:
                payment_method = PaymentMethod.OTHER
        
        # Cria pedido
        order = await order_service.create_order(
            user_id=user_id,
            items=items,
            delivery_address=delivery_address,
            notes=notes,
            payment_method=payment_method
        )
        
        return CommandResult(
            success=True,
            message=f"Pedido {order.order_number} criado com sucesso! Total: R$ {order.total_amount:.2f}",
            data={
                "order_id": order.id,
                "order_number": order.order_number,
                "total_amount": order.total_amount,
                "status": order.status.value,
                "action": "show_order",
                "target": "frontend"
            }
        )
        
    except Exception as e:
        logger.error("Erro ao criar pedido", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao criar pedido",
            error=str(e)
        )


async def view_order_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para visualizar um pedido"""
    try:
        order_id = params.get('order_id')
        order_number = params.get('order_number')
        
        if not order_id and not order_number:
            return CommandResult(
                success=False,
                message="ID ou número do pedido é obrigatório",
                error="order_id_or_number_required"
            )
        
        # Busca pedido
        if order_id:
            order = await order_service.get_order(order_id)
        else:
            order = await order_service.get_order_by_number(order_number)
        
        if not order:
            return CommandResult(
                success=False,
                message="Pedido não encontrado",
                error="order_not_found"
            )
        
        # Busca etapas do pedido
        stages = await order_service.get_order_stages(order.id)
        
        return CommandResult(
            success=True,
            message=f"Pedido {order.order_number} - Status: {order.status.value}",
            data={
                "order": order.dict(),
                "stages": [stage.dict() for stage in stages],
                "action": "show_order_details",
                "target": "frontend"
            }
        )
        
    except Exception as e:
        logger.error("Erro ao visualizar pedido", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao buscar pedido",
            error=str(e)
        )


async def list_orders_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para listar pedidos do usuário"""
    try:
        user_id = params.get('user_id')
        status_str = params.get('status')
        limit = params.get('limit', 10)
        
        if not user_id:
            return CommandResult(
                success=False,
                message="ID do usuário é obrigatório",
                error="user_id_required"
            )
        
        # Converte status se fornecido
        status = None
        if status_str:
            try:
                status = OrderStatus(status_str)
            except ValueError:
                pass
        
        # Busca pedidos
        orders = await order_service.get_user_orders(
            user_id=user_id,
            status=status,
            limit=limit
        )
        
        return CommandResult(
            success=True,
            message=f"Encontrados {len(orders)} pedido(s)",
            data={
                "orders": [order.dict() for order in orders],
                "count": len(orders),
                "action": "show_orders_list",
                "target": "frontend"
            }
        )
        
    except Exception as e:
        logger.error("Erro ao listar pedidos", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao buscar pedidos",
            error=str(e)
        )


async def track_order_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para acompanhar pedido"""
    try:
        order_id = params.get('order_id')
        order_number = params.get('order_number')
        
        if not order_id and not order_number:
            return CommandResult(
                success=False,
                message="ID ou número do pedido é obrigatório",
                error="order_id_or_number_required"
            )
        
        # Busca pedido
        if order_id:
            order = await order_service.get_order(order_id)
        else:
            order = await order_service.get_order_by_number(order_number)
        
        if not order:
            return CommandResult(
                success=False,
                message="Pedido não encontrado",
                error="order_not_found"
            )
        
        # Busca etapas
        stages = await order_service.get_order_stages(order.id)
        
        # Processa com IA para gerar resposta mais natural
        ai_response = await order_service.process_order_with_ai(
            order_id=order.id,
            user_message="Como está meu pedido?",
            context={"action": "track"}
        )
        
        tracking_message = ai_response.get("response", f"Pedido {order.order_number} - Status: {order.status.value}")
        
        return CommandResult(
            success=True,
            message=tracking_message,
            data={
                "order": order.dict(),
                "stages": [stage.dict() for stage in stages],
                "action": "show_order_tracking",
                "target": "frontend"
            }
        )
        
    except Exception as e:
        logger.error("Erro ao acompanhar pedido", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao acompanhar pedido",
            error=str(e)
        )


async def update_order_stage_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para atualizar etapa do pedido"""
    try:
        order_id = params.get('order_id')
        stage = params.get('stage')
        
        if not order_id:
            return CommandResult(
                success=False,
                message="ID do pedido é obrigatório",
                error="order_id_required"
            )
        
        if not stage:
            return CommandResult(
                success=False,
                message="Etapa é obrigatória",
                error="stage_required"
            )
        
        # Avança etapa
        order = await order_service.advance_order_stage(order_id, stage)
        
        if not order:
            return CommandResult(
                success=False,
                message="Pedido não encontrado",
                error="order_not_found"
            )
        
        return CommandResult(
            success=True,
            message=f"Pedido {order.order_number} atualizado para etapa: {stage}",
            data={
                "order_id": order.id,
                "order_number": order.order_number,
                "status": order.status.value,
                "stage": stage,
                "action": "update_order",
                "target": "frontend"
            }
        )
        
    except Exception as e:
        logger.error("Erro ao atualizar etapa do pedido", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao atualizar etapa do pedido",
            error=str(e)
        )


async def cancel_order_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para cancelar pedido"""
    try:
        order_id = params.get('order_id')
        
        if not order_id:
            return CommandResult(
                success=False,
                message="ID do pedido é obrigatório",
                error="order_id_required"
            )
        
        # Cancela pedido
        order = await order_service.cancel_order(order_id)
        
        if not order:
            return CommandResult(
                success=False,
                message="Pedido não encontrado",
                error="order_not_found"
            )
        
        return CommandResult(
            success=True,
            message=f"Pedido {order.order_number} cancelado com sucesso",
            data={
                "order_id": order.id,
                "order_number": order.order_number,
                "status": order.status.value,
                "action": "update_order",
                "target": "frontend"
            }
        )
        
    except Exception as e:
        logger.error("Erro ao cancelar pedido", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao cancelar pedido",
            error=str(e)
        )


async def process_order_with_ai_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para processar pedido com IA"""
    try:
        order_id = params.get('order_id')
        user_message = params.get('message', '')
        context = params.get('context', {})
        
        if not order_id:
            return CommandResult(
                success=False,
                message="ID do pedido é obrigatório",
                error="order_id_required"
            )
        
        # Processa com IA
        result = await order_service.process_order_with_ai(
            order_id=order_id,
            user_message=user_message,
            context=context
        )
        
        if not result.get("success"):
            return CommandResult(
                success=False,
                message=result.get("error", "Erro ao processar pedido"),
                error=result.get("error")
            )
        
        # Executa ações sugeridas pela IA
        actions = result.get("actions", [])
        for action in actions:
            if action.get("type") == "update_stage":
                await order_service.advance_order_stage(
                    order_id,
                    action.get("stage")
                )
        
        return CommandResult(
            success=True,
            message=result.get("response", "Pedido processado"),
            data={
                "order_id": order_id,
                "response": result.get("response"),
                "actions": actions,
                "order": result.get("order"),
                "action": "process_order_ai",
                "target": "frontend"
            }
        )
        
    except Exception as e:
        logger.error("Erro ao processar pedido com IA", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao processar pedido com IA",
            error=str(e)
        )
