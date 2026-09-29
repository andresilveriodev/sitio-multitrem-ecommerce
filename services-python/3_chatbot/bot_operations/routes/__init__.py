"""
Routers do chatbot_service
"""

from .chat_router import router as chat_router
from .analytics_router import router as analytics_router
from .ai_router import router as ai_router
from .telegram_router import router as telegram_router
from .messages_debug_router import router as messages_debug_router
from .order_intake_router import router as order_intake_router
from .cadastro_chat_router import router as cadastro_chat_router

__all__ = [
    "chat_router",
    "analytics_router",
    "ai_router",
    "telegram_router",
    "messages_debug_router",
    "order_intake_router",
    "cadastro_chat_router",
]
