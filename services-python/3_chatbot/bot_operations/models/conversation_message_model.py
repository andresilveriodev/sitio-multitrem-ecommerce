"""
Modelo SQLAlchemy para mensagens de conversa (histórico permanente).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from models.product_models import Base


class ConversationMessage(Base):
    """Mensagem de conversa persistida no PostgreSQL (permanente)."""
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)  # Telegram user_id
    content = Column(Text, nullable=False)
    message_type = Column(String(20), nullable=False, index=True)  # 'user', 'bot', 'system'
    created_at = Column(DateTime(timezone=False), nullable=False, default=datetime.utcnow, server_default=func.now())

    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, user_id='{self.user_id}', type='{self.message_type}')>"
