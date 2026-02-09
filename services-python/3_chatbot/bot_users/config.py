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
    PORT: int = 8002  # Porta específica para o Chatbot Service
    LOG_LEVEL: str = "INFO"
    
    # AI Service (serviço existente)
    AI_SERVICE_URL: str = "http://localhost:8003"
    AI_SERVICE_TIMEOUT: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Banco de dados
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/sitio_multitrem"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/9"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
