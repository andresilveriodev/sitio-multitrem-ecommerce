"""
Serviço de pedidos
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from decimal import Decimal
from datetime import datetime
from uuid import UUID
import structlog

from models.commerce import Order, OrderItem, Product, ProductPrice, OrderStatus, OrderChannel, Customer, CustomerAddress
from schemas.order import OrderCreate, OrderUpdate, OrderItemCreate
from services.pricing_service import PricingService
from services.shipping_service import ShippingService

logger = structlog.get_logger()


class OrderService:
    """Serviço para gerenciar pedidos"""
    
    @staticmethod
    def get_orders(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[OrderStatus] = None,
        customer_id: Optional[int] = None
    ) -> List[Order]:
        """Lista pedidos"""
        query = db.query(Order)
        
        if status:
            query = query.filter(Order.status == status)
        
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        
        return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_order(db: Session, order_id: UUID) -> Optional[Order]:
        """Busca um pedido por ID"""
        return db.query(Order).filter(Order.id == order_id).first()
    
    @staticmethod
    def create_order(db: Session, order: OrderCreate) -> Order:
        """
        Cria um novo pedido aplicando regras de negócio:
        1. Normalização de alfaces
        2. Aplicação de preços por perfil
        3. Cálculo de frete
        """
        # Busca cliente
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if not customer:
            raise ValueError(f"Cliente {order.customer_id} não encontrado")
        
        # Calcula subtotal aplicando regras de precificação
        subtotal = Decimal("0")
        items_data = []
        
        for item in order.items:
            # Busca produto
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise ValueError(f"Produto {item.product_id} não encontrado")
            
            # Verifica se é palito (pode vir do item ou do produto)
            is_palito = "palito" in (item.notes or "").lower() or "palito" in (product.sku or "").lower()
            
            # Aplica regras de precificação (normalização + preço)
            unit_price, item_subtotal, qty_final = PricingService.calculate_item_price(
                db, customer, product, item.qty, is_palito
            )
            
            if unit_price == 0:
                raise ValueError(f"Preço não encontrado para produto {product.id} e perfil {customer.price_profile.value}")
            
            subtotal += item_subtotal
            
            items_data.append({
                "product_id": item.product_id,
                "qty": qty_final,
                "unit_price": unit_price,
                "subtotal": item_subtotal,
                "notes": item.notes
            })
        
        # Calcula frete
        delivery_fee = order.delivery_fee
        if order.delivery_address_id:
            address = db.query(CustomerAddress).filter(CustomerAddress.id == order.delivery_address_id).first()
            if address:
                delivery_fee = ShippingService.calculate_shipping(db, address, subtotal)
            else:
                logger.warning(f"Endereço {order.delivery_address_id} não encontrado, usando frete informado")
        
        total = subtotal + delivery_fee
        
        # Cria o pedido
        order_data = order.model_dump(exclude={"items"})
        order_data["subtotal"] = subtotal
        order_data["total"] = total
        order_data["delivery_fee"] = delivery_fee
        order_data["status"] = OrderStatus.DRAFT
        
        db_order = Order(**order_data)
        db.add(db_order)
        db.flush()  # Para obter o ID
        
        # Cria os itens
        for item_data in items_data:
            db_item = OrderItem(
                order_id=db_order.id,
                **item_data
            )
            db.add(db_item)
        
        db.commit()
        db.refresh(db_order)
        logger.info(
            "Pedido criado",
            order_id=db_order.id,
            customer_id=order.customer_id,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total,
            price_profile=customer.price_profile.value
        )
        return db_order
    
    @staticmethod
    def update_order(db: Session, order_id: UUID, order: OrderUpdate) -> Optional[Order]:
        """Atualiza um pedido"""
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None
        
        update_data = order.model_dump(exclude_unset=True)
        
        # Se mudou para confirmed, atualiza confirmed_at
        if update_data.get("status") == OrderStatus.CONFIRMED and not db_order.confirmed_at:
            update_data["confirmed_at"] = datetime.utcnow()
        
        # Se mudou para delivered, atualiza delivered_at
        if update_data.get("status") == OrderStatus.DELIVERED and not db_order.delivered_at:
            update_data["delivered_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_order, field, value)
        
        db.commit()
        db.refresh(db_order)
        logger.info("Pedido atualizado", order_id=order_id, status=update_data.get("status"))
        return db_order
    
    @staticmethod
    def confirm_order(db: Session, order_id: UUID) -> Optional[Order]:
        """Confirma um pedido (muda status para confirmed)"""
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None
        
        if db_order.status != OrderStatus.DRAFT:
            raise ValueError(f"Pedido {order_id} não está em status DRAFT")
        
        db_order.status = OrderStatus.CONFIRMED
        db_order.confirmed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_order)
        logger.info("Pedido confirmado", order_id=order_id)
        return db_order
    
    @staticmethod
    def cancel_order(db: Session, order_id: UUID) -> Optional[Order]:
        """Cancela um pedido"""
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None
        
        if db_order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELED]:
            raise ValueError(f"Pedido {order_id} não pode ser cancelado")
        
        db_order.status = OrderStatus.CANCELED
        db.commit()
        db.refresh(db_order)
        logger.info("Pedido cancelado", order_id=order_id)
        return db_order
