"""
Modelos SQLAlchemy para o schema chatbot
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, 
    Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
import uuid
import enum

from db_session import Base


# Enums
class Channel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"


class ConversationStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class MessageDirection(str, enum.Enum):
    IN = "in"
    OUT = "out"


class OutboxStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


# Tabelas do schema chatbot
class ChannelAccount(Base):
    """Conta de canal (WhatsApp/Telegram)"""
    __tablename__ = "channel_account"
    __table_args__ = {'schema': 'chatbot'}
    
    id = Column(Integer, primary_key=True, index=True)
    channel = Column(SQLEnum(Channel), nullable=False, index=True)
    external_user_id = Column(String(100), nullable=False, index=True)  # phone/chat_id
    display_name = Column(String(200), nullable=True)
    customer_id = Column(Integer, ForeignKey('commerce.customer.id'), nullable=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    # customer será relacionado via string para evitar import circular
    conversations = relationship("Conversation", back_populates="channel_account")


class Conversation(Base):
    """Conversa"""
    __tablename__ = "conversation"
    __table_args__ = {'schema': 'chatbot'}
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    channel_account_id = Column(Integer, ForeignKey('chatbot.channel_account.id'), nullable=False, index=True)
    status = Column(SQLEnum(ConversationStatus), nullable=False, default=ConversationStatus.OPEN, index=True)
    current_order_id = Column(PGUUID(as_uuid=True), ForeignKey('commerce.order.id'), nullable=True, index=True)
    context = Column(JSONB, nullable=True)  # Estado do fluxo
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relacionamentos
    channel_account = relationship("ChannelAccount", back_populates="conversations")
    # order será relacionado via string para evitar import circular
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Mensagem"""
    __tablename__ = "message"
    __table_args__ = {'schema': 'chatbot'}
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(PGUUID(as_uuid=True), ForeignKey('chatbot.conversation.id'), nullable=False, index=True)
    direction = Column(SQLEnum(MessageDirection), nullable=False, index=True)
    text = Column(Text, nullable=False)
    raw_payload = Column(JSONB, nullable=True)
    intent = Column(String(50), nullable=True, index=True)  # "catalog", "new_order", etc.
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relacionamentos
    conversation = relationship("Conversation", back_populates="messages")


class IntentRule(Base):
    """Regra de intenção (whitelist antes de chamar GPT)"""
    __tablename__ = "intent_rule"
    __table_args__ = {'schema': 'chatbot'}
    
    id = Column(Integer, primary_key=True, index=True)
    pattern = Column(Text, nullable=False)  # Texto/regex
    intent = Column(String(50), nullable=False, index=True)  # "catalog", "new_order", "confirm", "cancel", "help", "status"
    priority = Column(Integer, nullable=False, default=0)  # Maior = mais prioritário
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class Outbox(Base):
    """Fila de mensagens para envio"""
    __tablename__ = "outbox"
    __table_args__ = {'schema': 'chatbot'}
    
    id = Column(Integer, primary_key=True, index=True)
    channel = Column(SQLEnum(Channel), nullable=False, index=True)
    channel_account_id = Column(Integer, ForeignKey('chatbot.channel_account.id'), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    status = Column(SQLEnum(OutboxStatus), nullable=False, default=OutboxStatus.PENDING, index=True)
    tries = Column(Integer, default=0, nullable=False)
    next_try_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relacionamentos
    channel_account = relationship("ChannelAccount", foreign_keys=[channel_account_id])
