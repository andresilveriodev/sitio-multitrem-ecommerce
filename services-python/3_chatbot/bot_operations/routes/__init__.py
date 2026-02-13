"""
Routers do chatbot_service
"""

from .chat_router import router as chat_router
from .analytics_router import router as analytics_router
from .ai_router import router as ai_router

__all__ = ["chat_router", "analytics_router", "ai_router"]
