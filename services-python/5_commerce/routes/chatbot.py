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
from models.commerce import Customer, CustomerContact, OrderChannel, PriceProfile, Product
from sqlalchemy import func, and_
from decimal import Decimal
import structlog
from schemas.chatbot import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationWithMessages, MessageCreate, MessageResponse,
    ChatbotOrderCreate, ChatbotOrderItem,
    TelegramBulkOrdersCreate, TelegramNormalizedOrder, TelegramNormalizedOrderItem
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


@router.post("/orders/bulk", response_model=List[OrderResponse], status_code=201)
async def create_orders_from_telegram(
    bulk_data: TelegramBulkOrdersCreate,
    db: Session = Depends(get_db_session),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Cria múltiplos pedidos a partir de dados normalizados do chatbot Telegram
    Tenta identificar cliente/contato, mas cria temporário se não encontrar
    Requer autenticação Keycloak
    """
    logger = structlog.get_logger()
    created_orders = []
    
    for order_data in bulk_data.orders:
        try:
            # 1. Tenta identificar ou criar cliente
            customer = None
            contact = None
            
            # Tenta encontrar por nome do estabelecimento
            if order_data.establishment_name:
                customers = db.query(Customer).filter(
                    func.lower(Customer.name).contains(order_data.establishment_name.lower())
                ).all()
                
                if customers:
                    customer = customers[0]  # Pega o primeiro match
                    
                    # Tenta encontrar contato
                    if order_data.contact_name:
                        contact = db.query(CustomerContact).filter(
                            and_(
                                func.lower(CustomerContact.name).contains(order_data.contact_name.lower()),
                                CustomerContact.customer_id == customer.id
                            )
                        ).first()
            
            # Se não encontrou, tenta por telefone do contato
            if not customer and order_data.contact_phone:
                contact = CustomerService.get_customer_contact_by_phone(db, order_data.contact_phone)
                if contact:
                    customer = db.query(Customer).filter(Customer.id == contact.customer_id).first()
            
            # Se ainda não encontrou, tenta buscar cliente pelo telefone diretamente
            if not customer:
                phone_to_check = order_data.contact_phone or "+5562999999999"
                customer = CustomerService.get_customer_by_phone(db, phone_to_check)
            
            # Se ainda não encontrou, cria cliente temporário
            if not customer:
                # Determina perfil de preço
                price_profile = PriceProfile.RESTAURANTE_LOW
                if order_data.price_profile_hint:
                    hint = order_data.price_profile_hint.replace(',', '.')
                    if "2.50" in hint:
                        price_profile = PriceProfile.RESTAURANTE_LOW
                    elif "3.00" in hint:
                        price_profile = PriceProfile.RESTAURANTE_HIGH
                    elif "3.50" in hint:
                        price_profile = PriceProfile.RESTAURANTE_LOW
                    elif "4.00" in hint:
                        price_profile = PriceProfile.VAREJO
                
                customer_name = order_data.establishment_name or order_data.contact_name or "Cliente Temporário"
                phone_e164 = order_data.contact_phone or "+5562999999999"
                
                # Tentar criar cliente
                try:
                    customer = Customer(
                        name=customer_name,
                        phone_e164=phone_e164,
                        price_profile=price_profile,
                        notes=f"Cliente criado automaticamente do Telegram. Contato: {order_data.contact_name or 'N/A'}"
                    )
                    db.add(customer)
                    db.flush()
                except Exception as create_error:
                    # Se falhar por constraint única, tentar buscar novamente
                    if "UniqueViolation" in str(create_error) or "duplicate key" in str(create_error).lower():
                        logger.warning(
                            "Tentativa de criar cliente duplicado, buscando existente",
                            phone_e164=phone_e164,
                            error=str(create_error)
                        )
                        # Rollback da tentativa de criação
                        db.rollback()
                        # Buscar cliente existente
                        customer = CustomerService.get_customer_by_phone(db, phone_e164)
                        if not customer:
                            # Se ainda não encontrou, re-raise o erro original
                            raise
                    else:
                        # Se for outro erro, re-raise
                        raise
                
                # Cria contato se tiver nome
                if order_data.contact_name and order_data.contact_name != customer_name:
                    contact = CustomerContact(
                        customer_id=customer.id,
                        name=order_data.contact_name,
                        phone_e164=order_data.contact_phone,
                        active=True
                    )
                    db.add(contact)
                    db.flush()
            
            # 2. Prepara itens do pedido (filtra apenas produtos identificados)
            order_items = []
            unmatched_products = []
            
            for item in order_data.items:
                if item.product_id:
                    # Busca produto para verificar se é palito (para notes)
                    product = db.query(Product).filter(Product.id == item.product_id).first()
                    is_palito = product and ("palito" in product.name.lower() or (product.sku and "palito" in product.sku.lower()))
                    
                    order_items.append(OrderItemCreate(
                        product_id=item.product_id,
                        qty=Decimal(str(item.qty)),
                        unit_price=Decimal("0"),  # Será calculado
                        notes=item.product_name if is_palito else None
                    ))
                else:
                    unmatched_products.append(item.product_name)
            
            if not order_items:
                logger.warning(
                    "Nenhum produto identificado no pedido",
                    contact_name=order_data.contact_name,
                    establishment_name=order_data.establishment_name
                )
                continue  # Pula este pedido
            
            # 3. Cria pedido
            order_create = OrderCreate(
                customer_id=customer.id,
                channel=OrderChannel.TELEGRAM,
                price_list_id=1,  # Lista padrão
                notes=f"Pedido do Telegram. Contato: {order_data.contact_name or 'N/A'}. "
                      f"Estabelecimento: {order_data.establishment_name or 'N/A'}. "
                      f"Produtos não identificados: {', '.join(unmatched_products) if unmatched_products else 'Nenhum'}",
                items=order_items  # Passar items diretamente no construtor
            )
            
            order = OrderService.create_order(db, order_create)
            created_orders.append(order)
            
            # 4. Atualiza conversa se tiver conversation_id
            if bulk_data.conversation_id:
                ChatbotService.update_conversation(
                    db,
                    bulk_data.conversation_id,
                    ConversationUpdate(current_order_id=order.id)
                )
            
        except Exception as e:
            logger.error(
                "Erro ao criar pedido do Telegram",
                error=str(e),
                contact_name=order_data.contact_name,
                establishment_name=order_data.establishment_name
            )
            # Continua com próximo pedido
            continue
    
    if not created_orders:
        raise HTTPException(
            status_code=400,
            detail="Nenhum pedido foi criado. Verifique se os produtos foram identificados corretamente."
        )
    
    return created_orders
