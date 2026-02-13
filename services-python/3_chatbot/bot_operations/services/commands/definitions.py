"""
Definições dos comandos permitidos no sistema
"""

from typing import Dict, List, Any
from .types import (
    CommandDefinition, 
    CommandCategory, 
    ParameterDefinition,
    CommandResult
)
import structlog

logger = structlog.get_logger(__name__)


# ============================================================================
# FUNÇÕES DE AÇÃO DOS COMANDOS
# ============================================================================

async def show_position_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para mostrar posição de um ativo"""
    try:
        symbol = params.get('symbol', '').upper()
        if not symbol:
            return CommandResult(
                success=False,
                message="Símbolo do ativo é obrigatório",
                error="symbol_required"
            )
        
        # Aqui seria feita a integração com o frontend
        # Por enquanto, retornamos uma simulação
        return CommandResult(
            success=True,
            message=f"Posição do ativo {symbol} exibida com sucesso",
            data={
                "symbol": symbol,
                "action": "show_position",
                "target": "frontend"
            }
        )
    except Exception as e:
        logger.error("Erro ao executar show_position", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao exibir posição",
            error=str(e)
        )


async def show_book_offers_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para mostrar book de ofertas"""
    try:
        symbol = params.get('symbol', '').upper()
        if not symbol:
            return CommandResult(
                success=False,
                message="Símbolo do ativo é obrigatório",
                error="symbol_required"
            )
        
        return CommandResult(
            success=True,
            message=f"Book de ofertas do ativo {symbol} exibido com sucesso",
            data={
                "symbol": symbol,
                "action": "show_book_offers",
                "target": "frontend"
            }
        )
    except Exception as e:
        logger.error("Erro ao executar show_book_offers", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao exibir book de ofertas",
            error=str(e)
        )


async def show_watchlist_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para mostrar watchlist"""
    try:
        return CommandResult(
            success=True,
            message="Lista de observação exibida com sucesso",
            data={
                "action": "show_watchlist",
                "target": "frontend"
            }
        )
    except Exception as e:
        logger.error("Erro ao executar show_watchlist", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao exibir lista de observação",
            error=str(e)
        )


async def add_multibox_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para adicionar box de cotação"""
    try:
        symbol = params.get('symbol', '').upper()
        
        return CommandResult(
            success=True,
            message=f"Box de cotação {'para ' + symbol if symbol else ''} criado com sucesso",
            data={
                "symbol": symbol,
                "action": "add_multibox",
                "target": "frontend"
            }
        )
    except Exception as e:
        logger.error("Erro ao executar add_multibox", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao criar box de cotação",
            error=str(e)
        )


async def add_watchlist_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para adicionar ativo ao watchlist"""
    try:
        symbol = params.get('symbol', '').upper()
        if not symbol:
            return CommandResult(
                success=False,
                message="Símbolo do ativo é obrigatório",
                error="symbol_required"
            )
        
        return CommandResult(
            success=True,
            message=f"Ativo {symbol} adicionado à lista de observação com sucesso",
            data={
                "symbol": symbol,
                "action": "add_watchlist",
                "target": "frontend"
            }
        )
    except Exception as e:
        logger.error("Erro ao executar add_watchlist", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao adicionar à lista de observação",
            error=str(e)
        )


async def create_analysis_tab_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para criar aba de análise"""
    try:
        symbol = params.get('symbol', '').upper()
        if not symbol:
            return CommandResult(
                success=False,
                message="Símbolo do ativo é obrigatório",
                error="symbol_required"
            )
        
        return CommandResult(
            success=True,
            message=f"Aba de análise para {symbol} criada com sucesso",
            data={
                "symbol": symbol,
                "action": "create_analysis_tab",
                "target": "frontend"
            }
        )
    except Exception as e:
        logger.error("Erro ao executar create_analysis_tab", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao criar aba de análise",
            error=str(e)
        )


async def prepare_buy_order_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para preparar ordem de compra (NÃO executa)"""
    try:
        symbol = params.get('symbol', '').upper()
        quantity = params.get('quantity')
        price = params.get('price')
        
        if not symbol:
            return CommandResult(
                success=False,
                message="Símbolo do ativo é obrigatório",
                error="symbol_required"
            )
        
        if not quantity:
            return CommandResult(
                success=False,
                message="Quantidade é obrigatória",
                error="quantity_required"
            )
        
        return CommandResult(
            success=True,
            message=f"Ordem de compra para {symbol} preparada com sucesso",
            data={
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "action": "prepare_buy_order",
                "target": "frontend",
                "note": "Ordem preparada - aguardando confirmação do usuário"
            }
        )
    except Exception as e:
        logger.error("Erro ao executar prepare_buy_order", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao preparar ordem de compra",
            error=str(e)
        )


async def prepare_sell_order_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para preparar ordem de venda (NÃO executa)"""
    try:
        symbol = params.get('symbol', '').upper()
        quantity = params.get('quantity')
        price = params.get('price')
        
        if not symbol:
            return CommandResult(
                success=False,
                message="Símbolo do ativo é obrigatório",
                error="symbol_required"
            )
        
        if not quantity:
            return CommandResult(
                success=False,
                message="Quantidade é obrigatória",
                error="quantity_required"
            )
        
        return CommandResult(
            success=True,
            message=f"Ordem de venda para {symbol} preparada com sucesso",
            data={
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "action": "prepare_sell_order",
                "target": "frontend",
                "note": "Ordem preparada - aguardando confirmação do usuário"
            }
        )
    except Exception as e:
        logger.error("Erro ao executar prepare_sell_order", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao preparar ordem de venda",
            error=str(e)
        )


# ============================================================================
# DEFINIÇÕES DOS COMANDOS
# ============================================================================

# Comandos de Visualização (Sem Confirmação)
VIEW_COMMANDS: Dict[str, CommandDefinition] = {
    "show_position": CommandDefinition(
        id="show_position",
        name="Mostrar Posição",
        description="Exibe a posição atual de um ativo",
        requires_confirmation=False,
        category=CommandCategory.VIEW,
        permissions=["view_positions"],
        parameters=[
            ParameterDefinition(
                name="symbol",
                type="string",
                required=True,
                description="Símbolo do ativo (ex: PETR4, VALE3)"
            )
        ],
        action=show_position_action,
        aliases=["posição", "position", "pos"],
        examples=[
            "Mostre a posição da PETR4",
            "Posição PETR4",
            "show position PETR4"
        ]
    ),
    
    "show_book_offers": CommandDefinition(
        id="show_book_offers",
        name="Book de Ofertas",
        description="Exibe o book de ofertas de um ativo",
        requires_confirmation=False,
        category=CommandCategory.VIEW,
        permissions=["view_book"],
        parameters=[
            ParameterDefinition(
                name="symbol",
                type="string",
                required=True,
                description="Símbolo do ativo"
            )
        ],
        action=show_book_offers_action,
        aliases=["book", "ofertas", "offers"],
        examples=[
            "Mostre o book da PETR4",
            "Book PETR4",
            "show book PETR4"
        ]
    ),
    
    "show_watchlist": CommandDefinition(
        id="show_watchlist",
        name="Lista de Observação",
        description="Exibe a lista de ativos observados",
        requires_confirmation=False,
        category=CommandCategory.VIEW,
        permissions=["view_watchlist"],
        parameters=[],
        action=show_watchlist_action,
        aliases=["watchlist", "observação", "watch"],
        examples=[
            "Mostre minha lista de observação",
            "Watchlist",
            "show watchlist"
        ]
    )
}

# Comandos de Criação (Com Confirmação)
CREATE_COMMANDS: Dict[str, CommandDefinition] = {
    "add_multibox": CommandDefinition(
        id="add_multibox",
        name="Adicionar Box de Cotação",
        description="Cria um novo box de cotação",
        requires_confirmation=True,
        category=CommandCategory.CREATE,
        permissions=["create_multibox"],
        parameters=[
            ParameterDefinition(
                name="symbol",
                type="string",
                required=False,
                description="Símbolo do ativo para o box (opcional)"
            )
        ],
        action=add_multibox_action,
        aliases=["multibox", "box", "cotação", "abrir", "abri", "criar box", "abrir box"],
        examples=[
            "Adicione um box de cotação",
            "Criar box PETR4",
            "Quero abrir um box de PETR4",
            "abri um box",
            "add multibox"
        ]
    ),
    
    "add_watchlist": CommandDefinition(
        id="add_watchlist",
        name="Adicionar ao Watchlist",
        description="Adiciona um ativo à lista de observação",
        requires_confirmation=True,
        category=CommandCategory.CREATE,
        permissions=["modify_watchlist"],
        parameters=[
            ParameterDefinition(
                name="symbol",
                type="string",
                required=True,
                description="Símbolo do ativo"
            )
        ],
        action=add_watchlist_action,
        aliases=["adicionar", "add", "watch"],
        examples=[
            "Adicione PETR4 ao watchlist",
            "Add PETR4",
            "add to watchlist PETR4"
        ]
    ),
    
    "create_analysis_tab": CommandDefinition(
        id="create_analysis_tab",
        name="Criar Aba de Análise",
        description="Cria uma nova aba para análise técnica",
        requires_confirmation=True,
        category=CommandCategory.CREATE,
        permissions=["create_analysis"],
        parameters=[
            ParameterDefinition(
                name="symbol",
                type="string",
                required=True,
                description="Símbolo do ativo para análise"
            )
        ],
        action=create_analysis_tab_action,
        aliases=["análise", "analysis", "tab"],
        examples=[
            "Crie uma aba de análise para PETR4",
            "Análise PETR4",
            "create analysis tab PETR4"
        ]
    )
}

# Comandos de Trading (Sempre Confirmação)
TRADE_COMMANDS: Dict[str, CommandDefinition] = {
    "prepare_buy_order": CommandDefinition(
        id="prepare_buy_order",
        name="Preparar Ordem de Compra",
        description="Prepara uma ordem de compra (NÃO executa)",
        requires_confirmation=True,
        category=CommandCategory.TRADE,
        permissions=["prepare_orders"],
        parameters=[
            ParameterDefinition(
                name="symbol",
                type="string",
                required=True,
                description="Símbolo do ativo"
            ),
            ParameterDefinition(
                name="quantity",
                type="integer",
                required=True,
                description="Quantidade de ações"
            ),
            ParameterDefinition(
                name="price",
                type="float",
                required=False,
                description="Preço limite (opcional - mercado se não informado)"
            )
        ],
        action=prepare_buy_order_action,
        aliases=["comprar", "buy", "compra"],
        examples=[
            "Prepare uma ordem de compra de 100 PETR4",
            "Comprar 100 PETR4 a 38.50",
            "prepare buy order PETR4 100 38.50"
        ]
    ),
    
    "prepare_sell_order": CommandDefinition(
        id="prepare_sell_order",
        name="Preparar Ordem de Venda",
        description="Prepara uma ordem de venda (NÃO executa)",
        requires_confirmation=True,
        category=CommandCategory.TRADE,
        permissions=["prepare_orders"],
        parameters=[
            ParameterDefinition(
                name="symbol",
                type="string",
                required=True,
                description="Símbolo do ativo"
            ),
            ParameterDefinition(
                name="quantity",
                type="integer",
                required=True,
                description="Quantidade de ações"
            ),
            ParameterDefinition(
                name="price",
                type="float",
                required=False,
                description="Preço limite (opcional - mercado se não informado)"
            )
        ],
        action=prepare_sell_order_action,
        aliases=["vender", "sell", "venda"],
        examples=[
            "Prepare uma ordem de venda de 100 PETR4",
            "Vender 100 PETR4 a 38.50",
            "prepare sell order PETR4 100 38.50"
        ]
    )
}

# Dicionário com todos os comandos
ALL_COMMANDS: Dict[str, CommandDefinition] = {
    **VIEW_COMMANDS,
    **CREATE_COMMANDS,
    **TRADE_COMMANDS
}

# Comandos PROIBIDOS (para referência)
PROHIBITED_COMMANDS = [
    "execute_order",           # Execução direta de ordens
    "modify_settings",         # Modificação de configurações críticas
    "access_user_data",        # Acesso a dados sensíveis
    "modify_permissions",      # Modificação de permissões
    "external_api_call",       # Chamadas para APIs externas
    "code_execution",          # Execução de código dinâmico
    "system_command",          # Comandos do sistema
    "file_operation",          # Operações de arquivo
    "network_access",          # Acesso à rede
    "database_query"           # Queries diretas ao banco
]

# Validações de segurança
SECURITY_VALIDATIONS = {
    "block_code_execution": [
        "eval(",
        "Function(",
        "setTimeout(",
        "setInterval(",
        "fetch(",
        "XMLHttpRequest",
        "exec(",
        "system(",
        "subprocess",
        "os.system"
    ],
    
    "blocked_keywords": [
        "hack",
        "system",
        "internal",
        "admin",
        "root",
        "sudo",
        "privilege",
        "bypass",
        "inject",
        "exploit"
    ],
    
    "blocked_patterns": [
        r"{{system}}",
        r"<tool>",
        r"<function>",
        r"<command>",
        r"javascript:",
        r"data:text/html",
        r"vbscript:"
    ]
}

