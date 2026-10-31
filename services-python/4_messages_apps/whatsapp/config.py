"""
Configurações do WhatsApp Gateway (somente canal Evolution).
"""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação gateway."""

    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8020"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Evolution webhook
    EVOLUTION_WEBHOOK_SECRET: str = os.getenv("EVOLUTION_WEBHOOK_SECRET", "")
    EVOLUTION_INSTANCE_NAME: str = os.getenv("EVOLUTION_INSTANCE_NAME", "sitio-multitrem")

    # Evolution outbound (sendText)
    EVOLUTION_API_URL: str = os.getenv("EVOLUTION_API_URL", "https://wpp-api.rendacontinua.com")
    EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "")
    EVOLUTION_SEND_TIMEOUT: int = int(os.getenv("EVOLUTION_SEND_TIMEOUT", "30"))

    # Chatbot (destino do forward)
    CHATBOT_SERVICE_URL: str = os.getenv("CHATBOT_SERVICE_URL", "http://localhost:8010")
    CHATBOT_SERVICE_TIMEOUT: int = int(os.getenv("CHATBOT_SERVICE_TIMEOUT", "30"))

    # Ops: buffer em memória dos últimos eventos
    RECENT_EVENTS_LIMIT: int = int(os.getenv("RECENT_EVENTS_LIMIT", "50"))
    DEDUPE_TTL_SECONDS: int = int(os.getenv("DEDUPE_TTL_SECONDS", "600"))

    ALLOWED_HOSTS: List[str] = ["*"]

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8003")
        if isinstance(origins_str, str):
            return [o.strip() for o in origins_str.split(",") if o.strip()]
        return list(origins_str) if origins_str else []

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
