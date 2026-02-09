"""
Tipos base para o sistema de comandos seguros
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from datetime import datetime


class CommandCategory(str, Enum):
    """Categorias de risco dos comandos"""
    VIEW = "view"           # Baixo risco - apenas visualização
    CREATE = "create"        # Médio risco - criação de recursos
    MODIFY = "modify"        # Médio risco - modificação
    DELETE = "delete"        # Alto risco - remoção
    TRADE = "trade"          # Crítico - operações de trading


class CommandStatus(str, Enum):
    """Status de execução dos comandos"""
    PENDING = "pending"      # Aguardando confirmação
    CONFIRMED = "confirmed"  # Confirmado pelo usuário
    EXECUTING = "executing"  # Em execução
    SUCCESS = "success"      # Executado com sucesso
    FAILED = "failed"        # Falhou na execução
    CANCELLED = "cancelled"  # Cancelado pelo usuário
    REJECTED = "rejected"    # Rejeitado por validação


@dataclass
class ParameterDefinition:
    """Definição de um parâmetro de comando"""
    name: str
    type: str
    required: bool = True
    description: str = ""
    default: Any = None
    validation_rules: Optional[Dict[str, Any]] = None


@dataclass
class CommandResult:
    """Resultado da execução de um comando"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class CommandDefinition:
    """Definição completa de um comando"""
    id: str
    name: str
    description: str
    requires_confirmation: bool
    category: CommandCategory
    permissions: List[str]
    parameters: List[ParameterDefinition]
    action: Callable[[Dict[str, Any]], CommandResult]
    aliases: Optional[List[str]] = None
    examples: Optional[List[str]] = None
    risk_level: Optional[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.examples is None:
            self.examples = []
        if self.risk_level is None:
            self.risk_level = self._get_risk_level()
    
    def _get_risk_level(self) -> str:
        """Determina o nível de risco baseado na categoria"""
        risk_map = {
            CommandCategory.VIEW: "baixo",
            CommandCategory.CREATE: "médio", 
            CommandCategory.MODIFY: "médio",
            CommandCategory.DELETE: "alto",
            CommandCategory.TRADE: "crítico"
        }
        return risk_map.get(self.category, "desconhecido")


@dataclass
class CommandRequest:
    """Requisição para execução de um comando"""
    command_id: str
    parameters: Dict[str, Any]
    user_id: str
    session_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class CommandExecution:
    """Registro de execução de um comando"""
    id: str
    command_id: str
    user_id: str
    session_id: Optional[str]
    parameters: Dict[str, Any]
    status: CommandStatus
    result: Optional[CommandResult] = None
    created_at: datetime = None
    updated_at: datetime = None
    confirmed_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class CommandConfirmation:
    """Dados para confirmação de comando"""
    execution_id: str
    command: CommandDefinition
    parameters: Dict[str, Any]
    user_id: str
    message: str
    risk_level: str
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


# Tipos para análise de comandos
@dataclass
class CommandAnalysis:
    """Resultado da análise de uma mensagem para comandos"""
    is_command: bool
    confidence: float
    command_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    original_message: str = ""
    processed_message: str = ""
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


# Tipos para auditoria
@dataclass
class CommandAuditLog:
    """Log de auditoria para comandos"""
    id: str
    user_id: str
    session_id: Optional[str]
    command_id: str
    parameters: Dict[str, Any]
    status: CommandStatus
    result: Optional[CommandResult]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

