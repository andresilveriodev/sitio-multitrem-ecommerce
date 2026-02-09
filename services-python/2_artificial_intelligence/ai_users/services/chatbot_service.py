from sqlalchemy.orm import Session
from models.conversation import Conversation, Message
from app.db import Session as DBSession
from services.ai_service import ai_service
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ChatbotService:
    def __init__(self):
        self.db_session = DBSession
    

    
    def create_conversation(self, user_id: int, username: str, title: Optional[str] = None) -> Conversation:
        """
        Cria uma nova conversa
        """
        try:
            conversation = Conversation(
                user_id=user_id,
                username=username,
                title=title or "Nova Conversa"
            )
            self.db_session.add(conversation)
            self.db_session.commit()
            self.db_session.refresh(conversation)
            return conversation
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Erro ao criar conversa: {str(e)}")
            raise
    
    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """
        Busca conversa por ID
        """
        return self.db_session.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def get_user_conversations(self, user_id: int) -> List[Conversation]:
        """
        Busca todas as conversas de um usuário
        """
        return self.db_session.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.status == 'active'
        ).order_by(Conversation.updated_at.desc()).all()
    
    def add_message(self, conversation_id: int, content: str, role: str, metadata: Optional[Dict] = None) -> Message:
        """
        Adiciona uma mensagem à conversa
        """
        try:
            message = Message(
                conversation_id=conversation_id,
                content=content,
                role=role,
                metadata=metadata
            )
            self.db_session.add(message)
            self.db_session.commit()
            self.db_session.refresh(message)
            return message
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Erro ao adicionar mensagem: {str(e)}")
            raise
    
    def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        """
        Busca todas as mensagens de uma conversa
        """
        return self.db_session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()
    
    async def process_user_message(
        self, 
        conversation_id: int, 
        user_message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Processa uma mensagem do usuário e gera resposta da IA
        
        Args:
            conversation_id: ID da conversa
            user_message: Mensagem do usuário
            provider: Provedor de IA ('openai', 'deepseek', 'ollama'). Se None, usa o padrão.
            model: Modelo específico a ser usado. Se None, usa o padrão do provedor.
        """
        try:
            logger.info(f"[CHATBOT_SERVICE] Processando mensagem - conversation_id={conversation_id}, provider={provider}, model={model}")
            
            # Adiciona mensagem do usuário
            logger.info(f"[CHATBOT_SERVICE] Adicionando mensagem do usuário...")
            self.add_message(conversation_id, user_message, "user")
            
            # Busca histórico da conversa
            logger.info(f"[CHATBOT_SERVICE] Buscando histórico da conversa...")
            messages = self.get_conversation_messages(conversation_id)
            logger.info(f"[CHATBOT_SERVICE] Histórico: {len(messages)} mensagens")
            
            # Converte para formato da API
            ai_messages = []
            for msg in messages:
                ai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Gera resposta da IA com o provider especificado (ou padrão)
            logger.info(f"[CHATBOT_SERVICE] Chamando ai_service.generate_response...")
            logger.info(f"[CHATBOT_SERVICE] Parâmetros: provider={provider}, model={model}, messages_count={len(ai_messages)}")
            
            ai_response = await ai_service.generate_response(
                messages=ai_messages,
                provider=provider,
                model=model
            )
            
            logger.info(f"[CHATBOT_SERVICE] Resposta recebida: {ai_response[:100] if ai_response else 'VAZIA'}...")
            
            # Adiciona resposta da IA
            logger.info(f"[CHATBOT_SERVICE] Adicionando resposta da IA...")
            self.add_message(conversation_id, ai_response, "assistant")
            
            return ai_response
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            error_msg = str(e)
            error_type = type(e).__name__
            
            logger.error(f"[CHATBOT_SERVICE] ERRO ao processar mensagem: {error_msg}")
            logger.error(f"[CHATBOT_SERVICE] Tipo: {error_type}")
            logger.error(f"[CHATBOT_SERVICE] Conversation ID: {conversation_id}")
            logger.error(f"[CHATBOT_SERVICE] Provider: {provider}, Model: {model}")
            logger.error(f"[CHATBOT_SERVICE] Traceback completo: {error_trace}")
            
            raise

# Instância global do serviço
chatbot_service = ChatbotService()