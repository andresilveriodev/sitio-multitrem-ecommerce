"""
Schemas Pydantic para chatbot
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from models.chatbot import Channel, ConversationStatus, MessageDirection


class ChannelAccountResponse(BaseModel):
    """Resposta de conta de canal"""
    id: int
    channel: Channel
    external_user_id: str
    display_name: Optional[str] = None
    customer_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """Base para conversa"""
    channel_account_id: int
    status: ConversationStatus = ConversationStatus.OPEN
    current_order_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None


class ConversationCreate(ConversationBase):
    """Criação de conversa"""
    pass


class ConversationUpdate(BaseModel):
    """Atualização de conversa"""
    status: Optional[ConversationStatus] = None
    current_order_id: Optional[UUID] = None
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(ConversationBase):
    """Resposta de conversa"""
    id: UUID
    last_message_at: Optional[datetime] = None
    created_at: datetime
    channel_account: Optional[ChannelAccountResponse] = None
    
    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    """Base para mensagem"""
    conversation_id: UUID
    direction: MessageDirection
    text: str
    raw_payload: Optional[Dict[str, Any]] = None
    intent: Optional[str] = None


class MessageCreate(MessageBase):
    """Criação de mensagem"""
    pass


class MessageResponse(MessageBase):
    """Resposta de mensagem"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Conversa com mensagens"""
    messages: List[MessageResponse] = []


class ChatbotOrderItem(BaseModel):
    """Item de pedido simplificado para chatbot (preço será calculado)"""
    product_id: int
    qty: float
    notes: Optional[str] = None


class ChatbotOrderCreate(BaseModel):
    """Criação de pedido via chatbot"""
    conversation_id: UUID
    customer_id: int
    items: List[ChatbotOrderItem] = Field(..., min_items=1)
    delivery_address_id: Optional[int] = None
    notes: Optional[str] = None


class TelegramNormalizedOrderItem(BaseModel):
    """Item de pedido já normalizado pelo chatbot"""
    product_id: Optional[int] = None  # Se None, produto não identificado
    product_name: str  # Nome do produto original
    qty: float


class TelegramNormalizedOrder(BaseModel):
    """Pedido normalizado pelo chatbot"""
    contact_name: Optional[str] = None  # Nome do contato (ex: "Dilma", sem "Dona")
    establishment_name: Optional[str] = None  # Nome do estabelecimento (ex: "Recanto Verde")
    contact_phone: Optional[str] = None  # Telefone do contato (se disponível)
    items: List[TelegramNormalizedOrderItem] = Field(..., min_items=1)
    price_profile_hint: Optional[str] = None  # Dica do chatbot sobre perfil (R$ 2,50 = RESTAURANTE_LOW)


class TelegramBulkOrdersCreate(BaseModel):
    """Múltiplos pedidos normalizados do Telegram"""
    conversation_id: Optional[UUID] = None
    orders: List[TelegramNormalizedOrder] = Field(..., min_items=1)