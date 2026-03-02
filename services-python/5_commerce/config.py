"""
Configurações do Commerce Service
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import structlog

logger = structlog.get_logger()

class Settings(BaseSettings):
    # Configurações básicas
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8002  # Porta para o Commerce Service
    LOG_LEVEL: str = "INFO"
    
    # Configurações de segurança
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    
    # Configurações do Keycloak
    KEYCLOAK_SERVER_URL: str = "https://auth.rendacontinua.com/auth"
    KEYCLOAK_REALM: str = "auth_sso"
    KEYCLOAK_CLIENT_ID: str = "auth_client"
    KEYCLOAK_CLIENT_SECRET: str = "e56cf527-d5d9-4b52-bd9f-1e87c8f288de"
    KEYCLOAK_VALIDATE_TOKEN: bool = True
    
    # Configurações do banco de dados
    DATABASE_URI: str = "postgresql://postgres:123456@localhost:5434/sitio_multitrem"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Configurações do Redis para cache
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 20
    
    # Configurações de cache
    CACHE_TTL_SECONDS: int = 300  # 5 minutos
    PRODUCT_CACHE_TTL_SECONDS: int = 600  # 10 minutos
    
    # Configurações de CORS
    CORS_ORIGINS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Configurações de rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # segundos
    
    # Configurações de auditoria
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info("Configurações do Commerce Service carregadas", 
                   database_pool_size=self.DATABASE_POOL_SIZE)

settings = Settings()
