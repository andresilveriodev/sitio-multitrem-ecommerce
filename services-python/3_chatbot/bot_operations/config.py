"""
Configurações do chatbot_service
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Configurações básicas
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8011  # Porta específica para o Chatbot Operations Service
    LOG_LEVEL: str = "INFO"
    
    # AI Service (serviço existente)
    AI_SERVICE_URL: str = "http://localhost:8005"
    AI_SERVICE_TIMEOUT: int = 30
    
    # Market Data Service
    MARKET_DATA_SERVICE_URL: str = "http://localhost:8000"
    MARKET_DATA_SERVICE_TIMEOUT: int = 10
    
    # Commerce Service
    COMMERCE_SERVICE_URL: str = "http://localhost:8002"
    COMMERCE_SERVICE_TIMEOUT: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Banco de dados
    DATABASE_URL: str = "postgresql://postgres:123456@localhost:5434/sitio_multitrem"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/9"
    
    # Telegram Bot Token (para autenticação de webhooks)
    TELEGRAM_BOT_TOKEN: str = ""
    
    # Configurações do Keycloak
    KEYCLOAK_AUTH_SERVER_URL: str = "https://auth.rendacontinua.com/auth"
    KEYCLOAK_REALM: str = "auth_sso"
    KEYCLOAK_RESOURCE: str = "auth_client"
    KEYCLOAK_PUBLIC_CLIENT: bool = False
    KEYCLOAK_BEARER_ONLY: bool = True
    KEYCLOAK_PRINCIPAL_ATTRIBUTE: str = "preferred_username"
    KEYCLOAK_CREDENTIALS_SECRET: str = "e56cf527-d5d9-4b52-bd9f-1e87c8f288de"
    KEYCLOAK_USE_RESOURCE_ROLE_MAPPINGS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
