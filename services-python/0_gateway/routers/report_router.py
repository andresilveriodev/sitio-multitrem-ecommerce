"""
Router para o serviço de relatórios
"""

from .base_router import create_service_router
from ..config import settings

router = create_service_router(
    service_url=settings.REPORT_SERVICE_URL,
    service_name="Report Service",
    require_auth=True
)
