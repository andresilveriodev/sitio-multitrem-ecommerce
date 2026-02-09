"""
Router para operações de pedidos e entregas
"""

import time
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
import structlog

from models.order_models import (
    Order, OrderItem, DeliveryAddress, OrderStatus,
    PaymentStatus, PaymentMethod, OrderUpdate
)
from services.order_service import order_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/create")
async def create_order(request: Request):
    """Cria um novo pedido"""
    try:
        body = await request.json()
        user_id = body.get("user_id")
        items_data = body.get("items", [])
        delivery_address_data = body.get("delivery_address")
        notes = body.get("notes")
        payment_method_str = body.get("payment_method")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id é obrigatório")
        
        if not items_data:
            raise HTTPException(status_code=400, detail="É necessário adicionar pelo menos um item")
        
        # Converte itens
        items = []
        for item_data in items_data:
            item = OrderItem(
                product_id=item_data.get("product_id", ""),
                product_name=item_data.get("product_name", "Produto"),
                quantity=item_data.get("quantity", 1),
                unit_price=item_data.get("unit_price", 0.0),
                total_price=item_data.get("total_price", item_data.get("unit_price", 0.0) * item_data.get("quantity", 1)),
                notes=item_data.get("notes")
            )
            items.append(item)
        
        # Converte endereço se fornecido
        delivery_address = None
        if delivery_address_data:
            delivery_address = DeliveryAddress(**delivery_address_data)
        
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
        
        return {
            "success": True,
            "order": order.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar pedido: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao criar pedido: {str(e)}")


@router.get("/{order_id}")
async def get_order(order_id: str):
    """Busca pedido por ID"""
    try:
        order = await order_service.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
        stages = await order_service.get_order_stages(order_id)
        
        return {
            "success": True,
            "order": order.dict(),
            "stages": [stage.dict() for stage in stages]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar pedido: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar pedido: {str(e)}")


@router.get("/number/{order_number}")
async def get_order_by_number(order_number: str):
    """Busca pedido por número"""
    try:
        order = await order_service.get_order_by_number(order_number)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
        stages = await order_service.get_order_stages(order.id)
        
        return {
            "success": True,
            "order": order.dict(),
            "stages": [stage.dict() for stage in stages]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar pedido: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar pedido: {str(e)}")


@router.get("/user/{user_id}")
async def get_user_orders(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50
):
    """Lista pedidos do usuário"""
    try:
        order_status = None
        if status:
            try:
                order_status = OrderStatus(status)
            except ValueError:
                pass
        
        orders = await order_service.get_user_orders(
            user_id=user_id,
            status=order_status,
            limit=limit
        )
        
        return {
            "success": True,
            "orders": [order.dict() for order in orders],
            "count": len(orders)
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar pedidos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao listar pedidos: {str(e)}")


@router.put("/{order_id}")
async def update_order(order_id: str, request: Request):
    """Atualiza pedido"""
    try:
        body = await request.json()
        
        update = OrderUpdate(
            order_id=order_id,
            status=OrderStatus(body["status"]) if body.get("status") else None,
            payment_status=PaymentStatus(body["payment_status"]) if body.get("payment_status") else None,
            stage=body.get("stage"),
            notes=body.get("notes"),
            metadata=body.get("metadata")
        )
        
        order = await order_service.update_order(order_id, update)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
        return {
            "success": True,
            "order": order.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar pedido: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar pedido: {str(e)}")


@router.post("/{order_id}/advance-stage")
async def advance_order_stage(order_id: str, request: Request):
    """Avança pedido para próxima etapa"""
    try:
        body = await request.json()
        stage = body.get("stage")
        
        if not stage:
            raise HTTPException(status_code=400, detail="stage é obrigatório")
        
        order = await order_service.advance_order_stage(order_id, stage)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
        return {
            "success": True,
            "order": order.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao avançar etapa: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao avançar etapa: {str(e)}")


@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str):
    """Cancela pedido"""
    try:
        order = await order_service.cancel_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        
        return {
            "success": True,
            "order": order.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao cancelar pedido: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar pedido: {str(e)}")


@router.post("/{order_id}/process-with-ai")
async def process_order_with_ai(order_id: str, request: Request):
    """Processa pedido usando IA"""
    try:
        body = await request.json()
        user_message = body.get("message", "")
        context = body.get("context", {})
        
        result = await order_service.process_order_with_ai(
            order_id=order_id,
            user_message=user_message,
            context=context
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Erro ao processar pedido")
            )
        
        # Executa ações sugeridas pela IA
        actions = result.get("actions", [])
        for action in actions:
            if action.get("type") == "update_stage":
                await order_service.advance_order_stage(
                    order_id,
                    action.get("stage")
                )
        
        return {
            "success": True,
            "response": result.get("response"),
            "actions": actions,
            "order": result.get("order")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar pedido com IA: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar pedido: {str(e)}")
