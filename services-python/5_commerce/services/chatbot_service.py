"""
Serviço de chatbot
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
import structlog

from models.chatbot import Conversation, Message, ChannelAccount, ConversationStatus, MessageDirection
from schemas.chatbot import ConversationCreate, ConversationUpdate, MessageCreate

logger = structlog.get_logger()


class ChatbotService:
    """Serviço para gerenciar conversas e mensagens do chatbot"""
    
    @staticmethod
    def get_or_create_channel_account(
        db: Session,
        channel: str,
        external_user_id: str,
        display_name: Optional[str] = None,
        customer_id: Optional[int] = None
    ) -> ChannelAccount:
        """Obtém ou cria uma conta de canal"""
        channel_account = db.query(ChannelAccount).filter(
            ChannelAccount.channel == channel,
            ChannelAccount.external_user_id == external_user_id
        ).first()
        
        if not channel_account:
            channel_account = ChannelAccount(
                channel=channel,
                external_user_id=external_user_id,
                display_name=display_name,
                customer_id=customer_id
            )
            db.add(channel_account)
            db.commit()
            db.refresh(channel_account)
            logger.info("Conta de canal criada", 
                       channel_account_id=channel_account.id,
                       channel=channel)
        
        return channel_account
    
    @staticmethod
    def get_or_create_conversation(
        db: Session,
        channel_account_id: int,
        status: ConversationStatus = ConversationStatus.OPEN
    ) -> Conversation:
        """Obtém ou cria uma conversa"""
        conversation = db.query(Conversation).filter(
            Conversation.channel_account_id == channel_account_id,
            Conversation.status == ConversationStatus.OPEN
        ).order_by(Conversation.created_at.desc()).first()
        
        if not conversation:
            conversation = Conversation(
                channel_account_id=channel_account_id,
                status=status
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info("Conversa criada", conversation_id=conversation.id)
        
        return conversation
    
    @staticmethod
    def get_conversation(db: Session, conversation_id: UUID) -> Optional[Conversation]:
        """Busca uma conversa por ID"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    @staticmethod
    def get_conversations_by_channel_account(
        db: Session,
        channel_account_id: int,
        limit: int = 10
    ) -> List[Conversation]:
        """Lista conversas de uma conta de canal"""
        return db.query(Conversation).filter(
            Conversation.channel_account_id == channel_account_id
        ).order_by(Conversation.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def update_conversation(
        db: Session,
        conversation_id: UUID,
        update_data: ConversationUpdate
    ) -> Optional[Conversation]:
        """Atualiza uma conversa"""
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(conversation, field, value)
        
        db.commit()
        db.refresh(conversation)
        logger.info("Conversa atualizada", conversation_id=conversation_id)
        return conversation
    
    @staticmethod
    def create_message(db: Session, message: MessageCreate) -> Message:
        """Cria uma mensagem"""
        db_message = Message(**message.model_dump())
        db.add(db_message)
        
        # Atualiza last_message_at da conversa
        conversation = db.query(Conversation).filter(
            Conversation.id == message.conversation_id
        ).first()
        if conversation:
            from datetime import datetime
            conversation.last_message_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_message)
        logger.info("Mensagem criada", 
                   message_id=db_message.id,
                   conversation_id=message.conversation_id)
        return db_message
    
    @staticmethod
    def get_messages(
        db: Session,
        conversation_id: UUID,
        limit: int = 50
    ) -> List[Message]:
        """Lista mensagens de uma conversa"""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit).all()
