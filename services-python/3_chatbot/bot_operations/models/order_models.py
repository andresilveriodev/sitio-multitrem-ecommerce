"""
Modelos de dados para pedidos do e-commerce
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Numeric, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
import enum

from models.product_models import Base


class OrderStatus(str, enum.Enum):
    """Status dos pedidos"""
    PENDING = "pending"           # Aguardando processamento
    CONFIRMED = "confirmed"       # Confirmado
    PROCESSING = "processing"     # Em processamento
    SHIPPED = "shipped"           # Enviado
    DELIVERED = "delivered"       # Entregue
    CANCELLED = "cancelled"       # Cancelado
    REJECTED = "rejected"         # Rejeitado


class Order(Base):
    """Modelo SQLAlchemy para pedidos"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)  # Número do pedido
    customer_id = Column(String(100), nullable=False, index=True)  # ID do cliente (Telegram user_id)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    customer_email = Column(String(255), nullable=True)
    
    # Endereço de entrega
    shipping_address = Column(Text, nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(50), nullable=True)
    shipping_zip = Column(String(20), nullable=True)
    
    # Valores
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    shipping_cost = Column(Numeric(10, 2), nullable=False, default=0)
    total = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Status e controle
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True)
    payment_status = Column(String(50), nullable=True, default="pending")  # pending, paid, refunded
    payment_method = Column(String(50), nullable=True)  # credit_card, pix, boleto, etc.
    
    # Observações
    notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)  # Notas internas do admin
    
    # Metadados
    created_by = Column(String(100), nullable=False)  # Telegram user_id que criou
    processed_by = Column(String(100), nullable=True)  # Telegram user_id que processou
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status.value}')>"


class OrderItem(Base):
    """Modelo SQLAlchemy para itens do pedido"""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)  # Nome do produto no momento da compra
    product_sku = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    order = relationship("Order", backref="items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity})>"


# Modelos Pydantic para validação e serialização
class OrderItemCreate(BaseModel):
    """Modelo para criação de item do pedido"""
    product_id: int = Field(..., description="ID do produto")
    quantity: int = Field(..., gt=0, description="Quantidade")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": 1,
                "quantity": 2
            }
        }


class OrderCreate(BaseModel):
    """Modelo para criação de pedido"""
    customer_name: Optional[str] = Field(None, max_length=255, description="Nome do cliente")
    customer_phone: Optional[str] = Field(None, max_length=20, description="Telefone do cliente")
    customer_email: Optional[str] = Field(None, max_length=255, description="Email do cliente")
    shipping_address: Optional[str] = Field(None, description="Endereço de entrega")
    shipping_city: Optional[str] = Field(None, max_length=100, description="Cidade")
    shipping_state: Optional[str] = Field(None, max_length=50, description="Estado")
    shipping_zip: Optional[str] = Field(None, max_length=20, description="CEP")
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Itens do pedido")
    payment_method: Optional[str] = Field(None, max_length=50, description="Método de pagamento")
    notes: Optional[str] = Field(None, description="Observações do cliente")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_name": "João Silva",
                "customer_phone": "(11) 99999-9999",
                "customer_email": "joao@example.com",
                "shipping_address": "Rua Exemplo, 123",
                "shipping_city": "São Paulo",
                "shipping_state": "SP",
                "shipping_zip": "01234-567",
                "items": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 3, "quantity": 1}
                ],
                "payment_method": "pix",
                "notes": "Entregar de manhã"
            }
        }


class OrderUpdate(BaseModel):
    """Modelo para atualização de pedido"""
    status: Optional[OrderStatus] = None
    payment_status: Optional[str] = None
    admin_notes: Optional[str] = None
    shipping_cost: Optional[float] = Field(None, ge=0)


class OrderResponse(BaseModel):
    """Modelo de resposta de pedido"""
    id: int
    order_number: str
    customer_id: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_email: Optional[str]
    shipping_address: Optional[str]
    shipping_city: Optional[str]
    shipping_state: Optional[str]
    shipping_zip: Optional[str]
    subtotal: float
    shipping_cost: float
    total: float
    status: str
    payment_status: Optional[str]
    payment_method: Optional[str]
    notes: Optional[str]
    admin_notes: Optional[str]
    created_by: str
    processed_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]
    items: List[dict] = []
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderItemResponse(BaseModel):
    """Modelo de resposta de item do pedido"""
    id: int
    order_id: int
    product_id: int
    product_name: str
    product_sku: Optional[str]
    quantity: int
    unit_price: float
    total_price: float
    
    class Config:
        from_attributes = True
