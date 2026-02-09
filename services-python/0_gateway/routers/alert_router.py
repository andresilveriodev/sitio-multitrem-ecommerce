"""
Router para o serviço de alertas
"""

from .base_router import create_service_router
from ..config import settings

router = create_service_router(
    service_url=settings.ALERT_SERVICE_URL,
    service_name="Alert Service",
    require_auth=True
)
