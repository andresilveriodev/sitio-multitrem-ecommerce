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


async def show_menu_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para mostrar menu principal com botões"""
    try:
        # Botões em 2 colunas
        inline_keyboard = [
            [
                {"text": "📦 Pedidos", "callback_data": "menu_pedidos"},
                {"text": "🚚 Entregas", "callback_data": "menu_entregas"}
            ],
            [
                {"text": "🥬 Estoque", "callback_data": "menu_estoque"},
                {"text": "💰 Financeiro", "callback_data": "menu_financeiro"}
            ],
            [
                {"text": "👤 Clientes", "callback_data": "menu_clientes"},
                {"text": "⚙️ Admin", "callback_data": "menu_admin"}
            ]
        ]
        
        return CommandResult(
            success=True,
            message="Menu Principal - Selecione uma opção:",
            data={
                "action": "show_menu",
                "target": "telegram",
                "has_keyboard": True,  # Flag explícita para Telegram Service
                "keyboard_type": "inline",  # Tipo de teclado (inline ou reply)
                "edit_message": False,  # Menu principal cria nova mensagem
                "telegram_keyboard": {
                    "inline_keyboard": inline_keyboard
                },
                # Formato direto para Telegram API
                "reply_markup": {
                    "inline_keyboard": inline_keyboard
                }
            }
        )
    except Exception as e:
        logger.error("Erro ao executar show_menu", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao exibir menu",
            error=str(e)
        )


async def show_pedidos_menu_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para mostrar menu de pedidos com botões"""
    try:
        # Botões do menu de pedidos
        inline_keyboard = [
            [
                {"text": "🆕 Novo Pedido", "callback_data": "pedido_novo"},
                {"text": "📋 Listar Pedidos", "callback_data": "pedido_listar"}
            ],
            [
                {"text": "🔎 Buscar Pedido", "callback_data": "pedido_buscar"},
                {"text": "✏️ Editar Pedido", "callback_data": "pedido_editar"}
            ],
            [
                {"text": "📊 Resumo por Data", "callback_data": "pedido_resumo"}
            ],
            [
                {"text": "🔙 Voltar", "callback_data": "menu_voltar"}
            ]
        ]
        
        return CommandResult(
            success=True,
            message="📦 Menu de Pedidos - Selecione uma opção:",
            data={
                "action": "show_pedidos_menu",
                "target": "telegram",
                "has_keyboard": True,
                "keyboard_type": "inline",
                "edit_message": False,  # Cria nova mensagem
                "telegram_keyboard": {
                    "inline_keyboard": inline_keyboard
                },
                "reply_markup": {
                    "inline_keyboard": inline_keyboard
                }
            }
        )
    except Exception as e:
        logger.error("Erro ao executar show_pedidos_menu", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao exibir menu de pedidos",
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
# AÇÕES DOS COMANDOS DE PEDIDOS
# ============================================================================

async def list_orders_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para listar pedidos"""
    try:
        from services.order_service import order_service
        from models.order_models import OrderStatus
        
        status_filter = params.get('status')
        customer_id = params.get('customer_id')
        limit = params.get('limit', 10)
        
        # Converter status string para enum se fornecido
        order_status = None
        if status_filter:
            try:
                order_status = OrderStatus(status_filter.lower())
            except ValueError:
                return CommandResult(
                    success=False,
                    message=f"Status inválido: {status_filter}. Use: pending, confirmed, processing, shipped, delivered, cancelled, rejected",
                    error="invalid_status"
                )
        
        orders = await order_service.list_orders(
            status=order_status,
            customer_id=customer_id,
            limit=limit
        )
        
        if not orders:
            return CommandResult(
                success=True,
                message="Nenhum pedido encontrado",
                data={
                    "orders": [],
                    "count": 0
                }
            )
        
        # Formatar pedidos para resposta
        orders_data = []
        for order in orders:
            orders_data.append({
                "id": order.id,
                "order_number": order.order_number,
                "customer_name": order.customer_name or order.customer_id,
                "status": order.status,
                "total": order.total,
                "created_at": order.created_at.isoformat() if order.created_at else None
            })
        
        message = f"Encontrados {len(orders)} pedido(s)"
        if order_status:
            message += f" com status '{order_status.value}'"
        
        return CommandResult(
            success=True,
            message=message,
            data={
                "orders": orders_data,
                "count": len(orders)
            }
        )
    except Exception as e:
        logger.error("Erro ao executar list_orders", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao listar pedidos",
            error=str(e)
        )


async def show_order_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para mostrar detalhes de um pedido"""
    try:
        from services.order_service import order_service
        
        order_id = params.get('order_id')
        order_number = params.get('order_number')
        
        if not order_id and not order_number:
            return CommandResult(
                success=False,
                message="ID ou número do pedido é obrigatório",
                error="order_identifier_required"
            )
        
        if order_id:
            order = await order_service.get_order(order_id)
        else:
            order = await order_service.get_order_by_number(order_number)
        
        if not order:
            return CommandResult(
                success=False,
                message="Pedido não encontrado",
                error="order_not_found"
            )
        
        # Formatar resposta detalhada
        items_text = "\n".join([
            f"  • {item['product_name']} (Qtd: {item['quantity']}) - R$ {item['total_price']:.2f}"
            for item in order.items
        ])
        
        message = f"""
📦 Pedido: {order.order_number}
👤 Cliente: {order.customer_name or order.customer_id}
📞 Telefone: {order.customer_phone or 'N/A'}
📧 Email: {order.customer_email or 'N/A'}

📍 Endereço:
{order.shipping_address or 'N/A'}
{order.shipping_city or ''}, {order.shipping_state or ''} - {order.shipping_zip or ''}

📋 Itens:
{items_text}

💰 Valores:
  Subtotal: R$ {order.subtotal:.2f}
  Frete: R$ {order.shipping_cost:.2f}
  Total: R$ {order.total:.2f}

📊 Status: {order.status.upper()}
💳 Pagamento: {order.payment_status or 'N/A'} ({order.payment_method or 'N/A'})

📝 Observações: {order.notes or 'Nenhuma'}
        """.strip()
        
        return CommandResult(
            success=True,
            message=message,
            data={
                "order": {
                    "id": order.id,
                    "order_number": order.order_number,
                    "customer_id": order.customer_id,
                    "customer_name": order.customer_name,
                    "status": order.status,
                    "total": order.total,
                    "items": order.items,
                    "created_at": order.created_at.isoformat() if order.created_at else None
                }
            }
        )
    except Exception as e:
        logger.error("Erro ao executar show_order", error=str(e))
        return CommandResult(
            success=False,
            message="Erro ao buscar pedido",
            error=str(e)
        )


async def approve_order_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para aprovar um pedido"""
    try:
        from services.order_service import order_service
        
        order_id = params.get('order_id')
        order_number = params.get('order_number')
        user_id = params.get('user_id', 'system')
        admin_notes = params.get('admin_notes')
        
        if not order_id and not order_number:
            return CommandResult(
                success=False,
                message="ID ou número do pedido é obrigatório",
                error="order_identifier_required"
            )
        
        # Buscar pedido primeiro
        if order_id:
            order = await order_service.get_order(order_id)
        else:
            order = await order_service.get_order_by_number(order_number)
        
        if not order:
            return CommandResult(
                success=False,
                message="Pedido não encontrado",
                error="order_not_found"
            )
        
        # Aprovar pedido
        updated_order = await order_service.approve_order(
            order_id=order.id,
            user_id=user_id,
            admin_notes=admin_notes
        )
        
        if not updated_order:
            return CommandResult(
                success=False,
                message="Erro ao aprovar pedido",
                error="approval_failed"
            )
        
        return CommandResult(
            success=True,
            message=f"Pedido {updated_order.order_number} aprovado com sucesso!",
            data={
                "order": {
                    "id": updated_order.id,
                    "order_number": updated_order.order_number,
                    "status": updated_order.status
                }
            }
        )
    except Exception as e:
        logger.error("Erro ao executar approve_order", error=str(e))
        return CommandResult(
            success=False,
            message=f"Erro ao aprovar pedido: {str(e)}",
            error=str(e)
        )


async def reject_order_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para rejeitar um pedido"""
    try:
        from services.order_service import order_service
        
        order_id = params.get('order_id')
        order_number = params.get('order_number')
        user_id = params.get('user_id', 'system')
        admin_notes = params.get('admin_notes')
        
        if not order_id and not order_number:
            return CommandResult(
                success=False,
                message="ID ou número do pedido é obrigatório",
                error="order_identifier_required"
            )
        
        # Buscar pedido primeiro
        if order_id:
            order = await order_service.get_order(order_id)
        else:
            order = await order_service.get_order_by_number(order_number)
        
        if not order:
            return CommandResult(
                success=False,
                message="Pedido não encontrado",
                error="order_not_found"
            )
        
        # Rejeitar pedido
        updated_order = await order_service.reject_order(
            order_id=order.id,
            user_id=user_id,
            admin_notes=admin_notes
        )
        
        if not updated_order:
            return CommandResult(
                success=False,
                message="Erro ao rejeitar pedido",
                error="rejection_failed"
            )
        
        return CommandResult(
            success=True,
            message=f"Pedido {updated_order.order_number} rejeitado. Estoque devolvido.",
            data={
                "order": {
                    "id": updated_order.id,
                    "order_number": updated_order.order_number,
                    "status": updated_order.status
                }
            }
        )
    except Exception as e:
        logger.error("Erro ao executar reject_order", error=str(e))
        return CommandResult(
            success=False,
            message=f"Erro ao rejeitar pedido: {str(e)}",
            error=str(e)
        )


async def update_order_status_action(params: Dict[str, Any]) -> CommandResult:
    """Ação para atualizar status de um pedido"""
    try:
        from services.order_service import order_service
        from models.order_models import OrderStatus
        
        order_id = params.get('order_id')
        order_number = params.get('order_number')
        new_status = params.get('status')
        user_id = params.get('user_id', 'system')
        admin_notes = params.get('admin_notes')
        
        if not order_id and not order_number:
            return CommandResult(
                success=False,
                message="ID ou número do pedido é obrigatório",
                error="order_identifier_required"
            )
        
        if not new_status:
            return CommandResult(
                success=False,
                message="Novo status é obrigatório",
                error="status_required"
            )
        
        # Converter status para enum
        try:
            order_status = OrderStatus(new_status.lower())
        except ValueError:
            return CommandResult(
                success=False,
                message=f"Status inválido: {new_status}. Use: pending, confirmed, processing, shipped, delivered, cancelled, rejected",
                error="invalid_status"
            )
        
        # Buscar pedido primeiro
        if order_id:
            order = await order_service.get_order(order_id)
        else:
            order = await order_service.get_order_by_number(order_number)
        
        if not order:
            return CommandResult(
                success=False,
                message="Pedido não encontrado",
                error="order_not_found"
            )
        
        # Atualizar status
        updated_order = await order_service.update_order_status(
            order_id=order.id,
            new_status=order_status,
            user_id=user_id,
            admin_notes=admin_notes
        )
        
        if not updated_order:
            return CommandResult(
                success=False,
                message="Erro ao atualizar status do pedido",
                error="update_failed"
            )
        
        return CommandResult(
            success=True,
            message=f"Status do pedido {updated_order.order_number} atualizado para '{order_status.value}'",
            data={
                "order": {
                    "id": updated_order.id,
                    "order_number": updated_order.order_number,
                    "status": updated_order.status
                }
            }
        )
    except Exception as e:
        logger.error("Erro ao executar update_order_status", error=str(e))
        return CommandResult(
            success=False,
            message=f"Erro ao atualizar status: {str(e)}",
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
    ),
    
    "show_menu": CommandDefinition(
        id="show_menu",
        name="Menu Principal",
        description="Exibe o menu principal com botões de navegação",
        requires_confirmation=False,
        category=CommandCategory.VIEW,
        permissions=[],  # Sem permissões específicas - qualquer usuário pode ver o menu
        parameters=[],
        action=show_menu_action,
        aliases=["menu", "m", "início", "inicio", "home"],
        examples=[
            "/menu",
            "menu",
            "mostrar menu"
        ]
    ),
    
    "show_pedidos_menu": CommandDefinition(
        id="show_pedidos_menu",
        name="Menu de Pedidos",
        description="Exibe o menu de pedidos com botões de navegação",
        requires_confirmation=False,
        category=CommandCategory.VIEW,
        permissions=[],  # Sem permissões específicas
        parameters=[],
        action=show_pedidos_menu_action,
        aliases=["pedidos", "p", "menu pedidos"],
        examples=[
            "/pedidos",
            "pedidos",
            "menu pedidos"
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

# Comandos de Pedidos (E-commerce)
ORDER_COMMANDS: Dict[str, CommandDefinition] = {
    "list_orders": CommandDefinition(
        id="list_orders",
        name="Listar Pedidos",
        description="Lista pedidos com filtros opcionais",
        requires_confirmation=False,
        category=CommandCategory.VIEW,
        permissions=["view_orders"],
        parameters=[
            ParameterDefinition(
                name="status",
                type="string",
                required=False,
                description="Filtrar por status (pending, confirmed, processing, shipped, delivered, cancelled, rejected)"
            ),
            ParameterDefinition(
                name="customer_id",
                type="string",
                required=False,
                description="Filtrar por ID do cliente"
            ),
            ParameterDefinition(
                name="limit",
                type="integer",
                required=False,
                description="Limite de resultados (padrão: 10)"
            )
        ],
        action=list_orders_action,
        aliases=["pedidos", "orders", "listar pedidos", "ver pedidos"],
        examples=[
            "Liste os pedidos pendentes",
            "Mostre os pedidos",
            "Pedidos com status pending",
            "list orders status=pending"
        ]
    ),
    
    "show_order": CommandDefinition(
        id="show_order",
        name="Ver Pedido",
        description="Exibe detalhes completos de um pedido",
        requires_confirmation=False,
        category=CommandCategory.VIEW,
        permissions=["view_orders"],
        parameters=[
            ParameterDefinition(
                name="order_id",
                type="integer",
                required=False,
                description="ID do pedido"
            ),
            ParameterDefinition(
                name="order_number",
                type="string",
                required=False,
                description="Número do pedido (ex: ORD-20240101-ABC12)"
            )
        ],
        action=show_order_action,
        aliases=["pedido", "order", "ver pedido", "detalhes pedido"],
        examples=[
            "Mostre o pedido 123",
            "Detalhes do pedido ORD-20240101-ABC12",
            "show order 123"
        ]
    ),
    
    "approve_order": CommandDefinition(
        id="approve_order",
        name="Aprovar Pedido",
        description="Aprova um pedido (muda status para CONFIRMED)",
        requires_confirmation=True,
        category=CommandCategory.MODIFY,
        permissions=["process_orders"],
        parameters=[
            ParameterDefinition(
                name="order_id",
                type="integer",
                required=False,
                description="ID do pedido"
            ),
            ParameterDefinition(
                name="order_number",
                type="string",
                required=False,
                description="Número do pedido"
            ),
            ParameterDefinition(
                name="admin_notes",
                type="string",
                required=False,
                description="Notas administrativas"
            )
        ],
        action=approve_order_action,
        aliases=["aprovar", "approve", "aprovar pedido"],
        examples=[
            "Aprove o pedido 123",
            "Aprovar pedido ORD-20240101-ABC12",
            "approve order 123"
        ]
    ),
    
    "reject_order": CommandDefinition(
        id="reject_order",
        name="Rejeitar Pedido",
        description="Rejeita um pedido (muda status para REJECTED e devolve estoque)",
        requires_confirmation=True,
        category=CommandCategory.MODIFY,
        permissions=["process_orders"],
        parameters=[
            ParameterDefinition(
                name="order_id",
                type="integer",
                required=False,
                description="ID do pedido"
            ),
            ParameterDefinition(
                name="order_number",
                type="string",
                required=False,
                description="Número do pedido"
            ),
            ParameterDefinition(
                name="admin_notes",
                type="string",
                required=False,
                description="Motivo da rejeição"
            )
        ],
        action=reject_order_action,
        aliases=["rejeitar", "reject", "rejeitar pedido"],
        examples=[
            "Rejeite o pedido 123",
            "Rejeitar pedido ORD-20240101-ABC12",
            "reject order 123 motivo='Estoque insuficiente'"
        ]
    ),
    
    "update_order_status": CommandDefinition(
        id="update_order_status",
        name="Atualizar Status do Pedido",
        description="Atualiza o status de um pedido",
        requires_confirmation=True,
        category=CommandCategory.MODIFY,
        permissions=["process_orders"],
        parameters=[
            ParameterDefinition(
                name="order_id",
                type="integer",
                required=False,
                description="ID do pedido"
            ),
            ParameterDefinition(
                name="order_number",
                type="string",
                required=False,
                description="Número do pedido"
            ),
            ParameterDefinition(
                name="status",
                type="string",
                required=True,
                description="Novo status (pending, confirmed, processing, shipped, delivered, cancelled, rejected)"
            ),
            ParameterDefinition(
                name="admin_notes",
                type="string",
                required=False,
                description="Notas administrativas"
            )
        ],
        action=update_order_status_action,
        aliases=["atualizar status", "update status", "mudar status"],
        examples=[
            "Atualize o status do pedido 123 para shipped",
            "Mudar status do pedido ORD-20240101-ABC12 para processing",
            "update order status 123 status=shipped"
        ]
    )
}

# Dicionário com todos os comandos
ALL_COMMANDS: Dict[str, CommandDefinition] = {
    **VIEW_COMMANDS,
    **CREATE_COMMANDS,
    **TRADE_COMMANDS,
    **ORDER_COMMANDS
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

