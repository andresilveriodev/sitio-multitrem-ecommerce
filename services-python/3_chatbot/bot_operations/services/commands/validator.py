"""
Validador de segurança para comandos
"""

import re
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from .types import (
    CommandDefinition, 
    CommandRequest, 
    CommandResult,
    CommandStatus,
    CommandExecution,
    CommandAuditLog
)
from .definitions import ALL_COMMANDS, SECURITY_VALIDATIONS, PROHIBITED_COMMANDS
import structlog

logger = structlog.get_logger(__name__)


class CommandValidator:
    """Validador de segurança para comandos"""
    
    def __init__(self):
        self.blocked_patterns = [re.compile(pattern) for pattern in SECURITY_VALIDATIONS["blocked_patterns"]]
        self.blocked_keywords = SECURITY_VALIDATIONS["blocked_keywords"]
        self.blocked_code_patterns = SECURITY_VALIDATIONS["block_code_execution"]
    
    async def validate_command_request(
        self, 
        request: CommandRequest,
        user_permissions: List[str],
        user_id: str
    ) -> Tuple[bool, str, Optional[CommandDefinition]]:
        """
        Valida uma requisição de comando completa
        
        Returns:
            Tuple[bool, str, Optional[CommandDefinition]]: 
            (is_valid, error_message, command_definition)
        """
        try:
            # 1. Validar se o comando existe
            command = ALL_COMMANDS.get(request.command_id)
            if not command:
                return False, f"Comando '{request.command_id}' não encontrado", None
            
            # 2. Validar permissões do usuário
            has_permission = await self._validate_permissions(command, user_permissions)
            if not has_permission:
                return False, f"Usuário não tem permissão para executar '{command.name}'", None
            
            # 3. Validar parâmetros
            param_validation = await self._validate_parameters(command, request.parameters)
            if not param_validation[0]:
                return False, param_validation[1], None
            
            # 4. Validar segurança dos parâmetros
            security_validation = await self._validate_security(command, request.parameters)
            if not security_validation[0]:
                return False, security_validation[1], None
            
            # 5. Validar limites e rate limiting
            rate_validation = await self._validate_rate_limits(request, user_id)
            if not rate_validation[0]:
                return False, rate_validation[1], None
            
            return True, "Comando validado com sucesso", command
            
        except Exception as e:
            logger.error("Erro na validação do comando", error=str(e), command_id=request.command_id)
            return False, f"Erro interno na validação: {str(e)}", None
    
    async def _validate_permissions(
        self, 
        command: CommandDefinition, 
        user_permissions: List[str]
    ) -> bool:
        """Valida se o usuário tem as permissões necessárias"""
        try:
            # Se o comando não requer permissões específicas (lista vazia), permite
            if not command.permissions or len(command.permissions) == 0:
                return True
            
            # Verificar se o usuário tem pelo menos uma das permissões necessárias
            for required_permission in command.permissions:
                if required_permission in user_permissions:
                    return True
            
            logger.warning(
                "Permissão negada", 
                command_id=command.id,
                required_permissions=command.permissions,
                user_permissions=user_permissions
            )
            return False
            
        except Exception as e:
            logger.error("Erro na validação de permissões", error=str(e))
            return False
    
    async def _validate_parameters(
        self, 
        command: CommandDefinition, 
        parameters: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Valida os parâmetros do comando"""
        try:
            # Verificar parâmetros obrigatórios
            for param in command.parameters:
                if param.required and param.name not in parameters:
                    return False, f"Parâmetro obrigatório '{param.name}' não fornecido"
                
                # Validar tipo do parâmetro
                if param.name in parameters:
                    type_validation = await self._validate_parameter_type(
                        param, parameters[param.name]
                    )
                    if not type_validation[0]:
                        return type_validation
            
            # Verificar parâmetros extras não permitidos
            allowed_params = {param.name for param in command.parameters}
            extra_params = set(parameters.keys()) - allowed_params
            if extra_params:
                return False, f"Parâmetros não reconhecidos: {', '.join(extra_params)}"
            
            return True, "Parâmetros válidos"
            
        except Exception as e:
            logger.error("Erro na validação de parâmetros", error=str(e))
            return False, f"Erro na validação de parâmetros: {str(e)}"
    
    async def _validate_parameter_type(
        self, 
        param: 'ParameterDefinition', 
        value: Any
    ) -> Tuple[bool, str]:
        """Valida o tipo de um parâmetro específico"""
        try:
            if param.type == "string":
                if not isinstance(value, str):
                    return False, f"Parâmetro '{param.name}' deve ser uma string"
                
                # Validações específicas para strings
                if param.name == "symbol":
                    if not re.match(r'^[A-Z]{4}\d$', value.upper()):
                        return False, f"Símbolo '{value}' deve estar no formato AAAA4 (ex: PETR4)"
                
            elif param.type == "integer":
                try:
                    int_value = int(value)
                    if int_value <= 0:
                        return False, f"Parâmetro '{param.name}' deve ser um número positivo"
                except (ValueError, TypeError):
                    return False, f"Parâmetro '{param.name}' deve ser um número inteiro"
                
            elif param.type == "float":
                try:
                    float_value = float(value)
                    if float_value <= 0:
                        return False, f"Parâmetro '{param.name}' deve ser um número positivo"
                except (ValueError, TypeError):
                    return False, f"Parâmetro '{param.name}' deve ser um número decimal"
            
            return True, "Tipo válido"
            
        except Exception as e:
            logger.error("Erro na validação de tipo", error=str(e), param_name=param.name)
            return False, f"Erro na validação do tipo: {str(e)}"
    
    async def _validate_security(
        self, 
        command: CommandDefinition, 
        parameters: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Valida a segurança dos parâmetros"""
        try:
            # Verificar se não há tentativas de execução de código
            for param_name, param_value in parameters.items():
                if isinstance(param_value, str):
                    # Verificar padrões bloqueados
                    for pattern in self.blocked_patterns:
                        if pattern.search(param_value):
                            return False, f"Parâmetro '{param_name}' contém padrão proibido"
                    
                    # Verificar palavras-chave bloqueadas
                    param_lower = param_value.lower()
                    for keyword in self.blocked_keywords:
                        if keyword in param_lower:
                            return False, f"Parâmetro '{param_name}' contém palavra proibida: {keyword}"
                    
                    # Verificar tentativas de execução de código
                    for code_pattern in self.blocked_code_patterns:
                        if code_pattern in param_value:
                            return False, f"Parâmetro '{param_name}' contém tentativa de execução de código"
            
            # Verificar se o comando não está na lista de proibidos
            if command.id in PROHIBITED_COMMANDS:
                return False, f"Comando '{command.id}' está na lista de comandos proibidos"
            
            return True, "Validação de segurança aprovada"
            
        except Exception as e:
            logger.error("Erro na validação de segurança", error=str(e))
            return False, f"Erro na validação de segurança: {str(e)}"
    
    async def _validate_rate_limits(
        self, 
        request: CommandRequest, 
        user_id: str
    ) -> Tuple[bool, str]:
        """Valida limites de taxa e rate limiting"""
        try:
            # TODO: Implementar rate limiting baseado em Redis
            # Por enquanto, retorna sempre válido
            
            # Exemplo de implementação:
            # - Máximo 10 comandos por minuto por usuário
            # - Máximo 100 comandos por hora por usuário
            # - Máximo 1000 comandos por dia por usuário
            
            return True, "Rate limiting aprovado"
            
        except Exception as e:
            logger.error("Erro na validação de rate limiting", error=str(e))
            return False, f"Erro no rate limiting: {str(e)}"
    
    async def create_execution_record(
        self,
        request: CommandRequest,
        command: CommandDefinition,
        status: CommandStatus = CommandStatus.PENDING
    ) -> CommandExecution:
        """Cria um registro de execução do comando"""
        try:
            execution_id = str(uuid.uuid4())
            
            execution = CommandExecution(
                id=execution_id,
                command_id=request.command_id,
                user_id=request.user_id,
                session_id=request.session_id,
                parameters=request.parameters,
                status=status
            )
            
            logger.info(
                "Registro de execução criado",
                execution_id=execution_id,
                command_id=command.id,
                user_id=request.user_id,
                status=status.value
            )
            
            return execution
            
        except Exception as e:
            logger.error("Erro ao criar registro de execução", error=str(e))
            raise
    
    async def create_audit_log(
        self,
        execution: CommandExecution,
        status: CommandStatus,
        result: Optional[CommandResult] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> CommandAuditLog:
        """Cria um log de auditoria"""
        try:
            audit_id = str(uuid.uuid4())
            
            audit_log = CommandAuditLog(
                id=audit_id,
                user_id=execution.user_id,
                session_id=execution.session_id,
                command_id=execution.command_id,
                parameters=execution.parameters,
                status=status,
                result=result,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            logger.info(
                "Log de auditoria criado",
                audit_id=audit_id,
                execution_id=execution.id,
                command_id=execution.command_id,
                user_id=execution.user_id,
                status=status.value
            )
            
            return audit_log
            
        except Exception as e:
            logger.error("Erro ao criar log de auditoria", error=str(e))
            raise
    
    async def validate_confirmation(
        self,
        execution_id: str,
        user_id: str,
        confirmation: bool
    ) -> Tuple[bool, str]:
        """Valida uma confirmação de comando"""
        try:
            # TODO: Implementar validação de confirmação
            # - Verificar se o execution_id existe
            # - Verificar se pertence ao usuário
            # - Verificar se ainda está pendente
            # - Verificar se não expirou
            
            if not confirmation:
                return True, "Comando cancelado pelo usuário"
            
            return True, "Confirmação válida"
            
        except Exception as e:
            logger.error("Erro na validação de confirmação", error=str(e))
            return False, f"Erro na validação de confirmação: {str(e)}"
    
    async def get_command_suggestions(
        self, 
        partial_command: str,
        user_permissions: List[str]
    ) -> List[Dict[str, Any]]:
        """Retorna sugestões de comandos baseadas no input parcial"""
        try:
            suggestions = []
            partial_lower = partial_command.lower()
            
            for command_id, command in ALL_COMMANDS.items():
                # Verificar se o usuário tem permissão
                has_permission = await self._validate_permissions(command, user_permissions)
                if not has_permission:
                    continue
                
                # Verificar se o comando ou alias corresponde ao input parcial
                if (partial_lower in command_id.lower() or
                    any(partial_lower in alias.lower() for alias in command.aliases) or
                    partial_lower in command.name.lower()):
                    
                    suggestions.append({
                        "id": command.id,
                        "name": command.name,
                        "description": command.description,
                        "category": command.category.value,
                        "risk_level": command.risk_level,
                        "examples": command.examples[:2]  # Apenas 2 exemplos
                    })
            
            # Ordenar por relevância (exato match primeiro)
            suggestions.sort(key=lambda x: (
                not (partial_lower == x["id"].lower() or 
                     partial_lower in [alias.lower() for alias in ALL_COMMANDS[x["id"]].aliases]),
                x["name"]
            ))
            
            return suggestions[:5]  # Máximo 5 sugestões
            
        except Exception as e:
            logger.error("Erro ao gerar sugestões", error=str(e))
            return []
    
    async def get_command_help(
        self, 
        command_id: str,
        user_permissions: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Retorna ajuda detalhada para um comando específico"""
        try:
            command = ALL_COMMANDS.get(command_id)
            if not command:
                return None
            
            # Verificar permissões
            has_permission = await self._validate_permissions(command, user_permissions)
            if not has_permission:
                return None
            
            return {
                "id": command.id,
                "name": command.name,
                "description": command.description,
                "category": command.category.value,
                "risk_level": command.risk_level,
                "requires_confirmation": command.requires_confirmation,
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type,
                        "required": param.required,
                        "description": param.description,
                        "default": param.default
                    }
                    for param in command.parameters
                ],
                "aliases": command.aliases,
                "examples": command.examples,
                "permissions": command.permissions
            }
            
        except Exception as e:
            logger.error("Erro ao obter ajuda do comando", error=str(e))
            return None

