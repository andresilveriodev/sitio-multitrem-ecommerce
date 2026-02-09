"""
Router para o serviço de usuários
"""

from .base_router import create_service_router
from ..config import settings

router = create_service_router(
    service_url=settings.USER_SERVICE_URL,
    service_name="User Service",
    require_auth=True
)
