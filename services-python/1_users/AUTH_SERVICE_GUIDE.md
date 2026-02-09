# Auth Service - Guia de Orientações

## 🎯 Visão Geral

O `user_service` é um **serviço de autenticação e autorização** que funciona como um **gateway de identidade** para o sistema E-commerce, integrando com Keycloak e fornecendo controle de acesso granular.

## 🔐 Funcionalidades Principais

### **1. Autenticação (Authentication)**
- **Login/Logout** via Keycloak
- **Validação de tokens JWT** 
- **Refresh automático** de tokens
- **Gerenciamento de sessões** locais
- **Suporte a CPF como username** (diferencial importante)

### **2. Cadastro de Usuários**
- **Criação via API** com validação completa
- **CPF obrigatório** como identificador principal
- **Verificação de duplicatas** (CPF/email)
- **Email de verificação** automático
- **Integração direta** com Keycloak Admin API

### **3. Autorização (Authorization)**
- **Sistema ACL** (Access Control List) completo
- **Perfis de usuário** configuráveis
- **Permissões granulares** por recurso/ação/escopo
- **Cache de permissões** para performance
- **Auditoria** de todas as ações

### **4. Integração Keycloak**
- **Autenticação remota** via Keycloak
- **Sincronização** de dados de usuário
- **Admin API** para criação/gestão de usuários
- **Token management** completo

## 🏗️ Arquitetura Técnica

### **Serviços Principais:**
- `AuthService`: Orquestra autenticação e sessões
- `KeycloakService`: Integração com Keycloak
- `ACLService`: Controle de acesso e permissões

### **Modelos de Dados:**
- `User` (ACL): Usuários locais sincronizados
- `Profile`: Perfis de acesso
- `Permission`: Permissões granulares
- `UserSession`: Sessões ativas
- `AuditLog`: Logs de auditoria

## 📡 Endpoints Principais

### **Autenticação:**
```
POST /api/v1/auth/login          # Login com CPF/email
POST /api/v1/auth/register       # Cadastro de usuário
POST /api/v1/auth/logout         # Logout
GET  /api/v1/auth/user           # Dados do usuário atual
GET  /api/v1/auth/check-user     # Verificar existência
```

### **ACL:**
```
POST /api/v1/acl/check           # Verificar permissão
GET  /api/v1/acl/permissions/summary/{id}  # Resumo de permissões
POST /api/v1/acl/profiles        # Criar perfil
POST /api/v1/acl/profiles/{id}/assign/{user_id}  # Atribuir perfil
```

## 🔄 Diferenças em Relação ao User Service

### **1. Foco e Responsabilidade**

| **Auth Service** | **User Service** |
|------------------|------------------|
| **Autenticação e Autorização** | **Gestão de Dados de Usuário** |
| Gateway de identidade | CRUD de perfis de usuário |
| Controle de acesso | Dados pessoais e preferências |
| Sessões e tokens | Configurações de conta |

### **2. Integração com Sistemas Externos**

| **Auth Service** | **User Service** |
|------------------|------------------|
| **Keycloak** (autenticação) | **Sistemas internos** |
| Admin API do Keycloak | APIs de negócio |
| Tokens JWT | Dados estruturados |

### **3. Modelo de Dados**

| **Auth Service** | **User Service** |
|------------------|------------------|
| `User` (sincronizado com Keycloak) | `User` (dados completos) |
| `Profile` (perfis de acesso) | `UserProfile` (preferências) |
| `Permission` (permissões) | `UserSettings` (configurações) |
| `UserSession` (sessões) | `UserPreferences` (preferências) |

### **4. Funcionalidades Específicas**

#### **Auth Service:**
- ✅ **CPF como username** (diferencial único)
- ✅ **Sistema ACL completo**
- ✅ **Integração Keycloak**
- ✅ **Auditoria de ações**
- ✅ **Cache de permissões**

#### **User Service:**
- ✅ **Gestão de perfil completo**
- ✅ **Preferências de usuário**
- ✅ **Configurações de conta**
- ✅ **Histórico de atividades**
- ✅ **Dados pessoais detalhados**

### **5. Fluxo de Trabalho**

#### **Auth Service:**
1. **Autenticação** → Keycloak
2. **Sincronização** → Banco local
3. **Verificação** → Permissões ACL
4. **Autorização** → Acesso aos recursos

#### **User Service:**
1. **Consulta** → Dados do usuário
2. **Atualização** → Perfil/Preferências
3. **Validação** → Dados de negócio
4. **Persistência** → Banco de dados

### **6. Casos de Uso**

#### **Auth Service:**
- Login/Logout do sistema
- Verificação de permissões
- Cadastro de novos usuários
- Controle de acesso a recursos
- Auditoria de ações

#### **User Service:**
- Edição de perfil pessoal
- Configuração de preferências
- Histórico de atividades
- Dados de conta
- Configurações de notificação

### **7. Dependências**

#### **Auth Service:**
- **Keycloak** (obrigatório)
- **PostgreSQL** (ACL e sessões)
- **Redis** (cache opcional)

#### **User Service:**
- **PostgreSQL** (dados de usuário)
- **Sistemas internos** (integração)

## 🎯 Resumo Executivo

O `auth_service` é um **serviço especializado em identidade e acesso** que:

1. **Centraliza a autenticação** via Keycloak
2. **Implementa controle de acesso granular** via ACL
3. **Gerencia o ciclo de vida** de usuários (cadastro, login, logout)
4. **Fornece auditoria completa** de ações
5. **Suporta CPF como identificador principal** (diferencial brasileiro)

Enquanto o `user_service` seria responsável por:
1. **Gestão de dados pessoais** dos usuários
2. **Preferências e configurações** de conta
3. **Perfis detalhados** de usuário
4. **Integração com sistemas de negócio**

## 🔧 Implementação Recomendada para User Service

### **Estrutura de Diretórios Sugerida:**

```
user_service/
├── main.py                    # Ponto de entrada
├── config.py                  # Configurações
├── requirements.txt           # Dependências
├── models/
│   ├── __init__.py
│   ├── user_profile.py       # Dados pessoais completos
│   ├── user_preferences.py   # Preferências de interface
│   ├── user_settings.py      # Configurações de conta
│   └── user_activity.py      # Histórico de atividades
├── services/
│   ├── __init__.py
│   ├── user_service.py       # Lógica de negócio
│   ├── profile_service.py    # Gestão de perfis
│   └── activity_service.py   # Histórico de atividades
├── routes/
│   ├── __init__.py
│   ├── profile.py            # CRUD de perfil
│   ├── preferences.py        # Gestão de preferências
│   └── activity.py           # Histórico de atividades
├── schemas/
│   ├── __init__.py
│   ├── profile.py            # Schemas Pydantic
│   ├── preferences.py        # Schemas Pydantic
│   └── activity.py           # Schemas Pydantic
├── utils/
│   ├── __init__.py
│   ├── validators.py         # Validações customizadas
│   └── file_upload.py        # Upload de avatar
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_routes.py
```

### **Modelos SQLAlchemy para User Service:**

```python
# models/user_profile.py
from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class UserProfile(Base):
    """Modelo para dados pessoais completos do usuário"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_service.users.id"), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    cpf = Column(String(14), nullable=True, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    country = Column(String(50), default="Brasil")
    postal_code = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    preferences = relationship("UserPreferences", back_populates="profile", uselist=False)
    settings = relationship("UserSettings", back_populates="profile", uselist=False)
    activities = relationship("UserActivity", back_populates="profile")

# models/user_preferences.py
class UserPreferences(Base):
    """Modelo para preferências de interface do usuário"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_service.users.id"), nullable=False, unique=True, index=True)
    language = Column(String(10), default="pt-BR", nullable=False)
    timezone = Column(String(50), default="America/Sao_Paulo", nullable=False)
    theme = Column(String(20), default="light", nullable=False)
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    email_notifications = Column(Boolean, default=True, nullable=False)
    push_notifications = Column(Boolean, default=False, nullable=False)
    sms_notifications = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    profile = relationship("UserProfile", back_populates="preferences")

# models/user_settings.py
class UserSettings(Base):
    """Modelo para configurações de conta do usuário"""
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_service.users.id"), nullable=False, unique=True, index=True)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    privacy_level = Column(String(20), default="public", nullable=False)
    data_sharing = Column(Boolean, default=True, nullable=False)
    marketing_emails = Column(Boolean, default=False, nullable=False)
    newsletter_subscription = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relacionamentos
    profile = relationship("UserProfile", back_populates="settings")

# models/user_activity.py
class UserActivity(Base):
    """Modelo para histórico de atividades do usuário"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_service.users.id"), nullable=False, index=True)
    activity_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relacionamentos
    profile = relationship("UserProfile", back_populates="activities")
```

### **Schemas Pydantic para User Service:**

```python
# schemas/profile.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import date, datetime

class UserProfileBase(BaseModel):
    """Schema base para perfil de usuário"""
    full_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: Optional[date] = None
    cpf: Optional[str] = Field(None, regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None

class UserProfileCreate(UserProfileBase):
    """Schema para criação de perfil"""
    pass

class UserProfileUpdate(BaseModel):
    """Schema para atualização de perfil"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    date_of_birth: Optional[date] = None
    cpf: Optional[str] = Field(None, regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None

class UserProfileResponse(UserProfileBase):
    """Schema para resposta de perfil"""
    id: int
    user_id: int
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# schemas/preferences.py
class UserPreferencesBase(BaseModel):
    """Schema base para preferências"""
    language: str = Field(default="pt-BR", max_length=10)
    timezone: str = Field(default="America/Sao_Paulo", max_length=50)
    theme: str = Field(default="light", max_length=20)
    notifications_enabled: bool = True
    email_notifications: bool = True
    push_notifications: bool = False
    sms_notifications: bool = False

class UserPreferencesCreate(UserPreferencesBase):
    """Schema para criação de preferências"""
    pass

class UserPreferencesUpdate(BaseModel):
    """Schema para atualização de preferências"""
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    theme: Optional[str] = Field(None, max_length=20)
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None

class UserPreferencesResponse(UserPreferencesBase):
    """Schema para resposta de preferências"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### **Serviços para User Service:**

```python
# services/user_service.py
from typing import Optional, List
from sqlalchemy.orm import Session
from models.user_profile import UserProfile
from models.user_preferences import UserPreferences
from models.user_settings import UserSettings
from models.user_activity import UserActivity
from schemas.profile import UserProfileCreate, UserProfileUpdate
from schemas.preferences import UserPreferencesCreate, UserPreferencesUpdate

class UserService:
    """Serviço principal para gestão de usuários"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Obtém perfil completo do usuário"""
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    async def create_user_profile(self, user_id: int, profile_data: UserProfileCreate) -> UserProfile:
        """Cria perfil de usuário"""
        profile = UserProfile(user_id=user_id, **profile_data.dict())
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    async def update_user_profile(self, user_id: int, profile_data: UserProfileUpdate) -> Optional[UserProfile]:
        """Atualiza perfil de usuário"""
        profile = await self.get_user_profile(user_id)
        if not profile:
            return None
        
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    async def get_user_preferences(self, user_id: int) -> Optional[UserPreferences]:
        """Obtém preferências do usuário"""
        return self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    
    async def update_user_preferences(self, user_id: int, preferences_data: UserPreferencesUpdate) -> Optional[UserPreferences]:
        """Atualiza preferências do usuário"""
        preferences = await self.get_user_preferences(user_id)
        if not preferences:
            # Criar preferências padrão se não existirem
            preferences = UserPreferences(user_id=user_id)
            self.db.add(preferences)
        
        update_data = preferences_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
        
        self.db.commit()
        self.db.refresh(preferences)
        return preferences
    
    async def get_user_activity_history(self, user_id: int, limit: int = 50) -> List[UserActivity]:
        """Obtém histórico de atividades do usuário"""
        return self.db.query(UserActivity)\
            .filter(UserActivity.user_id == user_id)\
            .order_by(UserActivity.created_at.desc())\
            .limit(limit)\
            .all()
    
    async def log_user_activity(self, user_id: int, activity_type: str, description: str = None, metadata: dict = None) -> UserActivity:
        """Registra atividade do usuário"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            metadata=metadata
        )
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity
```

## 📋 Checklist de Desenvolvimento

### **Auth Service (✅ Concluído)**
- [x] Integração com Keycloak
- [x] Sistema ACL
- [x] Cadastro de usuários
- [x] Autenticação com CPF
- [x] Auditoria
- [x] Cache de permissões

### **User Service (🔄 A Implementar)**
- [ ] **Estrutura Base**
  - [ ] Configuração do projeto
  - [ ] Conexão com banco de dados
  - [ ] Configuração de CORS e middleware
  - [ ] Health check endpoint

- [ ] **Modelos e Schemas**
  - [ ] Modelos SQLAlchemy (UserProfile, UserPreferences, UserSettings, UserActivity)
  - [ ] Schemas Pydantic para validação
  - [ ] Migrações do banco de dados
  - [ ] Relacionamentos entre tabelas

- [ ] **Serviços**
  - [ ] UserService (CRUD de perfis)
  - [ ] PreferencesService (gestão de preferências)
  - [ ] ActivityService (histórico de atividades)
  - [ ] FileUploadService (upload de avatar)

- [ ] **Rotas e Endpoints**
  - [ ] CRUD de perfil de usuário
  - [ ] Gestão de preferências
  - [ ] Configurações de conta
  - [ ] Histórico de atividades
  - [ ] Upload de arquivos

- [ ] **Integração**
  - [ ] Comunicação com auth_service
  - [ ] Validação de tokens JWT
  - [ ] Sincronização de dados
  - [ ] Tratamento de erros

- [ ] **Testes**
  - [ ] Testes unitários
  - [ ] Testes de integração
  - [ ] Testes de API
  - [ ] Cobertura de código

- [ ] **Documentação**
  - [ ] README.md
  - [ ] Documentação da API
  - [ ] Guias de uso
  - [ ] Exemplos de integração

## 🔗 Integração entre Serviços

### **Fluxo de Autenticação:**
1. **Frontend** → `auth_service` (login)
2. **auth_service** → Keycloak (validação)
3. **auth_service** → `user_service` (dados do perfil)
4. **Frontend** ← Dados completos do usuário

### **Fluxo de Atualização de Perfil:**
1. **Frontend** → `user_service` (atualização)
2. **user_service** → `auth_service` (sincronização se necessário)
3. **Frontend** ← Confirmação

## 📡 Endpoints Sugeridos para User Service

### **Perfil de Usuário:**
```http
GET    /api/v1/users/{user_id}/profile           # Obter perfil completo
POST   /api/v1/users/{user_id}/profile           # Criar perfil
PUT    /api/v1/users/{user_id}/profile           # Atualizar perfil
DELETE /api/v1/users/{user_id}/profile           # Deletar perfil
PATCH  /api/v1/users/{user_id}/profile/avatar    # Upload de avatar
```

### **Preferências:**
```http
GET    /api/v1/users/{user_id}/preferences       # Obter preferências
PUT    /api/v1/users/{user_id}/preferences       # Atualizar preferências
PATCH  /api/v1/users/{user_id}/preferences       # Atualizar parcialmente
```

### **Configurações:**
```http
GET    /api/v1/users/{user_id}/settings          # Obter configurações
PUT    /api/v1/users/{user_id}/settings          # Atualizar configurações
PATCH  /api/v1/users/{user_id}/settings          # Atualizar parcialmente
```

### **Atividades:**
```http
GET    /api/v1/users/{user_id}/activities        # Histórico de atividades
POST   /api/v1/users/{user_id}/activities        # Registrar atividade
GET    /api/v1/users/{user_id}/activities/stats  # Estatísticas de atividades
```

## 💡 Exemplos de Implementação

### **Exemplo de Rota para Perfil:**

```python
# routes/profile.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import structlog

from schemas.profile import UserProfileCreate, UserProfileUpdate, UserProfileResponse
from services.user_service import UserService
from utils.auth import get_current_user
from utils.file_upload import upload_avatar

logger = structlog.get_logger()
router = APIRouter(prefix="/users", tags=["User Profile"])

@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Obtém perfil completo do usuário"""
    try:
        # Verificar se usuário está consultando seu próprio perfil
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para acessar perfil de outro usuário"
            )
        
        user_service = UserService(db)
        profile = await user_service.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter perfil", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.put("/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: int,
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Atualiza perfil do usuário"""
    try:
        # Verificar permissão
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para atualizar perfil de outro usuário"
            )
        
        user_service = UserService(db)
        updated_profile = await user_service.update_user_profile(user_id, profile_data)
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )
        
        # Registrar atividade
        await user_service.log_user_activity(
            user_id=user_id,
            activity_type="PROFILE_UPDATED",
            description="Perfil atualizado"
        )
        
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao atualizar perfil", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.patch("/{user_id}/profile/avatar")
async def upload_user_avatar(
    user_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Upload de avatar do usuário"""
    try:
        # Verificar permissão
        if current_user["id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para atualizar avatar de outro usuário"
            )
        
        # Upload do arquivo
        avatar_url = await upload_avatar(file, user_id)
        
        # Atualizar perfil
        user_service = UserService(db)
        profile = await user_service.get_user_profile(user_id)
        
        if profile:
            profile.avatar_url = avatar_url
            db.commit()
        
        return {
            "message": "Avatar atualizado com sucesso",
            "avatar_url": avatar_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao fazer upload de avatar", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )
```

### **Exemplo de Validação de Token:**

```python
# utils/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx
import structlog

from config import settings

logger = structlog.get_logger()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://auth-service:8001/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Valida token JWT e retorna dados do usuário"""
    try:
        # Validar token com auth_service
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/api/v1/auth/user",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido ou expirado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user_data = response.json()
            return user_data
            
    except httpx.RequestError as e:
        logger.error("Erro de comunicação com auth_service", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de autenticação indisponível"
        )
    except Exception as e:
        logger.error("Erro ao validar token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

## ⚙️ Configuração do User Service

### **Variáveis de Ambiente:**

```bash
# Configurações do Serviço
SERVICE_NAME=user_service
HOST=0.0.0.0
PORT=8002
DEBUG=false
LOG_LEVEL=INFO

# Banco de Dados
DATABASE_URI=postgresql://postgres:123456@localhost:5434/sitio_multitrem
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# Integração com Auth Service
AUTH_SERVICE_URL=http://auth-service:8001
AUTH_SERVICE_TIMEOUT=30

# Upload de Arquivos
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=5242880  # 5MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif

# Cache
REDIS_URL=redis://localhost:6379/1
CACHE_TTL_SECONDS=300

# Segurança
SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "PATCH"]
CORS_ALLOW_HEADERS=["*"]
```

### **Configuração do Banco de Dados:**

```python
# config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Configurações do serviço
    service_name: str = "user_service"
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = False
    log_level: str = "INFO"
    
    # Banco de dados
    database_uri: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    
    # Integração com auth_service
    auth_service_url: str
    auth_service_timeout: int = 30
    
    # Upload de arquivos
    upload_dir: str = "/app/uploads"
    max_file_size: int = 5242880  # 5MB
    allowed_extensions: List[str] = ["jpg", "jpeg", "png", "gif"]
    
    # Cache
    redis_url: str = "redis://localhost:6379/1"
    cache_ttl_seconds: int = 300
    
    # Segurança
    secret_key: str
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    cors_allow_headers: List[str] = ["*"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### **Docker Compose para Desenvolvimento:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  user-service:
    build: .
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URI=postgresql://postgres:123456@postgres:5434/sitio_multitrem
      - AUTH_SERVICE_URL=http://auth-service:8001
      - REDIS_URL=redis://redis:6379/1
    volumes:
      - ./uploads:/app/uploads
    depends_on:
      - postgres
      - redis
      - auth-service
    networks:
      - ecommerce-network

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: sitio_multitrem
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 123456
    ports:
      - "5434:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ecommerce-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - ecommerce-network

  auth-service:
    image: auth-service:latest
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URI=postgresql://postgres:123456@postgres:5432/sitio_multitrem
    networks:
      - ecommerce-network

volumes:
  postgres_data:

networks:
  ecommerce-network:
    driver: bridge
```

## 🚀 Comandos de Desenvolvimento

### **Inicialização:**
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Inicializar banco de dados
python init_db.py

# Executar em desenvolvimento
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

### **Testes:**
```bash
# Executar testes
pytest

# Executar testes com cobertura
pytest --cov=app --cov-report=html

# Executar testes de integração
pytest tests/integration/
```

### **Docker:**
```bash
# Construir imagem
docker build -t user-service .

# Executar container
docker run -p 8002:8002 --env-file .env user-service

# Executar com docker-compose
docker-compose up -d
```

## 📚 Documentação Relacionada

- [README.md](./README.md) - Documentação principal
- [FRONTEND_REGISTRATION_GUIDE.md](./FRONTEND_REGISTRATION_GUIDE.md) - Guia frontend
- [README_KEYCLOAK_ADMIN.md](./README_KEYCLOAK_ADMIN.md) - Configuração Keycloak
- [USUARIOS_EXISTENTES_SSO.md](./USUARIOS_EXISTENTES_SSO.md) - Migração de usuários

---

**Última atualização:** Janeiro 2025  
**Versão:** 1.0.0  
**Autor:** Equipe E-commerce
