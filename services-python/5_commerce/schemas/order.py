"""
Schemas Pydantic para pedidos
"""

from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from models.commerce import OrderStatus, OrderChannel


class OrderItemBase(BaseModel):
    product_id: int
    qty: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., ge=0)
    notes: Optional[str] = None


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: UUID
    subtotal: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    customer_id: int
    channel: OrderChannel
    price_list_id: int
    delivery_address_id: Optional[int] = None
    delivery_fee: Decimal = Field(default=0, ge=0)
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_items=1)


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    delivery_address_id: Optional[int] = None
    delivery_fee: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class OrderResponse(OrderBase):
    id: UUID
    status: OrderStatus
    subtotal: Decimal
    total: Decimal
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    
    @computed_field
    def short_id(self) -> str:
        """Retorna um ID curto para exibição no formato DDMM-XXXXX (data + código)"""
        # Formata data como DDMM (sem ano)
        date_str = self.created_at.strftime('%d%m')
        # Pega primeiros 5 caracteres do UUID (sem hífens) em maiúsculas
        code = str(self.id).replace('-', '')[:5].upper()
        return f"{date_str}-{code}"
    
    class Config:
        from_attributes = True


class OrderSummary(BaseModel):
    """Resumo de pedido para listagens"""
    id: UUID
    customer_id: int
    customer_name: Optional[str] = None
    status: OrderStatus
    channel: OrderChannel
    total: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True
