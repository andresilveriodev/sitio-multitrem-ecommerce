from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from services.chatbot_service import chatbot_service
from models.conversation import Conversation, Message
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Schemas Pydantic
class ConversationCreate(BaseModel):
    user_id: int
    username: str
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    status: str
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    conversation_id: int
    content: str
    role: str = "user"

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    content: str
    role: str
    created_at: str
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    conversation_id: int
    message: str
    provider: Optional[str] = None  # 'openai', 'deepseek', 'ollama'
    model: Optional[str] = None  # Modelo específico

class ChatResponse(BaseModel):
    user_message: str
    ai_response: str
    conversation_id: int



# Endpoints de Conversa
@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(conversation_data: ConversationCreate):
    """
    Cria uma nova conversa
    """
    try:
        conversation = chatbot_service.create_conversation(
            user_id=conversation_data.user_id,
            username=conversation_data.username,
            title=conversation_data.title
        )
        return conversation
    except Exception as e:
        logger.error(f"Erro ao criar conversa: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int):
    """
    Busca conversa por ID
    """
    conversation = chatbot_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return conversation

@router.get("/users/{user_id}/conversations", response_model=List[ConversationResponse])
def get_user_conversations(user_id: int):
    """
    Busca todas as conversas de um usuário
    """
    conversations = chatbot_service.get_user_conversations(user_id)
    return conversations

# Endpoints de Mensagem
@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(conversation_id: int):
    """
    Busca todas as mensagens de uma conversa
    """
    # Verifica se a conversa existe
    conversation = chatbot_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    
    messages = chatbot_service.get_conversation_messages(conversation_id)
    return messages

# Endpoint principal do chat
@router.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """
    Processa uma mensagem do usuário e retorna resposta da IA
    """
    print("=" * 60)
    print("CHEGOU NO /chatbot/chat")
    print(f"Conversation ID: {chat_request.conversation_id}")
    print(f"Message: {chat_request.message[:50]}...")
    print(f"Provider: {chat_request.provider}")
    print(f"Model: {chat_request.model}")
    print("=" * 60)
    
    try:
        # Verifica se a conversa existe
        print("[*] Verificando se conversa existe...")
        conversation = chatbot_service.get_conversation(chat_request.conversation_id)
        if not conversation:
            logger.error(f"[CHATBOT] Conversa {chat_request.conversation_id} não encontrada")
            raise HTTPException(status_code=404, detail="Conversa não encontrada")
        
        print(f"[OK] Conversa encontrada: user_id={conversation.user_id}")
        
        # Processa a mensagem
        print("[*] Processando mensagem com chatbot_service...")
        ai_response = await chatbot_service.process_user_message(
            conversation_id=chat_request.conversation_id,
            user_message=chat_request.message,
            provider=chat_request.provider,
            model=chat_request.model
        )
        
        print(f"[OK] Resposta recebida: {ai_response[:100] if ai_response else 'VAZIA'}...")
        
        return ChatResponse(
            user_message=chat_request.message,
            ai_response=ai_response,
            conversation_id=chat_request.conversation_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        error_type = type(e).__name__
        
        print(f"[ERRO] Erro capturado no /chatbot/chat:")
        print(f"  Tipo: {error_type}")
        print(f"  Mensagem: {error_msg}")
        print(f"  Traceback: {error_trace}")
        
        logger.error(f"[CHATBOT] ERRO no chat: {error_msg}")
        logger.error(f"[CHATBOT] Tipo: {error_type}")
        logger.error(f"[CHATBOT] Traceback completo: {error_trace}")
        
        raise HTTPException(status_code=500, detail=f"Erro: {error_msg} (Tipo: {error_type})")

@router.get("/health")
def health_check():
    """
    Endpoint de verificação de saúde
    """
    return {"status": "healthy", "service": "chatbot"}