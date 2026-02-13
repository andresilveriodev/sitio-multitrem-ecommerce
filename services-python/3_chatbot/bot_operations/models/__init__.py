"""
Modelos do chatbot_service
"""

from .conversation_context import (
    Message,
    MessageType,
    ConversationContext,
    UserPreferences,
    SessionData
)

__all__ = [
    "Message",
    "MessageType", 
    "ConversationContext",
    "UserPreferences",
    "SessionData"
]
