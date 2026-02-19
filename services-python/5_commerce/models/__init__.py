"""
Modelos SQLAlchemy para o Commerce Service
"""

from db_session import Base

# Importar todos os modelos para que sejam registrados
from .commerce import (
    ProductCategory,
    Product,
    PriceList,
    ProductPrice,
    PriceProfile,
    Customer,
    CustomerAddress,
    CustomerProductPrice,
    DeliveryZone,
    Order,
    OrderItem,
    Payment,
    DeliveryRoute,
    DeliveryStop,
    AuditLog
)

from .chatbot import (
    ChannelAccount,
    Conversation,
    Message,
    IntentRule,
    Outbox
)

__all__ = [
    "Base",
    # Commerce models
    "ProductCategory",
    "Product",
    "PriceList",
    "ProductPrice",
    "PriceProfile",
    "Customer",
    "CustomerAddress",
    "CustomerProductPrice",
    "DeliveryZone",
    "Order",
    "OrderItem",
    "Payment",
    "DeliveryRoute",
    "DeliveryStop",
    "AuditLog",
    # Chatbot models
    "ChannelAccount",
    "Conversation",
    "Message",
    "IntentRule",
    "Outbox",
]
