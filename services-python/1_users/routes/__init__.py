"""
Rotas do Auth Service
"""

from .auth import router as auth_router
from .acl import router as acl_router
from .user_profile import router as user_profile_router
from .users import router as users_router

__all__ = ["auth_router", "acl_router", "user_profile_router", "users_router"]
