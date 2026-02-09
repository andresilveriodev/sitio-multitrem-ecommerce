"""
Rate Limiter e Anti-Spam
Controla taxa de mensagens por usuário/conversa
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import structlog

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Rate limiter para prevenir spam e flood"""
    
    def __init__(self):
        # Configurações
        self.max_messages_per_minute = 10  # Máximo de mensagens por minuto
        self.max_messages_per_hour = 50  # Máximo de mensagens por hora
        self.cooldown_seconds = 5  # Cooldown entre mensagens repetidas
        
        # Armazenamento em memória (pode ser movido para Redis)
        self.message_counts: Dict[str, list] = defaultdict(list)  # user_id -> [timestamps]
        self.last_messages: Dict[str, tuple] = {}  # user_id -> (message, timestamp)
        self.blocked_users: Dict[str, datetime] = {}  # user_id -> block_until
        
    def check_rate_limit(self, user_id: str, message: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica rate limit para usuário
        
        Returns:
            Tuple[bool, Optional[str]]: (allowed, reason_if_blocked)
        """
        now = datetime.utcnow()
        
        # 1. Verifica se usuário está bloqueado
        if user_id in self.blocked_users:
            block_until = self.blocked_users[user_id]
            if now < block_until:
                remaining = (block_until - now).seconds
                logger.warning(
                    "Usuário bloqueado por rate limit",
                    user_id=user_id,
                    remaining_seconds=remaining
                )
                return False, f"Rate limit excedido. Tente novamente em {remaining} segundos."
            else:
                # Bloqueio expirou
                del self.blocked_users[user_id]
        
        # 2. Limpa mensagens antigas (mais de 1 hora)
        if user_id in self.message_counts:
            cutoff = now - timedelta(hours=1)
            self.message_counts[user_id] = [
                ts for ts in self.message_counts[user_id] if ts > cutoff
            ]
        
        # 3. Verifica cooldown de mensagens repetidas
        if user_id in self.last_messages:
            last_message, last_timestamp = self.last_messages[user_id]
            if message.lower().strip() == last_message.lower().strip():
                time_since = (now - last_timestamp).total_seconds()
                if time_since < self.cooldown_seconds:
                    logger.warning(
                        "Mensagem repetida muito rápida",
                        user_id=user_id,
                        time_since=time_since
                    )
                    return False, f"Aguarde {int(self.cooldown_seconds - time_since)} segundos antes de enviar a mesma mensagem."
        
        # 4. Verifica limite por minuto
        recent_messages = [
            ts for ts in self.message_counts[user_id]
            if ts > now - timedelta(minutes=1)
        ]
        
        if len(recent_messages) >= self.max_messages_per_minute:
            # Bloqueia por 1 minuto
            self.blocked_users[user_id] = now + timedelta(minutes=1)
            logger.warning(
                "Rate limit excedido (mensagens por minuto)",
                user_id=user_id,
                count=len(recent_messages)
            )
            return False, "Muitas mensagens. Aguarde 1 minuto antes de continuar."
        
        # 5. Verifica limite por hora
        hourly_messages = [
            ts for ts in self.message_counts[user_id]
            if ts > now - timedelta(hours=1)
        ]
        
        if len(hourly_messages) >= self.max_messages_per_hour:
            # Bloqueia por 10 minutos
            self.blocked_users[user_id] = now + timedelta(minutes=10)
            logger.warning(
                "Rate limit excedido (mensagens por hora)",
                user_id=user_id,
                count=len(hourly_messages)
            )
            return False, "Limite de mensagens por hora excedido. Aguarde 10 minutos."
        
        # 6. Registra mensagem
        self.message_counts[user_id].append(now)
        self.last_messages[user_id] = (message, now)
        
        return True, None
    
    def reset_user(self, user_id: str):
        """Reseta contadores de um usuário"""
        if user_id in self.message_counts:
            del self.message_counts[user_id]
        if user_id in self.last_messages:
            del self.last_messages[user_id]
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]
        logger.info("Contadores resetados para usuário", user_id=user_id)


# Instância global do rate limiter
rate_limiter = RateLimiter()
