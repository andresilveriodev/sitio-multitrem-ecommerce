"""
Sistema de confirmação para comandos críticos
"""

import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ConfirmationRequest:
    """Requisição de confirmação"""
    id: str
    user_id: str
    command_id: str
    parameters: Dict[str, Any]
    message: str
    risk_level: str
    created_at: datetime
    expires_at: datetime
    status: str = "pending"  # pending, confirmed, cancelled, expired
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ConfirmationManager:
    """Gerenciador de confirmações para comandos críticos"""
    
    def __init__(self):
        self.confirmations: Dict[str, ConfirmationRequest] = {}
        self.confirmation_timeout = timedelta(minutes=30)  # 30 minutos
    
    async def create_confirmation(
        self,
        user_id: str,
        command_id: str,
        parameters: Dict[str, Any],
        message: str,
        risk_level: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ConfirmationRequest:
        """Cria uma nova solicitação de confirmação"""
        try:
            confirmation_id = str(uuid.uuid4())
            now = datetime.now()
            
            confirmation = ConfirmationRequest(
                id=confirmation_id,
                user_id=user_id,
                command_id=command_id,
                parameters=parameters,
                message=message,
                risk_level=risk_level,
                created_at=now,
                expires_at=now + self.confirmation_timeout,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.confirmations[confirmation_id] = confirmation
            
            logger.info(
                "Confirmação criada",
                confirmation_id=confirmation_id,
                user_id=user_id,
                command_id=command_id,
                risk_level=risk_level
            )
            
            return confirmation
            
        except Exception as e:
            logger.error("Erro ao criar confirmação", error=str(e))
            raise
    
    async def get_confirmation(self, confirmation_id: str) -> Optional[ConfirmationRequest]:
        """Retorna uma confirmação específica"""
        try:
            confirmation = self.confirmations.get(confirmation_id)
            
            if confirmation and confirmation.status == "pending":
                # Verificar se expirou
                if datetime.now() > confirmation.expires_at:
                    confirmation.status = "expired"
                    logger.info("Confirmação expirada", confirmation_id=confirmation_id)
            
            return confirmation
            
        except Exception as e:
            logger.error("Erro ao buscar confirmação", error=str(e))
            return None
    
    async def confirm_command(
        self,
        confirmation_id: str,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Optional[ConfirmationRequest]]:
        """
        Confirma um comando
        
        Returns:
            Tuple[bool, str, Optional[ConfirmationRequest]]:
            (success, message, confirmation)
        """
        try:
            confirmation = await self.get_confirmation(confirmation_id)
            
            if not confirmation:
                return False, "Confirmação não encontrada", None
            
            if confirmation.user_id != user_id:
                return False, "Confirmação não pertence ao usuário", None
            
            if confirmation.status != "pending":
                return False, f"Confirmação já foi {confirmation.status}", None
            
            if datetime.now() > confirmation.expires_at:
                confirmation.status = "expired"
                return False, "Confirmação expirou", None
            
            # Confirmar
            confirmation.status = "confirmed"
            confirmation.confirmed_at = datetime.now()
            
            logger.info(
                "Comando confirmado",
                confirmation_id=confirmation_id,
                user_id=user_id,
                command_id=confirmation.command_id
            )
            
            return True, "Comando confirmado com sucesso", confirmation
            
        except Exception as e:
            logger.error("Erro ao confirmar comando", error=str(e))
            return False, f"Erro interno: {str(e)}", None
    
    async def cancel_confirmation(
        self,
        confirmation_id: str,
        user_id: str,
        reason: str = "Cancelado pelo usuário",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Optional[ConfirmationRequest]]:
        """
        Cancela uma confirmação
        
        Returns:
            Tuple[bool, str, Optional[ConfirmationRequest]]:
            (success, message, confirmation)
        """
        try:
            confirmation = await self.get_confirmation(confirmation_id)
            
            if not confirmation:
                return False, "Confirmação não encontrada", None
            
            if confirmation.user_id != user_id:
                return False, "Confirmação não pertence ao usuário", None
            
            if confirmation.status != "pending":
                return False, f"Confirmação já foi {confirmation.status}", None
            
            # Cancelar
            confirmation.status = "cancelled"
            confirmation.cancelled_at = datetime.now()
            
            logger.info(
                "Comando cancelado",
                confirmation_id=confirmation_id,
                user_id=user_id,
                command_id=confirmation.command_id,
                reason=reason
            )
            
            return True, "Comando cancelado com sucesso", confirmation
            
        except Exception as e:
            logger.error("Erro ao cancelar confirmação", error=str(e))
            return False, f"Erro interno: {str(e)}", None
    
    async def get_user_pending_confirmations(self, user_id: str) -> List[Dict[str, Any]]:
        """Retorna confirmações pendentes do usuário"""
        try:
            pending = []
            
            for confirmation_id, confirmation in self.confirmations.items():
                if (confirmation.user_id == user_id and 
                    confirmation.status == "pending" and
                    datetime.now() <= confirmation.expires_at):
                    
                    pending.append({
                        "id": confirmation_id,
                        "command_id": confirmation.command_id,
                        "parameters": confirmation.parameters,
                        "message": confirmation.message,
                        "risk_level": confirmation.risk_level,
                        "created_at": confirmation.created_at.isoformat(),
                        "expires_at": confirmation.expires_at.isoformat(),
                        "time_remaining": (confirmation.expires_at - datetime.now()).total_seconds()
                    })
            
            # Ordenar por tempo restante (mais urgente primeiro)
            pending.sort(key=lambda x: x["time_remaining"])
            
            return pending
            
        except Exception as e:
            logger.error("Erro ao buscar confirmações pendentes", error=str(e))
            return []
    
    async def cleanup_expired_confirmations(self) -> int:
        """Remove confirmações expiradas e retorna o número removidas"""
        try:
            expired_ids = []
            now = datetime.now()
            
            for confirmation_id, confirmation in self.confirmations.items():
                if (confirmation.status == "pending" and 
                    now > confirmation.expires_at):
                    expired_ids.append(confirmation_id)
            
            for confirmation_id in expired_ids:
                confirmation = self.confirmations[confirmation_id]
                confirmation.status = "expired"
                
                logger.info("Confirmação expirada removida", confirmation_id=confirmation_id)
            
            if expired_ids:
                logger.info(f"Removidas {len(expired_ids)} confirmações expiradas")
            
            return len(expired_ids)
            
        except Exception as e:
            logger.error("Erro na limpeza de confirmações", error=str(e))
            return 0
    
    async def get_confirmation_stats(self, user_id: str) -> Dict[str, Any]:
        """Retorna estatísticas de confirmações do usuário"""
        try:
            user_confirmations = [
                conf for conf in self.confirmations.values()
                if conf.user_id == user_id
            ]
            
            total_confirmations = len(user_confirmations)
            pending_confirmations = len([c for c in user_confirmations if c.status == "pending"])
            confirmed_confirmations = len([c for c in user_confirmations if c.status == "confirmed"])
            cancelled_confirmations = len([c for c in user_confirmations if c.status == "cancelled"])
            expired_confirmations = len([c for c in user_confirmations if c.status == "expired"])
            
            # Estatísticas por nível de risco
            risk_stats = {}
            for confirmation in user_confirmations:
                risk = confirmation.risk_level
                if risk not in risk_stats:
                    risk_stats[risk] = {"total": 0, "confirmed": 0, "cancelled": 0}
                
                risk_stats[risk]["total"] += 1
                if confirmation.status == "confirmed":
                    risk_stats[risk]["confirmed"] += 1
                elif confirmation.status == "cancelled":
                    risk_stats[risk]["cancelled"] += 1
            
            return {
                "total_confirmations": total_confirmations,
                "pending_confirmations": pending_confirmations,
                "confirmed_confirmations": confirmed_confirmations,
                "cancelled_confirmations": cancelled_confirmations,
                "expired_confirmations": expired_confirmations,
                "confirmation_rate": (confirmed_confirmations / total_confirmations * 100) if total_confirmations > 0 else 0,
                "risk_stats": risk_stats
            }
            
        except Exception as e:
            logger.error("Erro ao calcular estatísticas de confirmação", error=str(e))
            return {}
    
    async def validate_confirmation_security(
        self,
        confirmation: ConfirmationRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Valida a segurança de uma confirmação
        
        Returns:
            Tuple[bool, str]: (is_secure, reason)
        """
        try:
            # Verificar se o IP mudou significativamente
            if (confirmation.ip_address and ip_address and 
                confirmation.ip_address != ip_address):
                
                # Permitir variações pequenas (ex: proxy, VPN)
                # Mas alertar sobre mudanças significativas
                logger.warning(
                    "Possível mudança de IP na confirmação",
                    confirmation_id=confirmation.id,
                    original_ip=confirmation.ip_address,
                    current_ip=ip_address
                )
            
            # Verificar se o User-Agent mudou
            if (confirmation.user_agent and user_agent and 
                confirmation.user_agent != user_agent):
                
                logger.warning(
                    "Mudança de User-Agent na confirmação",
                    confirmation_id=confirmation.id,
                    original_ua=confirmation.user_agent,
                    current_ua=user_agent
                )
            
            # Verificar se não há muitas confirmações pendentes
            pending_count = len(await self.get_user_pending_confirmations(confirmation.user_id))
            if pending_count > 10:
                return False, "Muitas confirmações pendentes. Limpe algumas antes de continuar."
            
            return True, "Confirmação segura"
            
        except Exception as e:
            logger.error("Erro na validação de segurança", error=str(e))
            return False, f"Erro na validação: {str(e)}"
    
    async def generate_confirmation_message(
        self,
        command_id: str,
        parameters: Dict[str, Any],
        risk_level: str
    ) -> str:
        """Gera uma mensagem de confirmação personalizada"""
        try:
            base_messages = {
                "add_watchlist": "Adicionar {symbol} à sua lista de observação?",
                "prepare_buy_order": "Preparar ordem de compra de {quantity} {symbol}{price_text}?",
                "prepare_sell_order": "Preparar ordem de venda de {quantity} {symbol}{price_text}?",
                "add_multibox": "Criar box de cotação{symbol_text}?",
                "create_analysis_tab": "Criar aba de análise para {symbol}?"
            }
            
            message_template = base_messages.get(command_id, "Confirmar {command_id}?")
            
            # Substituir parâmetros
            if command_id == "prepare_buy_order" or command_id == "prepare_sell_order":
                symbol = parameters.get("symbol", "")
                quantity = parameters.get("quantity", "")
                price = parameters.get("price")
                
                price_text = f" a R$ {price}" if price else " a mercado"
                
                return message_template.format(
                    symbol=symbol,
                    quantity=quantity,
                    price_text=price_text
                )
            
            elif command_id == "add_watchlist":
                symbol = parameters.get("symbol", "")
                return message_template.format(symbol=symbol)
            
            elif command_id == "add_multibox":
                symbol = parameters.get("symbol", "")
                symbol_text = f" para {symbol}" if symbol else ""
                return message_template.format(symbol_text=symbol_text)
            
            elif command_id == "create_analysis_tab":
                symbol = parameters.get("symbol", "")
                return message_template.format(symbol=symbol)
            
            else:
                return message_template.format(command_id=command_id)
                
        except Exception as e:
            logger.error("Erro ao gerar mensagem de confirmação", error=str(e))
            return f"Confirmar {command_id}?"


# Instância global do gerenciador de confirmações
confirmation_manager = ConfirmationManager()

