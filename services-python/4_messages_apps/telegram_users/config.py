"""
Configurações do Telegram Service
"""

import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Configurações básicas
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8021"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    
    # Chatbot Service
    CHATBOT_SERVICE_URL: str = os.getenv("CHATBOT_SERVICE_URL", "http://localhost:8002")
    CHATBOT_SERVICE_TIMEOUT: int = int(os.getenv("CHATBOT_SERVICE_TIMEOUT", "30"))
    
    # User Service / Gateway (para autenticação)
    GATEWAY_SERVICE_URL: str = os.getenv("GATEWAY_SERVICE_URL", "http://localhost:8000")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
    
    # CORS - será processado manualmente
    _allowed_origins_str: str = ""
    
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Redis (opcional, para cache)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/10")
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Retorna lista de origens permitidas para CORS"""
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080")
        if isinstance(origins_str, str):
            return [origin.strip() for origin in origins_str.split(",") if origin.strip()]
        return origins_str if isinstance(origins_str, list) else []
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar campos extras do .env


settings = Settings()
