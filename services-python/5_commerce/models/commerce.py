"""
Modelos SQLAlchemy para o schema commerce
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, 
    Numeric, Date, Enum as SQLEnum, UUID, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM
import uuid
import enum

from db_session import Base


# Enums
class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    SEPARATING = "separating"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class OrderChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SITE = "site"
    MANUAL = "manual"


class PaymentMethod(str, enum.Enum):
    PIX = "pix"
    CASH = "cash"
    TRANSFER = "transfer"
    CARD = "card"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class DeliveryRouteStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELED = "canceled"


class DeliveryStopStatus(str, enum.Enum):
    PENDING = "pending"
    ARRIVED = "arrived"
    DELIVERED = "delivered"
    FAILED = "failed"


# Tabelas do schema commerce
class ProductCategory(Base):
    """Categoria de produtos"""
    __tablename__ = "product_category"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    products = relationship("Product", back_populates="category")


class Product(Base):
    """Produto"""
    __tablename__ = "product"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey('commerce.product_category.id'), nullable=False, index=True)
    sku = Column(String(50), unique=True, nullable=True, index=True)
    name = Column(String(200), nullable=False)
    unit = Column(String(20), nullable=False)  # un, maço, bandeja, dz, pct
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    category = relationship("ProductCategory", back_populates="products")
    prices = relationship("ProductPrice", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    customer_product_prices = relationship("CustomerProductPrice", back_populates="product")


class PriceList(Base):
    """Lista de preços"""
    __tablename__ = "price_list"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    product_prices = relationship("ProductPrice", back_populates="price_list")
    customers = relationship("Customer", back_populates="default_price_list")
    orders = relationship("Order", back_populates="price_list")


class ProductPrice(Base):
    """Preço de produto por lista de preços"""
    __tablename__ = "product_price"
    __table_args__ = (
        Index('idx_product_price_composite', 'product_id', 'price_list_id', 'valid_from'),
        {'schema': 'commerce'}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('commerce.product.id'), nullable=False, index=True)
    price_list_id = Column(Integer, ForeignKey('commerce.price_list.id'), nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    product = relationship("Product", back_populates="prices")
    price_list = relationship("PriceList", back_populates="product_prices")


class PriceProfile(str, enum.Enum):
    """Perfil de preço do cliente"""
    RESTAURANTE_HIGH = "RESTAURANTE_HIGH"
    RESTAURANTE_LOW = "RESTAURANTE_LOW"
    VAREJO = "VAREJO"


class Customer(Base):
    """Cliente"""
    __tablename__ = "customer"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    phone_e164 = Column(String(20), unique=True, nullable=False, index=True)  # +5562...
    document = Column(String(20), nullable=True)  # CPF/CNPJ
    price_profile = Column(SQLEnum(PriceProfile), nullable=False, default=PriceProfile.VAREJO, index=True)
    default_price_list_id = Column(Integer, ForeignKey('commerce.price_list.id'), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    default_price_list = relationship("PriceList", back_populates="customers", foreign_keys=[default_price_list_id])
    addresses = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")
    customer_product_prices = relationship("CustomerProductPrice", back_populates="customer", cascade="all, delete-orphan")
    contacts = relationship("CustomerContact", back_populates="customer", cascade="all, delete-orphan")


class DeliveryZone(Base):
    """Zona de entrega"""
    __tablename__ = "delivery_zone"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # "Centro", "Setor Jaó", etc.
    fee = Column(Numeric(10, 2), nullable=False)  # Valor do frete
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    addresses = relationship("CustomerAddress", back_populates="delivery_zone")


class CustomerAddress(Base):
    """Endereço do cliente"""
    __tablename__ = "customer_address"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('commerce.customer.id'), nullable=False, index=True)
    delivery_zone_id = Column(Integer, ForeignKey('commerce.delivery_zone.id'), nullable=True, index=True)
    label = Column(String(100), nullable=False)  # "Casa", "Restaurante", etc.
    street = Column(String(200), nullable=False)
    number = Column(String(20), nullable=True)
    district = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zip = Column(String(10), nullable=False)
    reference = Column(Text, nullable=True)
    location_url = Column(String(500), nullable=True)  # URL do Google Maps ou similar
    lat = Column(Numeric(10, 8), nullable=True)
    lng = Column(Numeric(11, 8), nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    customer = relationship("Customer", back_populates="addresses")
    delivery_zone = relationship("DeliveryZone", back_populates="addresses")
    orders = relationship("Order", back_populates="delivery_address")


class CustomerProductPrice(Base):
    """Preço específico de produto para um cliente (exceção comercial)"""
    __tablename__ = "customer_product_price"
    __table_args__ = (
        Index('idx_customer_product_price_unique', 'customer_id', 'product_id', unique=True),
        {'schema': 'commerce'}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('commerce.customer.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('commerce.product.id'), nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    customer = relationship("Customer", back_populates="customer_product_prices")
    product = relationship("Product", back_populates="customer_product_prices")


class CustomerContact(Base):
    """Contato/Usuário vinculado a um cliente comercial"""
    __tablename__ = "customer_contact"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('commerce.customer.id'), nullable=False, index=True)
    name = Column(String(200), nullable=False)  # Nome do contato (ex: "João Batista", "Dona Dilma")
    phone_e164 = Column(String(20), nullable=True, index=True)  # Telefone do contato (opcional)
    email = Column(String(200), nullable=True, index=True)  # Email para login (opcional)
    role = Column(String(100), nullable=True)  # Função: "proprietario", "cozinheira", "gerente", etc.
    keycloak_user_id = Column(String(200), nullable=True, index=True)  # ID do usuário no Keycloak (opcional)
    active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)  # Observações sobre o contato
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    customer = relationship("Customer", back_populates="contacts")


class Order(Base):
    """Pedido"""
    __tablename__ = "order"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(Integer, ForeignKey('commerce.customer.id'), nullable=False, index=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.DRAFT, index=True)
    channel = Column(SQLEnum(OrderChannel), nullable=False, index=True)
    price_list_id = Column(Integer, ForeignKey('commerce.price_list.id'), nullable=False)
    delivery_address_id = Column(Integer, ForeignKey('commerce.customer_address.id'), nullable=True)
    delivery_fee = Column(Numeric(10, 2), default=0, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    # Relacionamentos
    customer = relationship("Customer", back_populates="orders")
    price_list = relationship("PriceList", back_populates="orders")
    delivery_address = relationship("CustomerAddress", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    delivery_stops = relationship("DeliveryStop", back_populates="order")


class OrderItem(Base):
    """Item do pedido"""
    __tablename__ = "order_item"
    __table_args__ = (
        Index('idx_order_item_order', 'order_id'),
        Index('idx_order_item_product', 'product_id'),
        {'schema': 'commerce'}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey('commerce.order.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('commerce.product.id'), nullable=False, index=True)
    qty = Column(Numeric(10, 2), nullable=False)  # Permite 0.5 maço
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text, nullable=True)  # "com raiz", "no vaso"
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base):
    """Pagamento"""
    __tablename__ = "payment"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey('commerce.order.id'), nullable=False, index=True)
    method = Column(SQLEnum(PaymentMethod), nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    paid_at = Column(DateTime, nullable=True)
    external_ref = Column(String(200), nullable=True)  # txid pix, etc.
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    order = relationship("Order", back_populates="payments")


class DeliveryRoute(Base):
    """Rota de entrega"""
    __tablename__ = "delivery_route"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    driver_name = Column(String(200), nullable=True)  # Ou driver_id no futuro
    status = Column(SQLEnum(DeliveryRouteStatus), nullable=False, default=DeliveryRouteStatus.PLANNED, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    stops = relationship("DeliveryStop", back_populates="route", cascade="all, delete-orphan")


class DeliveryStop(Base):
    """Parada na rota de entrega"""
    __tablename__ = "delivery_stop"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey('commerce.delivery_route.id'), nullable=False, index=True)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey('commerce.order.id'), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)  # Ordem na rota
    status = Column(SQLEnum(DeliveryStopStatus), nullable=False, default=DeliveryStopStatus.PENDING, index=True)
    delivered_at = Column(DateTime, nullable=True)
    proof = Column(Text, nullable=True)  # Texto/arquivo ref
    fee_per_stop = Column(Numeric(10, 2), default=1.50, nullable=False)  # 1,50 por ponto
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    route = relationship("DeliveryRoute", back_populates="stops")
    order = relationship("Order", back_populates="delivery_stops")


class AuditLog(Base):
    """Log de auditoria"""
    __tablename__ = "audit_log"
    __table_args__ = {'schema': 'commerce'}
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True)  # "order", "customer", etc.
    entity_id = Column(String(100), nullable=False, index=True)  # UUID ou ID
    action = Column(String(50), nullable=False, index=True)  # "create", "update", "delete"
    data = Column(Text, nullable=True)  # JSONB seria melhor, mas Text funciona
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
