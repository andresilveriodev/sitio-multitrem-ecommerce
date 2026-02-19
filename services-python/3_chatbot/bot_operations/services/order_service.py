"""
Serviço de CRUD de pedidos
Integrado com o Commerce Service
"""

from typing import List, Optional
import structlog

from models.order_models import (
    OrderStatus, 
    OrderCreate, OrderUpdate, OrderResponse
)
from services.commerce_integration import commerce_integration

logger = structlog.get_logger(__name__)


class OrderService:
    """Serviço para operações CRUD de pedidos usando Commerce Service"""
    
    async def create_order(
        self, 
        order_data: OrderCreate, 
        customer_id: str,
        user_id: str
    ) -> OrderResponse:
        """Cria um novo pedido usando Commerce Service"""
        try:
            logger.info(f"Criando pedido para cliente {customer_id} via Commerce Service")
            order = await commerce_integration.create_order(order_data, customer_id, user_id)
            logger.info(f"Pedido criado: {order.order_number} por usuário {user_id}")
            return order
        except Exception as e:
            logger.error(f"Erro ao criar pedido: {e}", exc_info=True)
            raise
    
    async def get_order(self, order_id: int) -> Optional[OrderResponse]:
        """Busca um pedido por ID usando Commerce Service"""
        try:
            return await commerce_integration.get_order(order_id)
        except Exception as e:
            logger.error(f"Erro ao buscar pedido {order_id}: {e}", exc_info=True)
            raise
    
    async def get_order_by_number(self, order_number: str) -> Optional[OrderResponse]:
        """Busca um pedido por número usando Commerce Service"""
        try:
            return await commerce_integration.get_order_by_number(order_number)
        except Exception as e:
            logger.error(f"Erro ao buscar pedido {order_number}: {e}", exc_info=True)
            raise
    
    async def list_orders(
        self,
        status: Optional[OrderStatus] = None,
        customer_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OrderResponse]:
        """Lista pedidos com filtros opcionais usando Commerce Service"""
        try:
            return await commerce_integration.list_orders(status, customer_id, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao listar pedidos: {e}", exc_info=True)
            raise
    
    async def update_order_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        user_id: str,
        admin_notes: Optional[str] = None
    ) -> Optional[OrderResponse]:
        """Atualiza o status de um pedido usando Commerce Service"""
        try:
            logger.info(f"Atualizando status do pedido {order_id} para {new_status.value} por usuário {user_id}")
            return await commerce_integration.update_order_status(order_id, new_status, user_id, admin_notes)
        except Exception as e:
            logger.error(f"Erro ao atualizar status do pedido {order_id}: {e}", exc_info=True)
            raise
    
    async def approve_order(
        self,
        order_id: int,
        user_id: str,
        admin_notes: Optional[str] = None
    ) -> Optional[OrderResponse]:
        """Aprova um pedido (muda status para CONFIRMED) usando Commerce Service"""
        try:
            logger.info(f"Aprovando pedido {order_id} por usuário {user_id}")
            return await commerce_integration.approve_order(order_id, user_id, admin_notes)
        except Exception as e:
            logger.error(f"Erro ao aprovar pedido {order_id}: {e}", exc_info=True)
            raise
    
    async def reject_order(
        self,
        order_id: int,
        user_id: str,
        admin_notes: Optional[str] = None
    ) -> Optional[OrderResponse]:
        """Rejeita um pedido (muda status para REJECTED) usando Commerce Service"""
        try:
            logger.info(f"Rejeitando pedido {order_id} por usuário {user_id}")
            return await commerce_integration.reject_order(order_id, user_id, admin_notes)
        except Exception as e:
            logger.error(f"Erro ao rejeitar pedido {order_id}: {e}", exc_info=True)
            raise
    
    async def get_pending_orders_count(self) -> int:
        """Retorna a quantidade de pedidos pendentes usando Commerce Service"""
        try:
            return await commerce_integration.get_pending_orders_count()
        except Exception as e:
            logger.error(f"Erro ao contar pedidos pendentes: {e}", exc_info=True)
            return 0


# Instância global do serviço
order_service = OrderService()
