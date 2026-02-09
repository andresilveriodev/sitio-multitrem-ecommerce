"""
Executor de comandos - gerencia a execução segura dos comandos
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from .types import (
    CommandDefinition,
    CommandRequest,
    CommandResult,
    CommandStatus,
    CommandExecution,
    CommandConfirmation,
    CommandAuditLog
)
from .validator import CommandValidator
from .definitions import ALL_COMMANDS
import structlog

logger = structlog.get_logger(__name__)


class CommandExecutor:
    """Executor de comandos com gestão de segurança"""
    
    def __init__(self):
        self.validator = CommandValidator()
        self.pending_executions: Dict[str, CommandExecution] = {}
        self.execution_history: List[CommandExecution] = []
        self.audit_logs: List[CommandAuditLog] = []
    
    async def execute_command(
        self,
        request: CommandRequest,
        user_permissions: List[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Optional[CommandResult], Optional[CommandConfirmation]]:
        """
        Executa um comando com validação completa
        
        Returns:
            Tuple[bool, str, Optional[CommandResult], Optional[CommandConfirmation]]:
            (success, message, result, confirmation_needed)
        """
        try:
            # 1. Validar a requisição
            is_valid, error_message, command = await self.validator.validate_command_request(
                request, user_permissions, request.user_id
            )
            
            if not is_valid:
                await self._log_audit(
                    request, CommandStatus.REJECTED, None, 
                    error_message, ip_address, user_agent
                )
                return False, error_message, None, None
            
            # 2. Criar registro de execução
            execution = await self.validator.create_execution_record(request, command)
            self.pending_executions[execution.id] = execution
            
            # 3. Verificar se precisa confirmação
            if command.requires_confirmation:
                confirmation = await self._create_confirmation(execution, command)
                await self._log_audit(
                    request, CommandStatus.PENDING, None, 
                    "Aguardando confirmação do usuário", ip_address, user_agent
                )
                return True, "Comando aguardando confirmação", None, confirmation
            
            # 4. Executar diretamente
            result = await self._execute_command_action(command, request.parameters)
            
            # 5. Atualizar status
            execution.status = CommandStatus.SUCCESS if result.success else CommandStatus.FAILED
            execution.result = result
            execution.executed_at = datetime.now()
            
            # 6. Log de auditoria
            await self._log_audit(
                request, execution.status, result, 
                "Comando executado", ip_address, user_agent
            )
            
            # 7. Limpar execução pendente
            if execution.id in self.pending_executions:
                del self.pending_executions[execution.id]
            
            # 8. Adicionar ao histórico
            self.execution_history.append(execution)
            
            return True, "Comando executado com sucesso", result, None
            
        except Exception as e:
            logger.error("Erro na execução do comando", error=str(e), command_id=request.command_id)
            
            # Log de erro
            await self._log_audit(
                request, CommandStatus.FAILED, None, 
                f"Erro interno: {str(e)}", ip_address, user_agent
            )
            
            return False, f"Erro interno na execução: {str(e)}", None, None
    
    async def confirm_command(
        self,
        execution_id: str,
        user_id: str,
        confirmed: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Optional[CommandResult]]:
        """
        Confirma ou cancela um comando pendente
        
        Returns:
            Tuple[bool, str, Optional[CommandResult]]:
            (success, message, result)
        """
        try:
            # 1. Buscar execução pendente
            execution = self.pending_executions.get(execution_id)
            if not execution:
                return False, "Execução não encontrada ou já expirada", None
            
            # 2. Verificar se pertence ao usuário
            if execution.user_id != user_id:
                return False, "Execução não pertence ao usuário", None
            
            # 3. Verificar se ainda está pendente
            if execution.status != CommandStatus.PENDING:
                return False, "Execução não está mais pendente", None
            
            # 4. Verificar se não expirou (30 minutos)
            if datetime.now() - execution.created_at > timedelta(minutes=30):
                del self.pending_executions[execution_id]
                return False, "Execução expirou", None
            
            # 5. Validar confirmação
            is_valid, error_message = await self.validator.validate_confirmation(
                execution_id, user_id, confirmed
            )
            
            if not is_valid:
                return False, error_message, None
            
            # 6. Processar confirmação
            if not confirmed:
                # Cancelar comando
                execution.status = CommandStatus.CANCELLED
                execution.updated_at = datetime.now()
                
                await self._log_audit(
                    CommandRequest(
                        command_id=execution.command_id,
                        parameters=execution.parameters,
                        user_id=execution.user_id,
                        session_id=execution.session_id
                    ),
                    CommandStatus.CANCELLED, None,
                    "Comando cancelado pelo usuário", ip_address, user_agent
                )
                
                del self.pending_executions[execution_id]
                self.execution_history.append(execution)
                
                return True, "Comando cancelado com sucesso", None
            
            # 7. Executar comando confirmado
            command = ALL_COMMANDS.get(execution.command_id)
            if not command:
                return False, "Comando não encontrado", None
            
            execution.status = CommandStatus.CONFIRMED
            execution.confirmed_at = datetime.now()
            
            # Executar ação
            result = await self._execute_command_action(command, execution.parameters)
            
            # Atualizar status final
            execution.status = CommandStatus.SUCCESS if result.success else CommandStatus.FAILED
            execution.result = result
            execution.executed_at = datetime.now()
            
            # Log de auditoria
            await self._log_audit(
                CommandRequest(
                    command_id=execution.command_id,
                    parameters=execution.parameters,
                    user_id=execution.user_id,
                    session_id=execution.session_id
                ),
                execution.status, result,
                "Comando confirmado e executado", ip_address, user_agent
            )
            
            # Limpar execução pendente
            del self.pending_executions[execution_id]
            self.execution_history.append(execution)
            
            return True, "Comando executado com sucesso", result
            
        except Exception as e:
            logger.error("Erro na confirmação do comando", error=str(e), execution_id=execution_id)
            return False, f"Erro interno na confirmação: {str(e)}", None
    
    async def _execute_command_action(
        self, 
        command: CommandDefinition, 
        parameters: Dict[str, Any]
    ) -> CommandResult:
        """Executa a ação do comando"""
        start_time = time.time()
        
        try:
            # Executar ação do comando
            result = await command.action(parameters)
            
            # Adicionar tempo de execução
            result.execution_time = time.time() - start_time
            
            logger.info(
                "Comando executado",
                command_id=command.id,
                execution_time=result.execution_time,
                success=result.success
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                "Erro na execução da ação",
                command_id=command.id,
                error=str(e),
                execution_time=execution_time
            )
            
            return CommandResult(
                success=False,
                message=f"Erro na execução: {str(e)}",
                error=str(e),
                execution_time=execution_time
            )
    
    async def _create_confirmation(
        self, 
        execution: CommandExecution, 
        command: CommandDefinition
    ) -> CommandConfirmation:
        """Cria uma solicitação de confirmação"""
        try:
            # Gerar mensagem de confirmação
            message = self._generate_confirmation_message(command, execution.parameters)
            
            confirmation = CommandConfirmation(
                execution_id=execution.id,
                command=command,
                parameters=execution.parameters,
                user_id=execution.user_id,
                message=message,
                risk_level=command.risk_level
            )
            
            return confirmation
            
        except Exception as e:
            logger.error("Erro ao criar confirmação", error=str(e))
            raise
    
    def _generate_confirmation_message(
        self, 
        command: CommandDefinition, 
        parameters: Dict[str, Any]
    ) -> str:
        """Gera mensagem de confirmação personalizada"""
        try:
            base_message = f"Confirmar {command.name.lower()}?"
            
            # Adicionar detalhes específicos baseados no comando
            if command.id == "add_watchlist":
                symbol = parameters.get("symbol", "")
                return f"Adicionar {symbol} à sua lista de observação?"
            
            elif command.id == "prepare_buy_order":
                symbol = parameters.get("symbol", "")
                quantity = parameters.get("quantity", "")
                price = parameters.get("price", "")
                
                if price:
                    return f"Preparar ordem de compra de {quantity} {symbol} a R$ {price}?"
                else:
                    return f"Preparar ordem de compra de {quantity} {symbol} a mercado?"
            
            elif command.id == "prepare_sell_order":
                symbol = parameters.get("symbol", "")
                quantity = parameters.get("quantity", "")
                price = parameters.get("price", "")
                
                if price:
                    return f"Preparar ordem de venda de {quantity} {symbol} a R$ {price}?"
                else:
                    return f"Preparar ordem de venda de {quantity} {symbol} a mercado?"
            
            elif command.id == "add_multibox":
                symbol = parameters.get("symbol", "")
                if symbol:
                    return f"Criar box de cotação para {symbol}?"
                else:
                    return "Criar novo box de cotação?"
            
            elif command.id == "create_analysis_tab":
                symbol = parameters.get("symbol", "")
                return f"Criar aba de análise para {symbol}?"
            
            elif command.id == "create_order":
                items_count = len(parameters.get("items", []))
                return f"Criar pedido com {items_count} item(ns)?"
            
            elif command.id == "cancel_order":
                order_id = parameters.get("order_id", "")
                return f"Cancelar pedido {order_id}? Esta ação não pode ser desfeita."
            
            elif command.id == "update_order_stage":
                order_id = parameters.get("order_id", "")
                stage = parameters.get("stage", "")
                return f"Avançar pedido {order_id} para etapa '{stage}'?"
            
            # Caso padrão
            return base_message
            
        except Exception as e:
            logger.error("Erro ao gerar mensagem de confirmação", error=str(e))
            return f"Confirmar {command.name.lower()}?"
    
    async def _log_audit(
        self,
        request: CommandRequest,
        status: CommandStatus,
        result: Optional[CommandResult],
        message: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Registra log de auditoria"""
        try:
            audit_log = await self.validator.create_audit_log(
                CommandExecution(
                    id="temp",
                    command_id=request.command_id,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    parameters=request.parameters,
                    status=status
                ),
                status,
                result,
                ip_address,
                user_agent
            )
            
            self.audit_logs.append(audit_log)
            
        except Exception as e:
            logger.error("Erro ao criar log de auditoria", error=str(e))
    
    async def get_pending_executions(self, user_id: str) -> List[Dict[str, Any]]:
        """Retorna execuções pendentes do usuário"""
        try:
            pending = []
            
            for execution_id, execution in self.pending_executions.items():
                if execution.user_id == user_id:
                    # Verificar se não expirou
                    if datetime.now() - execution.created_at <= timedelta(minutes=30):
                        command = ALL_COMMANDS.get(execution.command_id)
                        
                        pending.append({
                            "execution_id": execution_id,
                            "command_id": execution.command_id,
                            "command_name": command.name if command else "Desconhecido",
                            "parameters": execution.parameters,
                            "created_at": execution.created_at.isoformat(),
                            "expires_at": (execution.created_at + timedelta(minutes=30)).isoformat(),
                            "confirmation_message": self._generate_confirmation_message(
                                command, execution.parameters
                            ) if command else "Confirmar comando?"
                        })
            
            return pending
            
        except Exception as e:
            logger.error("Erro ao buscar execuções pendentes", error=str(e))
            return []
    
    async def get_execution_history(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retorna histórico de execuções do usuário"""
        try:
            history = []
            
            # Filtrar por usuário e ordenar por data
            user_executions = [
                ex for ex in self.execution_history 
                if ex.user_id == user_id
            ]
            
            user_executions.sort(key=lambda x: x.created_at, reverse=True)
            
            for execution in user_executions[:limit]:
                command = ALL_COMMANDS.get(execution.command_id)
                
                history.append({
                    "execution_id": execution.id,
                    "command_id": execution.command_id,
                    "command_name": command.name if command else "Desconhecido",
                    "parameters": execution.parameters,
                    "status": execution.status.value,
                    "created_at": execution.created_at.isoformat(),
                    "executed_at": execution.executed_at.isoformat() if execution.executed_at else None,
                    "result": {
                        "success": execution.result.success if execution.result else None,
                        "message": execution.result.message if execution.result else None
                    } if execution.result else None
                })
            
            return history
            
        except Exception as e:
            logger.error("Erro ao buscar histórico", error=str(e))
            return []
    
    async def cleanup_expired_executions(self):
        """Remove execuções expiradas"""
        try:
            expired_ids = []
            cutoff_time = datetime.now() - timedelta(minutes=30)
            
            for execution_id, execution in self.pending_executions.items():
                if execution.created_at < cutoff_time:
                    expired_ids.append(execution_id)
            
            for execution_id in expired_ids:
                execution = self.pending_executions[execution_id]
                execution.status = CommandStatus.CANCELLED
                execution.updated_at = datetime.now()
                
                self.execution_history.append(execution)
                del self.pending_executions[execution_id]
                
                logger.info("Execução expirada removida", execution_id=execution_id)
            
            if expired_ids:
                logger.info(f"Removidas {len(expired_ids)} execuções expiradas")
                
        except Exception as e:
            logger.error("Erro na limpeza de execuções expiradas", error=str(e))
    
    async def get_execution_stats(self, user_id: str) -> Dict[str, Any]:
        """Retorna estatísticas de execução do usuário"""
        try:
            user_executions = [
                ex for ex in self.execution_history 
                if ex.user_id == user_id
            ]
            
            total_executions = len(user_executions)
            successful_executions = len([ex for ex in user_executions if ex.status == CommandStatus.SUCCESS])
            failed_executions = len([ex for ex in user_executions if ex.status == CommandStatus.FAILED])
            cancelled_executions = len([ex for ex in user_executions if ex.status == CommandStatus.CANCELLED])
            
            # Estatísticas por categoria
            category_stats = {}
            for execution in user_executions:
                command = ALL_COMMANDS.get(execution.command_id)
                if command:
                    category = command.category.value
                    if category not in category_stats:
                        category_stats[category] = 0
                    category_stats[category] += 1
            
            return {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "cancelled_executions": cancelled_executions,
                "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                "category_stats": category_stats,
                "pending_executions": len(await self.get_pending_executions(user_id))
            }
            
        except Exception as e:
            logger.error("Erro ao calcular estatísticas", error=str(e))
            return {}

