"""
Configurações do Gateway Service
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Configurações básicas
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS
    # Permite configurar via variável de ambiente ou usar padrão
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Retorna lista de origens permitidas para CORS"""
        if self.CORS_ORIGINS:
            # Se configurado via env, usar lista separada por vírgula
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        
        # Em modo DEBUG, permitir muitas portas locais comuns para desenvolvimento
        if self.DEBUG:
            # Adiciona portas comuns de desenvolvimento
            origins = []
            ports = [3000, 3001, 3002, 5173, 5174, 5175, 8080, 8081, 4200, 4201, 5000, 5001]
            for port in ports:
                origins.extend([
                    f"http://localhost:{port}",
                    f"http://127.0.0.1:{port}",
                ])
            return origins
        
        # Em produção, lista restrita
        return [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:4200",
            "http://localhost:5173",
        ]
    
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ]
    
    # Microserviços URLs
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
    IMPORT_SERVICE_URL: str = os.getenv("IMPORT_SERVICE_URL", "http://localhost:8002")
    CHATBOT_SERVICE_URL: str = os.getenv("CHATBOT_SERVICE_URL", "http://localhost:8002")
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://localhost:8003")
    
    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60"))
    
    # Timeouts
    CONNECT_TIMEOUT: float = float(os.getenv("CONNECT_TIMEOUT", "10.0"))
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
    
    # Load Balancing
    ENABLE_LOAD_BALANCING: bool = os.getenv("ENABLE_LOAD_BALANCING", "false").lower() == "true"
    
    # Configurações do Keycloak
    KEYCLOAK_AUTH_SERVER_URL: str = os.getenv("KEYCLOAK_AUTH_SERVER_URL", "https://auth.rendacontinua.com/auth")
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "auth_sso")
    
    # Configurações do Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/1")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "1"))
    
    @property
    def KEYCLOAK_ISSUER(self) -> str:
        """Retorna o issuer do Keycloak baseado na URL e realm"""
        issuer = os.getenv("KEYCLOAK_ISSUER")
        if issuer:
            return issuer
        return f"{self.KEYCLOAK_AUTH_SERVER_URL}/realms/{self.KEYCLOAK_REALM}"
    
    @property
    def REDIS_URL_FALLBACK(self) -> str:
        """Retorna URL do Redis construída a partir de host/port/db se REDIS_URL não estiver definida"""
        if os.getenv("REDIS_URL"):
            return os.getenv("REDIS_URL")
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instância global das configurações
settings = Settings()
