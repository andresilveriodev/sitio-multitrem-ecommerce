"""
Router para o serviço de importação
"""

from .base_router import create_service_router
from ..config import settings

router = create_service_router(
    service_url=settings.IMPORT_SERVICE_URL,
    service_name="Import Service",
    require_auth=True
)
