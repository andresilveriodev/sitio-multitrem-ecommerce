"""
Serviço de gerenciamento de contexto de conversas.
Mensagens são persistidas permanentemente no PostgreSQL; Redis é usado como cache/fallback.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import redis.asyncio as redis
import structlog
from sqlalchemy import select

from config import settings
from models.conversation_context import (
    ConversationContext,
    Message,
    MessageType,
    UserPreferences,
    SessionData
)

try:
    from services.database_service import database_service
    from models.conversation_message_model import ConversationMessage
except ImportError:
    database_service = None
    ConversationMessage = None

logger = structlog.get_logger(__name__)


class ContextService:
    """Serviço de gerenciamento de contexto"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.active_sessions: Dict[str, SessionData] = {}
        
    async def connect(self):
        """Conecta ao Redis"""
        try:
            self.redis = redis.from_url(settings.REDIS_URL)
            await self.redis.ping()
            logger.info("ContextService connected to Redis")
        except Exception as e:
            logger.error(f"Error connecting ContextService to Redis: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Desconecta do Redis"""
        if self.redis:
            await self.redis.close()
    
    def _get_context_key(self, user_id: str) -> str:
        """Gera chave para contexto do usuário"""
        return f"context:{user_id}"
    
    def _get_session_key(self, session_id: str) -> str:
        """Gera chave para sessão"""
        return f"session:{session_id}"
    
    def _get_preferences_key(self, user_id: str) -> str:
        """Gera chave para preferências do usuário"""
        return f"preferences:{user_id}"

    def _get_order_state_key(self, user_id: str) -> str:
        """Gera chave para estado do pedido em construção (compartilhado entre workers)."""
        return f"order_state:{user_id}"

    async def get_order_state(self, user_id: str) -> Optional[Dict]:
        """Retorna o estado do pedido em construção (persistido no Redis)."""
        if not self.redis:
            return None
        try:
            data = await self.redis.get(self._get_order_state_key(user_id))
            if not data:
                return None
            raw = data.decode("utf-8") if isinstance(data, bytes) else data
            return json.loads(raw)
        except Exception as e:
            logger.warning("Falha ao carregar order_state do Redis", user_id=user_id, error=str(e))
            return None

    async def save_order_state(self, user_id: str, state: Dict) -> bool:
        """Persiste o estado do pedido no Redis (compartilhado entre workers)."""
        if not self.redis:
            return False
        try:
            await self.redis.setex(
                self._get_order_state_key(user_id),
                7200,  # 2 horas
                json.dumps(state, ensure_ascii=False),
            )
            return True
        except Exception as e:
            logger.warning("Falha ao salvar order_state no Redis", user_id=user_id, error=str(e))
            return False

    async def clear_order_state(self, user_id: str) -> bool:
        """Remove o estado do pedido do Redis."""
        if not self.redis:
            return False
        try:
            await self.redis.delete(self._get_order_state_key(user_id))
            return True
        except Exception as e:
            logger.warning("Falha ao limpar order_state no Redis", user_id=user_id, error=str(e))
            return False

    async def create_session(self, user_id: str, metadata: Dict = None) -> SessionData:
        """Cria nova sessão para o usuário"""
        session_id = str(uuid.uuid4())
        session_data = SessionData(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # Armazena no Redis
        if self.redis:
            try:
                await self.redis.setex(
                    self._get_session_key(session_id),
                    3600,  # 1 hora
                    session_data.json()
                )
            except Exception as e:
                logger.error(f"Erro ao salvar sessão no Redis: {e}")
        
        # Armazena em memória
        self.active_sessions[session_id] = session_data
        
        logger.info(f"Nova sessão criada: {session_id} para usuário {user_id}")
        return session_data
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Busca sessão por ID"""
        # Primeiro tenta memória
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Depois tenta Redis
        if self.redis:
            try:
                session_data = await self.redis.get(self._get_session_key(session_id))
                if session_data:
                    session = SessionData.parse_raw(session_data)
                    # Atualiza memória
                    self.active_sessions[session_id] = session
                    return session
            except Exception as e:
                logger.error(f"Erro ao buscar sessão no Redis: {e}")
        
        return None
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Atualiza atividade da sessão"""
        session = await self.get_session(session_id)
        if session:
            session.last_activity = datetime.utcnow()
            
            # Atualiza Redis
            if self.redis:
                try:
                    await self.redis.setex(
                        self._get_session_key(session_id),
                        3600,
                        session.json()
                    )
                except Exception as e:
                    logger.error(f"Erro ao atualizar sessão no Redis: {e}")
            
            # Atualiza memória
            self.active_sessions[session_id] = session
            return True
        
        return False
    
    async def end_session(self, session_id: str) -> bool:
        """Finaliza sessão"""
        # Remove do Redis
        if self.redis:
            try:
                await self.redis.delete(self._get_session_key(session_id))
            except Exception as e:
                logger.error(f"Erro ao remover sessão do Redis: {e}")
        
        # Remove da memória
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        logger.info(f"Sessão finalizada: {session_id}")
        return True
    
    async def get_conversation_context(self, user_id: str) -> ConversationContext:
        """Busca contexto de conversa do usuário. Preferência: PostgreSQL (permanente), depois Redis (cache)."""
        # 1) PostgreSQL: histórico permanente (últimas 50 mensagens)
        if database_service and ConversationMessage and getattr(database_service, "is_connected", False):
            try:
                async with database_service.get_session() as session:
                    result = await session.execute(
                        select(ConversationMessage)
                        .where(ConversationMessage.user_id == user_id)
                        .order_by(ConversationMessage.created_at.desc())
                        .limit(50)
                    )
                    rows = list(result.scalars().all())
                    rows.reverse()  # ordem cronológica (mais antiga primeiro)
                    messages = []
                    for row in rows:
                        msg_type = MessageType(row.message_type) if row.message_type in ("user", "bot", "system") else MessageType.USER
                        messages.append(Message(
                            id=str(row.id),
                            user_id=row.user_id,
                            content=row.content or "",
                            timestamp=row.created_at,
                            message_type=msg_type,
                        ))
                    if messages:
                        return ConversationContext(
                            user_id=user_id,
                            session_id=str(uuid.uuid4()),
                            message_history=messages,
                            last_interaction=messages[-1].timestamp if messages else datetime.utcnow(),
                        )
            except Exception as e:
                logger.warning("Falha ao carregar histórico do PostgreSQL, usando Redis", user_id=user_id, error=str(e))

        # 2) Redis (cache/fallback)
        if self.redis:
            try:
                context_data = await self.redis.get(self._get_context_key(user_id))
                if context_data:
                    raw = context_data.decode("utf-8") if isinstance(context_data, bytes) else context_data
                    return ConversationContext.parse_raw(raw)
            except Exception as e:
                logger.error(f"Erro ao buscar contexto no Redis: {e}")

        return ConversationContext(
            user_id=user_id,
            session_id=str(uuid.uuid4())
        )
    
    async def save_conversation_context(self, context: ConversationContext) -> bool:
        """Salva contexto de conversa"""
        context.updated_at = datetime.utcnow()
        
        if self.redis:
            try:
                await self.redis.setex(
                    self._get_context_key(context.user_id),
                    7200,  # 2 horas
                    context.json()
                )
                return True
            except Exception as e:
                logger.error(f"Erro ao salvar contexto no Redis: {e}")
                return False
        
        return True
    
    async def add_message_to_context(self, user_id: str, message: Message) -> bool:
        """Adiciona mensagem ao contexto. Persiste no PostgreSQL (permanente) e no Redis (cache)."""
        saved_to_db = False
        # 1) PostgreSQL: persistência permanente
        if database_service and ConversationMessage and getattr(database_service, "is_connected", False):
            try:
                async with database_service.get_session() as session:
                    row = ConversationMessage(
                        user_id=user_id,
                        content=message.content or "",
                        message_type=message.message_type.value if hasattr(message.message_type, "value") else str(message.message_type),
                    )
                    session.add(row)
                    await session.commit()
                    saved_to_db = True
                    logger.debug("Mensagem salva no PostgreSQL", user_id=user_id, type=message.message_type.value, content_len=len(message.content or ""))
            except Exception as e:
                content_preview = (message.content or "")[:100].replace("\n", " ")
                logger.warning(
                    "Falha ao salvar mensagem no PostgreSQL",
                    user_id=user_id,
                    error=str(e),
                    content_len=len(message.content or ""),
                    content_preview=content_preview,
                )

        # 2) Redis: atualizar cache (se salvou no DB, recarregar do DB para não duplicar; senão append)
        context = await self.get_conversation_context(user_id)
        if not saved_to_db:
            context.message_history.append(message)
        # se saved_to_db, o get_conversation_context já trouxe a mensagem do DB
        context.last_interaction = datetime.utcnow()
        if len(context.message_history) > 50:
            context.message_history = context.message_history[-50:]
        if self.redis:
            await self.save_conversation_context(context)
        return True
    
    async def update_context_summary(self, user_id: str, summary: str) -> bool:
        """Atualiza resumo do contexto"""
        context = await self.get_conversation_context(user_id)
        context.context_summary = summary
        return await self.save_conversation_context(context)
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Busca preferências do usuário"""
        if self.redis:
            try:
                prefs_data = await self.redis.get(self._get_preferences_key(user_id))
                if prefs_data:
                    return UserPreferences.parse_raw(prefs_data)
            except Exception as e:
                logger.error(f"Erro ao buscar preferências no Redis: {e}")
        
        # Retorna preferências padrão
        return UserPreferences(user_id=user_id)
    
    async def save_user_preferences(self, preferences: UserPreferences) -> bool:
        """Salva preferências do usuário"""
        preferences.updated_at = datetime.utcnow()
        
        if self.redis:
            try:
                await self.redis.setex(
                    self._get_preferences_key(preferences.user_id),
                    86400,  # 24 horas
                    preferences.json()
                )
                return True
            except Exception as e:
                logger.error(f"Erro ao salvar preferências no Redis: {e}")
                return False
        
        return True
    
    async def detect_topic_change(self, user_id: str, new_message: str) -> Tuple[bool, str]:
        """Detecta mudança de tópico na conversa"""
        context = await self.get_conversation_context(user_id)
        
        if not context.message_history:
            return True, "general"
        
        # Análise simples de mudança de tópico
        last_messages = context.message_history[-3:]  # Últimas 3 mensagens
        last_content = " ".join([msg.content.lower() for msg in last_messages])
        
        # Palavras-chave para diferentes tópicos
        topic_keywords = {
            "trading": ["ação", "ações", "bolsa", "investir", "compra", "venda", "preço"],
            "technical": ["indicador", "gráfico", "análise", "tendência", "suporte", "resistência"],
            "fundamental": ["empresa", "lucro", "receita", "dividendo", "balanço"],
            "general": ["oi", "olá", "ajuda", "como", "quando", "onde"]
        }
        
        # Verifica se há mudança de tópico
        current_topic = context.current_topic
        for topic, keywords in topic_keywords.items():
            if any(keyword in new_message.lower() for keyword in keywords):
                if topic != current_topic:
                    return True, topic
        
        return False, current_topic
    
    async def cleanup_expired_sessions(self) -> int:
        """Limpa sessões expiradas"""
        expired_sessions = []
        now = datetime.utcnow()
        
        for session_id, session in self.active_sessions.items():
            if now - session.last_activity > timedelta(hours=1):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.end_session(session_id)
        
        return len(expired_sessions)


# Instância global do serviço de contexto
context_service = ContextService()
