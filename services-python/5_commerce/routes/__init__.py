"""
Rotas FastAPI do Commerce Service
"""

from .products import router as products_router
from .customers import router as customers_router
from .orders import router as orders_router
from .payments import router as payments_router
from .deliveries import router as deliveries_router
from .shipping import router as shipping_router
from .chatbot import router as chatbot_router

__all__ = [
    "products_router",
    "customers_router",
    "orders_router",
    "payments_router",
    "deliveries_router",
    "shipping_router",
    "chatbot_router",
]
