"""
Handler para processar menus e callbacks do Telegram
"""

from typing import Dict, Any, Optional
import structlog

from services.pedido_inline_service import pedido_inline_service, PRODUTOS

logger = structlog.get_logger(__name__)


class TelegramMenuHandler:
    """Gerencia menus e callbacks do Telegram"""
    
    async def handle_callback(self, callback_data: str) -> Dict[str, Any]:
        """
        Processa callback_data e retorna resposta apropriada
        
        Args:
            callback_data: Dados do callback (ex: "menu_pedidos", "menu_estoque")
            
        Returns:
            Dict com resposta e botões se necessário
        """
        if callback_data.startswith("menu_"):
            menu_type = callback_data.replace("menu_", "")
            return await self._handle_menu_callback(menu_type)
        
        # Outros tipos de callback podem ser adicionados aqui
        return {
            "response": "Callback não reconhecido",
            "has_keyboard": False
        }
    
    async def _handle_menu_callback(self, menu_type: str) -> Dict[str, Any]:
        """Processa callback de menu específico"""
        
        if menu_type == "pedidos":
            return self._get_pedidos_menu()
        elif menu_type == "entregas":
            return self._get_entregas_menu()
        elif menu_type == "estoque":
            return self._get_estoque_menu()
        elif menu_type == "financeiro":
            return self._get_financeiro_menu()
        elif menu_type == "clientes":
            return self._get_clientes_menu()
        elif menu_type == "admin":
            return self._get_admin_menu()
        elif menu_type == "voltar":
            return self._get_main_menu()
        else:
            return {
                "response": f"Menu '{menu_type}' não encontrado",
                "has_keyboard": False
            }
    
    def _get_pedidos_menu(self) -> Dict[str, Any]:
        """Retorna menu de pedidos"""
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
        
        return {
            "response": "📦 Menu de Pedidos - Selecione uma opção:",
            "has_keyboard": True,
            "keyboard_type": "inline",
            "edit_message": True,  # Editar mensagem existente
            "reply_markup": {
                "inline_keyboard": inline_keyboard
            }
        }
    
    def _get_entregas_menu(self) -> Dict[str, Any]:
        """Retorna menu de entregas"""
        inline_keyboard = [
            [{"text": "🚚 Rotas de Entrega", "callback_data": "entrega_rotas"}],
            [{"text": "📍 Paradas", "callback_data": "entrega_paradas"}],
            [{"text": "✅ Confirmar Entrega", "callback_data": "entrega_confirmar"}],
            [{"text": "🔙 Voltar", "callback_data": "menu_voltar"}]
        ]
        
        return {
            "response": "🚚 Menu de Entregas\n\nSelecione uma opção:",
            "has_keyboard": True,
            "keyboard_type": "inline",
            "edit_message": True,  # Editar mensagem existente
            "reply_markup": {
                "inline_keyboard": inline_keyboard
            }
        }
    
    def _get_estoque_menu(self) -> Dict[str, Any]:
        """Retorna menu de estoque"""
        inline_keyboard = [
            [{"text": "📦 Listar Produtos", "callback_data": "estoque_listar"}],
            [{"text": "➕ Adicionar Produto", "callback_data": "estoque_adicionar"}],
            [{"text": "✏️ Editar Produto", "callback_data": "estoque_editar"}],
            [{"text": "📊 Relatório de Estoque", "callback_data": "estoque_relatorio"}],
            [{"text": "🔙 Voltar", "callback_data": "menu_voltar"}]
        ]
        
        return {
            "response": "🥬 Menu de Estoque\n\nSelecione uma opção:",
            "has_keyboard": True,
            "keyboard_type": "inline",
            "edit_message": True,  # Editar mensagem existente
            "reply_markup": {
                "inline_keyboard": inline_keyboard
            }
        }
    
    def _get_financeiro_menu(self) -> Dict[str, Any]:
        """Retorna menu financeiro"""
        inline_keyboard = [
            [{"text": "💰 Pagamentos", "callback_data": "financeiro_pagamentos"}],
            [{"text": "📊 Relatórios", "callback_data": "financeiro_relatorios"}],
            [{"text": "💳 Métodos de Pagamento", "callback_data": "financeiro_metodos"}],
            [{"text": "🔙 Voltar", "callback_data": "menu_voltar"}]
        ]
        
        return {
            "response": "💰 Menu Financeiro\n\nSelecione uma opção:",
            "has_keyboard": True,
            "keyboard_type": "inline",
            "edit_message": True,  # Editar mensagem existente
            "reply_markup": {
                "inline_keyboard": inline_keyboard
            }
        }
    
    def _get_clientes_menu(self) -> Dict[str, Any]:
        """Retorna menu de clientes"""
        inline_keyboard = [
            [{"text": "👤 Listar Clientes", "callback_data": "cliente_listar"}],
            [{"text": "➕ Novo Cliente", "callback_data": "cliente_novo"}],
            [{"text": "🔍 Buscar Cliente", "callback_data": "cliente_buscar"}],
            [{"text": "📍 Endereços", "callback_data": "cliente_enderecos"}],
            [{"text": "🔙 Voltar", "callback_data": "menu_voltar"}]
        ]
        
        return {
            "response": "👤 Menu de Clientes\n\nSelecione uma opção:",
            "has_keyboard": True,
            "keyboard_type": "inline",
            "edit_message": True,  # Editar mensagem existente
            "reply_markup": {
                "inline_keyboard": inline_keyboard
            }
        }
    
    def _get_admin_menu(self) -> Dict[str, Any]:
        """Retorna menu administrativo"""
        inline_keyboard = [
            [{"text": "⚙️ Configurações", "callback_data": "admin_config"}],
            [{"text": "👥 Usuários", "callback_data": "admin_usuarios"}],
            [{"text": "📝 Logs", "callback_data": "admin_logs"}],
            [{"text": "🔙 Voltar", "callback_data": "menu_voltar"}]
        ]
        
        return {
            "response": "⚙️ Menu Administrativo\n\nSelecione uma opção:",
            "has_keyboard": True,
            "keyboard_type": "inline",
            "edit_message": True,  # Editar mensagem existente
            "reply_markup": {
                "inline_keyboard": inline_keyboard
            }
        }
    
    def _get_main_menu(self) -> Dict[str, Any]:
        """Retorna menu principal"""
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
        
        return {
            "response": "Menu Principal - Selecione uma opção:",
            "has_keyboard": True,
            "keyboard_type": "inline",
            "edit_message": True,  # Editar mensagem existente (quando voltar)
            "reply_markup": {
                "inline_keyboard": inline_keyboard
            }
        }
    
    async def handle_pedido_callback(self, callback_data: str, user_id: str = None) -> Dict[str, Any]:
        """Processa callbacks específicos de pedidos"""
        
        # Novo sistema de pedido inline (UX melhorada)
        if callback_data == "pedido_novo":
            if not user_id:
                return {
                    "response": "Erro: user_id não fornecido",
                    "has_keyboard": False
                }
            
            pedido = pedido_inline_service.init_pedido(user_id)
            pedido_inline_service.reset_pedido(user_id)
            panel_state = pedido_inline_service.get_panel_state(user_id)
            
            texto = pedido_inline_service.render_text(pedido, panel_state)
            keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
            
            return {
                "response": texto,
                "has_keyboard": True,
                "keyboard_type": "inline",
                "edit_message": True,  # Editar mensagem (substitui menu de pedidos)
                "reply_markup": keyboard,
                "parse_mode": "HTML"
            }
        
        # Processar novos callbacks do sistema melhorado
        if (callback_data.startswith("prod:") or 
            callback_data.startswith("sel:") or 
            callback_data.startswith("action:") or
            callback_data == "noop"):
            return await self._handle_pedido_inline_callback(callback_data, user_id)
        
        # Processar callbacks antigos (manter compatibilidade)
        if callback_data.startswith("pedido_"):
            return await self._handle_pedido_inline_callback_old(callback_data, user_id)
        
        # Callbacks antigos (manter compatibilidade)
        if callback_data == "pedido_listar":
            return {
                "response": (
                    "📋 Listar Pedidos\n\n"
                    "Listando pedidos...\n\n"
                    "Use o comando: /list_orders\n"
                    "Ou digite: 'listar pedidos'\n\n"
                    "Você pode filtrar por status:\n"
                    "- listar pedidos pendentes\n"
                    "- listar pedidos confirmados"
                ),
                "has_keyboard": False,
                "trigger_command": "list_orders"  # Flag para executar comando
            }
        elif callback_data == "pedido_buscar":
            return {
                "response": (
                    "🔎 Buscar Pedido\n\n"
                    "Para buscar um pedido, informe:\n\n"
                    "• ID do pedido (ex: 123)\n"
                    "• Número do pedido (ex: ORD-20240101-ABC12)\n\n"
                    "Ou use o comando: /show_order\n"
                    "Ou digite: 'mostrar pedido 123'"
                ),
                "has_keyboard": False
            }
        elif callback_data == "pedido_editar":
            return {
                "response": (
                    "✏️ Editar Pedido\n\n"
                    "Para editar o status de um pedido:\n\n"
                    "Use: /update_order_status\n\n"
                    "Informe:\n"
                    "• ID ou número do pedido\n"
                    "• Novo status (pending, confirmed, processing, shipped, delivered, cancelled)\n\n"
                    "Exemplo: atualizar status do pedido 123 para confirmed"
                ),
                "has_keyboard": False
            }
        elif callback_data == "pedido_resumo":
            return {
                "response": (
                    "📊 Resumo por Data\n\n"
                    "Funcionalidade em desenvolvimento.\n\n"
                    "Em breve você poderá ver:\n"
                    "• Resumo de pedidos por dia/semana/mês\n"
                    "• Estatísticas de vendas\n"
                    "• Gráficos e relatórios"
                ),
                "has_keyboard": False
            }
        else:
            return {
                "response": "Opção não reconhecida",
                "has_keyboard": False
            }
    
    async def _handle_pedido_inline_callback(self, callback_data: str, user_id: str) -> Dict[str, Any]:
        """Processa callbacks do sistema de pedido inline (UX melhorada)"""
        if not user_id:
            return {
                "response": "Erro: user_id não fornecido",
                "has_keyboard": False
            }
        
        # Noop - apenas responder ao callback (não editar mensagem)
        if callback_data == "noop":
            return {
                "response": "",  # Vazio, apenas answerCallbackQuery
                "has_keyboard": False,
                "noop": True,
                "edit_message": False  # Não editar mensagem
            }
        
        pedido = pedido_inline_service.init_pedido(user_id)
        panel_state = pedido_inline_service.get_panel_state(user_id)
        
        # prod:select:<key> - Selecionar produto
        if callback_data.startswith("prod:select:"):
            produto_key = callback_data.replace("prod:select:", "")
            pedido_inline_service.set_selected_key(user_id, produto_key)
            panel_state = pedido_inline_service.get_panel_state(user_id)
            texto = pedido_inline_service.render_text(pedido, panel_state)
            keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
        
        # prod:inc:<key> / prod:dec:<key> - Incrementar/Decrementar (-1/+1)
        elif callback_data.startswith("prod:inc:"):
            produto_key = callback_data.replace("prod:inc:", "")
            pedido_inline_service.ajustar_quantidade(user_id, produto_key, 1)
            pedido_inline_service.set_selected_key(user_id, produto_key)  # Também seleciona
            panel_state = pedido_inline_service.get_panel_state(user_id)
            texto = pedido_inline_service.render_text(pedido, panel_state)
            keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
        
        elif callback_data.startswith("prod:dec:"):
            produto_key = callback_data.replace("prod:dec:", "")
            pedido_inline_service.ajustar_quantidade(user_id, produto_key, -1)
            pedido_inline_service.set_selected_key(user_id, produto_key)  # Também seleciona
            panel_state = pedido_inline_service.get_panel_state(user_id)
            texto = pedido_inline_service.render_text(pedido, panel_state)
            keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
        
        # prod:header:<campo> - Cabeçalho (nome, data, endereco, outros)
        elif callback_data.startswith("prod:header:"):
            campo = callback_data.replace("prod:header:", "")
            pedido_inline_service.set_awaiting(user_id, campo)
            instrucao = {
                "nome": "✏️ Digite o nome do cliente:",
                "data": "📅 Digite a data (DD/MM/AAAA):",
                "endereco": "📍 Digite o endereço:",
                "outros": "📝 Digite observações adicionais:"
            }.get(campo, "")
            texto = pedido_inline_service.render_text(pedido, panel_state, instrucao)
            keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
        
        # sel:add:<delta> - Ajustar produto selecionado
        elif callback_data.startswith("sel:add:"):
            delta_str = callback_data.replace("sel:add:", "")
            delta = int(delta_str)
            selected_key = pedido_inline_service.get_selected_key(user_id)
            if selected_key:
                pedido_inline_service.ajustar_quantidade(user_id, selected_key, delta)
                panel_state = pedido_inline_service.get_panel_state(user_id)
                texto = pedido_inline_service.render_text(pedido, panel_state)
                keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
            else:
                # Nenhum produto selecionado
                texto = pedido_inline_service.render_text(pedido, panel_state, "⚠️ Selecione um produto primeiro")
                keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
        
        # sel:set - Digitar quantidade do produto selecionado
        elif callback_data == "sel:set":
            selected_key = pedido_inline_service.get_selected_key(user_id)
            if selected_key:
                pedido_inline_service.set_awaiting(user_id, "set_qty")
                produto_info = PRODUTOS[selected_key]
                qtde = pedido["produtos"][selected_key]
                instrucao = f"✏️ Digite a quantidade para {produto_info['emoji']} {produto_info['nome']} (atual: {qtde}):"
                texto = pedido_inline_service.render_text(pedido, panel_state, instrucao)
                keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
            else:
                texto = pedido_inline_service.render_text(pedido, panel_state, "⚠️ Selecione um produto primeiro")
                keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
        
        # action:save - Salvar pedido
        elif callback_data == "action:save":
            pedido["status"] = "SALVO"
            pedido_inline_service.user_pedidos[user_id] = pedido
            logger.info("PEDIDO SALVO", pedido=pedido, user_id=user_id)
            texto = pedido_inline_service.render_text(pedido, panel_state, "✅ Pedido salvo com sucesso!")
            keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
        
        # action:zero - Zerar tudo
        elif callback_data == "action:zero":
            for key in pedido["produtos"]:
                pedido["produtos"][key] = 0
            pedido["outros"] = ""
            pedido_inline_service.user_pedidos[user_id] = pedido
            texto = pedido_inline_service.render_text(pedido, panel_state, "🔄 Todos os produtos foram zerados.")
            keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
        
        # action:cancel - Cancelar pedido
        elif callback_data == "action:cancel":
            pedido_inline_service.cancelar_pedido(user_id)
            return {
                "response": "❌ Pedido cancelado. Use o botão '🆕 Novo Pedido' para criar um novo.",
                "has_keyboard": False,
                "delete_message": True
            }
        
        # action:back - Voltar ao menu
        elif callback_data == "action:back":
            return await self._handle_menu_callback("voltar")
        
        else:
            # Fallback
            texto = pedido_inline_service.render_text(pedido, panel_state)
            keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
        
        return {
            "response": texto,
            "has_keyboard": True,
            "keyboard_type": "inline",
            "edit_message": True,
            "reply_markup": keyboard,
            "parse_mode": "HTML"
        }
    
    async def _handle_pedido_inline_callback_old(self, callback_data: str, user_id: str) -> Dict[str, Any]:
        """Processa callbacks antigos (compatibilidade)"""
        # Manter código antigo para compatibilidade se necessário
        return {
            "response": "Callback antigo não suportado. Use o novo sistema.",
            "has_keyboard": False
        }


# Instância global
telegram_menu_handler = TelegramMenuHandler()
