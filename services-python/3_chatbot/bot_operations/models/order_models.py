"""
Modelos para gerenciamento de pedidos e entregas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class OrderStatus(str, Enum):
    """Status do pedido"""
    PENDING = "pending"  # Aguardando confirmação
    CONFIRMED = "confirmed"  # Confirmado
    IN_HARVEST = "in_harvest"  # Em colheita
    IN_PURCHASE = "in_purchase"  # Comprando no fornecedor
    IN_SEPARATION = "in_separation"  # Em separação
    READY_TO_SHIP = "ready_to_ship"  # Pronto para envio
    SHIPPED = "shipped"  # Enviado
    IN_TRANSIT = "in_transit"  # Em trânsito
    DELIVERED = "delivered"  # Entregue
    CANCELLED = "cancelled"  # Cancelado
    PAYMENT_PENDING = "payment_pending"  # Aguardando pagamento
    PAYMENT_CONFIRMED = "payment_confirmed"  # Pagamento confirmado
    PAYMENT_FAILED = "payment_failed"  # Falha no pagamento


class PaymentStatus(str, Enum):
    """Status do pagamento"""
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Métodos de pagamento"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PIX = "pix"
    BANK_SLIP = "bank_slip"
    CASH = "cash"
    OTHER = "other"


class OrderItem(BaseModel):
    """Item do pedido"""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    notes: Optional[str] = None


class DeliveryAddress(BaseModel):
    """Endereço de entrega"""
    street: str
    number: str
    complement: Optional[str] = None
    neighborhood: str
    city: str
    state: str
    zip_code: str
    reference: Optional[str] = None


class Order(BaseModel):
    """Modelo de pedido"""
    id: str
    user_id: str
    order_number: str  # Número do pedido (ex: PED-2024-001)
    status: OrderStatus = OrderStatus.PENDING
    items: List[OrderItem] = Field(default_factory=list)
    total_amount: float = 0.0
    delivery_address: Optional[DeliveryAddress] = None
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    payment_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict)  # Metadados adicionais
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderStage(BaseModel):
    """Etapa do processo de pedido"""
    order_id: str
    stage: str  # "pedido", "colheita", "compra_fornecedor", "separacao", "envio", "pagamento"
    status: str  # "pending", "in_progress", "completed", "failed"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OrderUpdate(BaseModel):
    """Atualização de pedido"""
    order_id: str
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    stage: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict] = None


class OrderQuery(BaseModel):
    """Query para buscar pedidos"""
    user_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    order_number: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 50
    offset: int = 0
