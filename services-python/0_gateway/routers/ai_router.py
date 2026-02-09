"""
Router para o serviço de IA
"""

from .base_router import create_service_router
from ..config import settings

router = create_service_router(
    service_url=settings.AI_SERVICE_URL,
    service_name="AI Service",
    require_auth=True
)
