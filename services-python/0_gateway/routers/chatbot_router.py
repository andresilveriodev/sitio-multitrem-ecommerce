"""
Router para o serviço de chatbot
"""

from .base_router import create_service_router
from ..config import settings

router = create_service_router(
    service_url=settings.CHATBOT_SERVICE_URL,
    service_name="Chatbot Service",
    require_auth=True
)
