"""
Modelos do chatbot_service
"""

from .conversation_context import (
    Message,
    MessageType,
    ConversationContext,
    UserPreferences,
    SessionData
)
from .order_models import (
    Order,
    OrderStatus,
    OrderItem,
    DeliveryAddress,
    PaymentStatus,
    PaymentMethod,
    OrderStage,
    OrderUpdate,
    OrderQuery
)

__all__ = [
    "Message",
    "MessageType", 
    "ConversationContext",
    "UserPreferences",
    "SessionData",
    "Order",
    "OrderStatus",
    "OrderItem",
    "DeliveryAddress",
    "PaymentStatus",
    "PaymentMethod",
    "OrderStage",
    "OrderUpdate",
    "OrderQuery"
]
