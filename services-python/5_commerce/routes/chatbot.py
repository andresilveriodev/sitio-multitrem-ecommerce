"""
Rotas para chatbot - Requerem autenticação Keycloak
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID

from db_session import get_db_session
from auth.keycloak import get_current_user
from services.chatbot_service import ChatbotService
from services.order_service import OrderService
from services.customer_service import CustomerService
from schemas.chatbot import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationWithMessages, MessageCreate, MessageResponse,
    ChatbotOrderCreate, ChatbotOrderItem
)
from schemas.order import OrderResponse, OrderCreate, OrderItemCreate
from schemas.customer import CustomerResponse
from models.chatbot import Channel, ConversationStatus

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Busca uma conversa com suas mensagens
    Requer autenticação Keycloak
    """
    conversation = ChatbotService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    messages = ChatbotService.get_messages(db, conversation_id)
    
    # Converter para response
    from schemas.chatbot import ConversationWithMessages, MessageResponse
    return ConversationWithMessages(
        id=conversation.id,
        channel_account_id=conversation.channel_account_id,
        status=conversation.status,
        current_order_id=conversation.current_order_id,
        context=conversation.context,
        last_message_at=conversation.last_message_at,
        created_at=conversation.created_at,
        channel_account=conversation.channel_account,
        messages=[MessageResponse.model_validate(m) for m in messages]
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    channel: Channel = Query(...),
    external_user_id: str = Query(...),
    display_name: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cria ou obtém uma conversa para um canal
    Requer autenticação Keycloak
    """
    channel_account = ChatbotService.get_or_create_channel_account(
        db, channel.value, external_user_id, display_name, customer_id
    )
    
    conversation = ChatbotService.get_or_create_conversation(
        db, channel_account.id
    )
    
    return ConversationResponse.model_validate(conversation)


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    update_data: ConversationUpdate,
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Atualiza uma conversa (status, contexto, pedido atual)
    Requer autenticação Keycloak
    """
    conversation = ChatbotService.update_conversation(db, conversation_id, update_data)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    return ConversationResponse.model_validate(conversation)


@router.post("/messages", response_model=MessageResponse, status_code=201)
async def create_message(
    message: MessageCreate,
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cria uma mensagem em uma conversa
    Requer autenticação Keycloak
    """
    # Verificar se a conversa existe
    conversation = ChatbotService.get_conversation(db, message.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    db_message = ChatbotService.create_message(db, message)
    return MessageResponse.model_validate(db_message)


@router.get("/messages/{conversation_id}", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Lista mensagens de uma conversa
    Requer autenticação Keycloak
    """
    messages = ChatbotService.get_messages(db, conversation_id, limit)
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order_via_chatbot(
    order_data: ChatbotOrderCreate,
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cria um pedido via chatbot
    Aplica regras de precificação automaticamente
    Requer autenticação Keycloak
    """
    # Verificar se a conversa existe
    conversation = ChatbotService.get_conversation(db, order_data.conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    # Buscar cliente
    customer = CustomerService.get_customer(db, order_data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Determinar canal baseado na conversa
    channel_account = conversation.channel_account
    from models.commerce import OrderChannel
    order_channel = OrderChannel.WHATSAPP if channel_account.channel == Channel.WHATSAPP else OrderChannel.TELEGRAM
    
    # Criar pedido usando OrderService (que aplica regras automaticamente)
    # Converter items do chatbot para OrderItemCreate (unit_price será calculado)
    from decimal import Decimal
    order_items = [
        OrderItemCreate(
            product_id=item.product_id,
            qty=Decimal(str(item.qty)),
            unit_price=Decimal("0"),  # Será recalculado pelo OrderService
            notes=item.notes
        )
        for item in order_data.items
    ]
    
    order_create = OrderCreate(
        customer_id=order_data.customer_id,
        channel=order_channel,
        price_list_id=1,  # Será determinado pelo perfil do cliente
        delivery_address_id=order_data.delivery_address_id,
        notes=order_data.notes,
        items=order_items
    )
    
    try:
        order = OrderService.create_order(db, order_create)
        
        # Atualizar conversa com o pedido atual
        ChatbotService.update_conversation(
            db,
            order_data.conversation_id,
            ConversationUpdate(current_order_id=order.id)
        )
        
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/customers/phone/{phone_e164}", response_model=CustomerResponse)
async def get_customer_by_phone(
    phone_e164: str,
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Busca cliente por telefone (endpoint exclusivo para chatbot)
    Requer autenticação Keycloak
    """
    customer = CustomerService.get_customer_by_phone(db, phone_e164)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return customer
