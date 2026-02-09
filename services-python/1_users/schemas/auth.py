"""
Schemas Pydantic para autenticação e usuários
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Schema base para usuário"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    keycloak_id: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema para criação de usuário"""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Schema para atualização de usuário"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    keycloak_id: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema para resposta de usuário"""
    id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserBase):
    """Schema para usuário no banco de dados"""
    id: int
    hashed_password: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema para token de acesso"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Schema para dados do token"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    """Schema para requisição de login"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Schema para requisição de registro"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=6)


class PasswordChangeRequest(BaseModel):
    """Schema para mudança de senha"""
    current_password: str
    new_password: str = Field(..., min_length=6)


class PasswordResetRequest(BaseModel):
    """Schema para reset de senha"""
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Schema para confirmação de reset de senha"""
    token: str
    new_password: str = Field(..., min_length=6)


class UserProfileResponse(BaseModel):
    """Schema para resposta de perfil de usuário"""
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Schema para lista de usuários"""
    users: list[UserResponse]
    total: int
    skip: int
    limit: int


class HealthCheckResponse(BaseModel):
    """Schema para health check"""
    status: str
    timestamp: datetime
    version: str
    database: str
    keycloak: str

