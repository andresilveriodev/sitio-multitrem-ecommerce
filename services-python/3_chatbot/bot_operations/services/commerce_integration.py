"""
Serviço de integração com o Commerce Service
Adapta os modelos do chatbot para os modelos do Commerce Service
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from services.commerce_client import commerce_client
from models.product_models import ProductCreate, ProductUpdate, ProductResponse
from models.order_models import OrderCreate, OrderUpdate, OrderResponse, OrderStatus

logger = structlog.get_logger(__name__)


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Converte string ISO ou datetime para datetime"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # Tenta parsear ISO format
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    return None


class CommerceIntegrationService:
    """Serviço de integração que adapta modelos do chatbot para o Commerce Service"""
    
    # ========== PRODUTOS ==========
    
    def _adapt_product_to_commerce(self, product: Dict[str, Any]) -> ProductResponse:
        """Adapta produto do Commerce Service para ProductResponse do chatbot"""
        return ProductResponse(
            id=product.get("id"),
            name=product.get("name"),
            description=product.get("description"),
            price=float(product.get("price", 0)),
            stock_quantity=product.get("stock_quantity", 0),
            sku=product.get("sku"),
            category=product.get("category"),
            is_active=product.get("is_active", True),
            created_by=product.get("created_by", ""),
            created_at=_parse_datetime(product.get("created_at")),
            updated_at=_parse_datetime(product.get("updated_at"))
        )
    
    def _adapt_product_create_to_commerce(self, product: ProductCreate) -> Dict[str, Any]:
        """Adapta ProductCreate do chatbot para formato do Commerce Service"""
        return {
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock_quantity": product.stock_quantity,
            "sku": product.sku,
            "category": product.category
        }
    
    def _adapt_product_update_to_commerce(self, product: ProductUpdate) -> Dict[str, Any]:
        """Adapta ProductUpdate do chatbot para formato do Commerce Service"""
        data = product.model_dump(exclude_unset=True)
        return data
    
    async def list_products(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProductResponse]:
        """Lista produtos do Commerce Service"""
        try:
            products = await commerce_client.list_products(
                category=category,
                is_active=is_active,
                limit=limit,
                offset=offset
            )
            return [self._adapt_product_to_commerce(p) for p in products]
        except Exception as e:
            logger.error(f"Erro ao listar produtos do Commerce Service: {e}", exc_info=True)
            raise
    
    async def get_product(self, product_id: int) -> Optional[ProductResponse]:
        """Busca um produto do Commerce Service"""
        try:
            product = await commerce_client.get_product(product_id)
            if not product:
                return None
            return self._adapt_product_to_commerce(product)
        except Exception as e:
            logger.error(f"Erro ao buscar produto {product_id} do Commerce Service: {e}", exc_info=True)
            raise
    
    async def create_product(
        self,
        product_data: ProductCreate,
        user_id: str
    ) -> ProductResponse:
        """Cria um produto no Commerce Service"""
        try:
            commerce_data = self._adapt_product_create_to_commerce(product_data)
            # Adiciona created_by se o Commerce Service suportar
            commerce_data["created_by"] = user_id
            
            product = await commerce_client.create_product(commerce_data)
            return self._adapt_product_to_commerce(product)
        except Exception as e:
            logger.error(f"Erro ao criar produto no Commerce Service: {e}", exc_info=True)
            raise
    
    async def update_product(
        self,
        product_id: int,
        product_data: ProductUpdate,
        user_id: str
    ) -> Optional[ProductResponse]:
        """Atualiza um produto no Commerce Service"""
        try:
            commerce_data = self._adapt_product_update_to_commerce(product_data)
            product = await commerce_client.update_product(product_id, commerce_data)
            return self._adapt_product_to_commerce(product)
        except Exception as e:
            logger.error(f"Erro ao atualizar produto {product_id} no Commerce Service: {e}", exc_info=True)
            raise
    
    async def delete_product(self, product_id: int, user_id: str) -> bool:
        """Deleta um produto no Commerce Service (soft delete)"""
        try:
            # Soft delete - marca como inativo
            product = await commerce_client.update_product(
                product_id,
                {"is_active": False}
            )
            return product is not None
        except Exception as e:
            logger.error(f"Erro ao deletar produto {product_id} no Commerce Service: {e}", exc_info=True)
            raise
    
    # ========== PEDIDOS ==========
    
    def _adapt_order_to_commerce(self, order: Dict[str, Any]) -> OrderResponse:
        """Adapta pedido do Commerce Service para OrderResponse do chatbot"""
        # Mapeia status do Commerce Service para OrderStatus do chatbot
        status_map = {
            "draft": OrderStatus.PENDING,
            "confirmed": OrderStatus.CONFIRMED,
            "separating": OrderStatus.PROCESSING,
            "ready": OrderStatus.PROCESSING,
            "out_for_delivery": OrderStatus.SHIPPED,
            "delivered": OrderStatus.DELIVERED,
            "canceled": OrderStatus.CANCELLED
        }
        
        commerce_status = order.get("status", "draft")
        chatbot_status = status_map.get(commerce_status, OrderStatus.PENDING)
        
        return OrderResponse(
            id=order.get("id"),
            order_number=order.get("order_number", ""),
            customer_id=str(order.get("customer_id", "")),
            customer_name=order.get("customer_name"),
            customer_phone=order.get("customer_phone"),
            customer_email=order.get("customer_email"),
            shipping_address=order.get("shipping_address"),
            shipping_city=order.get("shipping_city"),
            shipping_state=order.get("shipping_state"),
            shipping_zip=order.get("shipping_zip"),
            subtotal=float(order.get("subtotal", 0)),
            shipping_cost=float(order.get("shipping_cost", 0)),
            total=float(order.get("total", 0)),
            status=chatbot_status.value,
            payment_status=order.get("payment_status"),
            payment_method=order.get("payment_method"),
            notes=order.get("notes"),
            admin_notes=order.get("admin_notes"),
            created_by=str(order.get("created_by", "")),
            processed_by=str(order.get("processed_by", "")) if order.get("processed_by") else None,
            created_at=_parse_datetime(order.get("created_at")),
            updated_at=_parse_datetime(order.get("updated_at")),
            processed_at=_parse_datetime(order.get("processed_at")),
            items=order.get("items", [])
        )
    
    def _adapt_order_create_to_commerce(self, order: OrderCreate, customer_id: str, user_id: str) -> Dict[str, Any]:
        """Adapta OrderCreate do chatbot para formato do Commerce Service"""
        return {
            "customer_id": int(customer_id) if customer_id.isdigit() else None,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "customer_email": order.customer_email,
            "shipping_address": order.shipping_address,
            "shipping_city": order.shipping_city,
            "shipping_state": order.shipping_state,
            "shipping_zip": order.shipping_zip,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity
                }
                for item in order.items
            ],
            "payment_method": order.payment_method,
            "notes": order.notes,
            "channel": "telegram",  # Canal de origem
            "created_by": user_id
        }
    
    async def list_orders(
        self,
        status: Optional[OrderStatus] = None,
        customer_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[OrderResponse]:
        """Lista pedidos do Commerce Service"""
        try:
            # Mapeia status do chatbot para Commerce Service
            status_map = {
                OrderStatus.PENDING: "draft",
                OrderStatus.CONFIRMED: "confirmed",
                OrderStatus.PROCESSING: "separating",
                OrderStatus.SHIPPED: "out_for_delivery",
                OrderStatus.DELIVERED: "delivered",
                OrderStatus.CANCELLED: "canceled",
                OrderStatus.REJECTED: "canceled"
            }
            
            commerce_status = status_map.get(status) if status else None
            
            orders = await commerce_client.list_orders(
                status=commerce_status,
                customer_id=customer_id,
                limit=limit,
                offset=offset
            )
            return [self._adapt_order_to_commerce(o) for o in orders]
        except Exception as e:
            logger.error(f"Erro ao listar pedidos do Commerce Service: {e}", exc_info=True)
            raise
    
    async def get_order(self, order_id: int) -> Optional[OrderResponse]:
        """Busca um pedido do Commerce Service"""
        try:
            order = await commerce_client.get_order(order_id)
            if not order:
                return None
            return self._adapt_order_to_commerce(order)
        except Exception as e:
            logger.error(f"Erro ao buscar pedido {order_id} do Commerce Service: {e}", exc_info=True)
            raise
    
    async def get_order_by_number(self, order_number: str) -> Optional[OrderResponse]:
        """Busca um pedido por número do Commerce Service"""
        try:
            # O Commerce Service pode não ter endpoint direto por número
            # Vamos buscar na lista e filtrar
            orders = await commerce_client.list_orders(limit=100)
            for order in orders:
                if order.get("order_number") == order_number:
                    return self._adapt_order_to_commerce(order)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar pedido {order_number} do Commerce Service: {e}", exc_info=True)
            raise
    
    async def create_order(
        self,
        order_data: OrderCreate,
        customer_id: str,
        user_id: str
    ) -> OrderResponse:
        """Cria um pedido no Commerce Service"""
        try:
            commerce_data = self._adapt_order_create_to_commerce(order_data, customer_id, user_id)
            order = await commerce_client.create_order(commerce_data)
            return self._adapt_order_to_commerce(order)
        except Exception as e:
            logger.error(f"Erro ao criar pedido no Commerce Service: {e}", exc_info=True)
            raise
    
    async def update_order_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        user_id: str,
        admin_notes: Optional[str] = None
    ) -> Optional[OrderResponse]:
        """Atualiza o status de um pedido no Commerce Service"""
        try:
            # Mapeia status do chatbot para Commerce Service
            status_map = {
                OrderStatus.PENDING: "draft",
                OrderStatus.CONFIRMED: "confirmed",
                OrderStatus.PROCESSING: "separating",
                OrderStatus.SHIPPED: "out_for_delivery",
                OrderStatus.DELIVERED: "delivered",
                OrderStatus.CANCELLED: "canceled",
                OrderStatus.REJECTED: "canceled"
            }
            
            commerce_status = status_map.get(new_status, "draft")
            
            update_data = {"status": commerce_status}
            if admin_notes:
                update_data["admin_notes"] = admin_notes
            
            order = await commerce_client.update_order(order_id, update_data)
            return self._adapt_order_to_commerce(order)
        except Exception as e:
            logger.error(f"Erro ao atualizar status do pedido {order_id} no Commerce Service: {e}", exc_info=True)
            raise
    
    async def approve_order(
        self,
        order_id: int,
        user_id: str,
        admin_notes: Optional[str] = None
    ) -> Optional[OrderResponse]:
        """Aprova um pedido no Commerce Service"""
        try:
            order = await commerce_client.confirm_order(order_id)
            if admin_notes:
                # Atualiza com notas se necessário
                update_data = {"admin_notes": admin_notes}
                order = await commerce_client.update_order(order_id, update_data)
            return self._adapt_order_to_commerce(order)
        except Exception as e:
            logger.error(f"Erro ao aprovar pedido {order_id} no Commerce Service: {e}", exc_info=True)
            raise
    
    async def reject_order(
        self,
        order_id: int,
        user_id: str,
        admin_notes: Optional[str] = None
    ) -> Optional[OrderResponse]:
        """Rejeita um pedido no Commerce Service"""
        try:
            order = await commerce_client.cancel_order(order_id)
            if admin_notes:
                update_data = {"admin_notes": admin_notes}
                order = await commerce_client.update_order(order_id, update_data)
            return self._adapt_order_to_commerce(order)
        except Exception as e:
            logger.error(f"Erro ao rejeitar pedido {order_id} no Commerce Service: {e}", exc_info=True)
            raise
    
    async def get_pending_orders_count(self) -> int:
        """Retorna a quantidade de pedidos pendentes"""
        try:
            orders = await commerce_client.list_orders(status="draft", limit=1000)
            return len(orders)
        except Exception as e:
            logger.error(f"Erro ao contar pedidos pendentes do Commerce Service: {e}", exc_info=True)
            return 0


# Instância global do serviço de integração
commerce_integration = CommerceIntegrationService()
