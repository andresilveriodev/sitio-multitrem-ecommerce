"""
Modelos para gerenciamento de contexto de conversas
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class MessageType(str, Enum):
    """Tipos de mensagem"""
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class Message(BaseModel):
    """Modelo de mensagem para contexto"""
    id: str
    user_id: str
    content: str
    timestamp: datetime
    message_type: MessageType
    requires_ai: bool = False
    ai_provider_used: Optional[str] = None
    context_added: Dict = Field(default_factory=dict)
    response_time: Optional[float] = None
    conversation_id: Optional[int] = None  # ID da conversa no AI Service


class ConversationContext(BaseModel):
    """Contexto de conversa do usuário"""
    user_id: str
    session_id: str
    current_topic: str = "general"
    message_history: List[Message] = Field(default_factory=list)
    context_summary: str = ""  # Resumo do contexto atual
    conversation_metadata: Dict = Field(default_factory=dict)
    cache_hits: int = 0
    last_interaction: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserPreferences(BaseModel):
    """Preferências do usuário para contexto"""
    user_id: str
    language: str = "pt-BR"
    response_style: str = "concise"  # 'concise', 'detailed', 'technical'
    auto_cache: bool = True
    max_context_length: int = 1000
    conversation_preferences: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionData(BaseModel):
    """Dados da sessão do usuário"""
    session_id: str
    user_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


