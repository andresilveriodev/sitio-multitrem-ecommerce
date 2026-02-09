"""
Modelos Pydantic para autenticação e ACL
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class Token(BaseModel):
    """Modelo para token de acesso"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Modelo para dados do token"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    profiles: List[str] = []


# ==================== MODELOS DE AUTENTICAÇÃO ====================

class UserBase(BaseModel):
    """Modelo base para usuário de autenticação"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    keycloak_id: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False


class UserCreate(UserBase):
    """Modelo para criação de usuário"""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Modelo para atualização de usuário"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    keycloak_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class User(UserBase):
    """Modelo para usuário de autenticação"""
    id: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """Modelo para usuário no banco de dados"""
    hashed_password: str


class UserResponse(BaseModel):
    """Modelo para resposta de usuário"""
    id: int
    username: str
    email: EmailStr
    keycloak_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    profiles: List[str] = []
    
    class Config:
        from_attributes = True


# ==================== MODELOS DE PERFIL ====================

class ProfileBase(BaseModel):
    """Modelo base para perfil"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: bool = True


class ProfileCreate(ProfileBase):
    """Modelo para criação de perfil"""
    pass


class ProfileUpdate(BaseModel):
    """Modelo para atualização de perfil"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Profile(ProfileBase):
    """Modelo para perfil"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== MODELOS DE PERMISSÃO ====================

class PermissionScope(str, Enum):
    """Escopo das permissões"""
    OWN = "own"
    ALL = "all"
    ADMIN = "admin"


class PermissionBase(BaseModel):
    """Modelo base para permissão"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    resource: str = Field(..., min_length=2, max_length=50)
    action: str = Field(..., min_length=2, max_length=20)
    scope: PermissionScope = PermissionScope.OWN
    is_active: bool = True


class PermissionCreate(PermissionBase):
    """Modelo para criação de permissão"""
    pass


class PermissionUpdate(BaseModel):
    """Modelo para atualização de permissão"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    resource: Optional[str] = Field(None, min_length=2, max_length=50)
    action: Optional[str] = Field(None, min_length=2, max_length=20)
    scope: Optional[PermissionScope] = None
    is_active: Optional[bool] = None


class Permission(PermissionBase):
    """Modelo para permissão"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== MODELOS DE RELACIONAMENTOS ====================

class UserProfileBase(BaseModel):
    """Modelo base para relacionamento usuário-perfil"""
    user_id: int
    profile_id: int
    assigned_by: Optional[int] = None


class UserProfileCreate(UserProfileBase):
    """Modelo para criação de relacionamento usuário-perfil"""
    pass


class UserProfile(UserProfileBase):
    """Modelo para relacionamento usuário-perfil"""
    id: int
    assigned_at: datetime
    
    class Config:
        from_attributes = True


class ProfilePermissionBase(BaseModel):
    """Modelo base para relacionamento perfil-permissão"""
    profile_id: int
    permission_id: int


class ProfilePermissionCreate(ProfilePermissionBase):
    """Modelo para criação de relacionamento perfil-permissão"""
    pass


class ProfilePermission(ProfilePermissionBase):
    """Modelo para relacionamento perfil-permissão"""
    id: int
    assigned_at: datetime
    
    class Config:
        from_attributes = True


# ==================== MODELOS DE SESSÃO ====================

class UserSessionBase(BaseModel):
    """Modelo base para sessão de usuário"""
    user_id: int
    session_token: str
    refresh_token: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    is_active: bool = True


class UserSessionCreate(UserSessionBase):
    """Modelo para criação de sessão"""
    pass


class UserSessionUpdate(BaseModel):
    """Modelo para atualização de sessão"""
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class UserSession(UserSessionBase):
    """Modelo para sessão de usuário"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== MODELOS DE AUDITORIA ====================

class AuditLogBase(BaseModel):
    """Modelo base para log de auditoria"""
    user_id: Optional[int] = None
    action: str = Field(..., min_length=2, max_length=100)
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True


class AuditLogCreate(AuditLogBase):
    """Modelo para criação de log de auditoria"""
    pass


class AuditLog(AuditLogBase):
    """Modelo para log de auditoria"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== MODELOS DE RESPOSTA ====================

class ProfileWithPermissions(Profile):
    """Modelo para perfil com suas permissões"""
    permissions: List[Permission] = []


class UserWithProfiles(UserResponse):
    """Modelo para usuário com seus perfis"""
    profiles: List[Profile] = []


class ACLCheckRequest(BaseModel):
    """Modelo para verificação de ACL"""
    user_id: int
    resource: str
    action: str
    scope: Optional[PermissionScope] = PermissionScope.OWN


class ACLCheckResponse(BaseModel):
    """Modelo para resposta de verificação de ACL"""
    allowed: bool
    permissions: List[Permission]
    message: Optional[str] = None


class LoginRequest(BaseModel):
    """Modelo para requisição de login"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Modelo para resposta de login"""
    user: UserResponse
    token: Token
    profiles: List[Profile]
    permissions: List[Permission]


class RefreshRequest(BaseModel):
    """Modelo para requisição de refresh token"""
    refresh_token: str


import re
from typing import Union

def validate_cpf(cpf: str) -> bool:
    """Valida CPF brasileiro"""
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    # Verifica se os dígitos calculados são iguais aos do CPF
    return cpf[-2:] == f"{digito1}{digito2}"

def validate_username(username: str) -> bool:
    """Valida se username é email ou CPF válido"""
    # Verifica se é email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, username):
        return True
    
    # Verifica se é CPF
    if validate_cpf(username):
        return True
    
    return False

class RegisterRequest(BaseModel):
    """Modelo para requisição de registro"""
    cpf: str = Field(..., min_length=11, max_length=20)  # CPF do usuário
    email: EmailStr
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)  # Telefone internacional (opcional)
    password: Optional[str] = Field(None, min_length=6)  # Opcional, pode ser definida depois
    keycloak_id: Optional[str] = None
    
    @validator('cpf')
    def validate_cpf_format(cls, v):
        if not validate_cpf(v):
            raise ValueError('CPF deve ser válido')
        return v
    
    @validator('phone')
    def validate_phone_format(cls, v):
        # Validar formato internacional: +pais-dd-telefone (se fornecido)
        if v is not None:
            phone_pattern = r'^\+[1-9]\d{1,3}-\d{1,4}-\d{4,15}$'
            if not re.match(phone_pattern, v):
                raise ValueError('Telefone deve estar no formato internacional: +pais-dd-telefone (ex: +55-11-99999-9999)')
        return v


class RegisterResponse(BaseModel):
    """Modelo para resposta de registro"""
    success: bool
    keycloak_id: Optional[str] = None
    message: str
    user_data: Optional[Dict[str, Any]] = None


class UserDataResponse(BaseModel):
    """Modelo para resposta com dados do token JWT"""
    # Dados do Keycloak (do token)
    keycloak_id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: List[str] = []
    exp: Optional[int] = None
    iat: Optional[int] = None
    
    # Dados do usuário local (opcionais - não consultados)
    id: Optional[int] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Perfis e permissões (opcionais - não consultados)
    profiles: List[str] = []
    permissions: List[Dict[str, Any]] = []
    
    # Informações da sessão (opcional - não consultado)
    session_info: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
