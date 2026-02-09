"""
Modelos do Auth Service
"""

from .auth import (
    Token, TokenData, UserBase, UserCreate, User, UserInDB, UserResponse,
    Profile, Permission, UserSession, AuditLog, AuditLogCreate,
    ACLCheckRequest, ACLCheckResponse, LoginRequest, LoginResponse,
    RefreshRequest, RegisterRequest, RegisterResponse
)
from .acl import (
    User as ACLUser,
    Profile as ACLProfile,
    Permission as ACLPermission,
    UserSession as ACLUserSession,
    AuditLog as ACLAuditLog
)
from .user_profile import (
    UserProfileData, UserPreferences, UserSettings, UserActivity
)

__all__ = [
    # Auth models
    "Token", "TokenData", "UserBase", "UserCreate", "User", "UserInDB", "UserResponse",
    "Profile", "Permission", "UserSession", "AuditLog", "AuditLogCreate",
    "ACLCheckRequest", "ACLCheckResponse", "LoginRequest", "LoginResponse",
    "RefreshRequest", "RegisterRequest", "RegisterResponse",
    # ACL models (SQLAlchemy)
    "ACLUser", "ACLProfile", "ACLPermission", "ACLUserSession", "ACLAuditLog",
    # User Profile models
    "UserProfileData", "UserPreferences", "UserSettings", "UserActivity"
]
