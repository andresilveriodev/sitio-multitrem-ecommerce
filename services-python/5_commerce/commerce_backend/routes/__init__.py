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
from .cadastro import router as cadastro_router
from .boletas import router as boletas_router
from .conversas import router as conversas_router
from .listas_compra import router as listas_compra_router
from .preferencia import router as preferencia_router
from .contexto_ia import router as contexto_ia_router
from .colaboradores import router as colaboradores_router
from .whatsapp_envio import router as whatsapp_envio_router

__all__ = [
    "products_router",
    "customers_router",
    "orders_router",
    "payments_router",
    "deliveries_router",
    "shipping_router",
    "chatbot_router",
    "cadastro_router",
    "boletas_router",
    "conversas_router",
    "listas_compra_router",
    "preferencia_router",
    "contexto_ia_router",
    "colaboradores_router",
    "whatsapp_envio_router",
]
