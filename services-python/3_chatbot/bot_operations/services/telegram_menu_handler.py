"""
Handler para processar menus e callbacks do Telegram
"""

from typing import Dict, Any, Optional
import structlog
import uuid
from datetime import datetime

from services.pedido_inline_service import pedido_inline_service, PRODUTOS
from services.telegram_order_parser import telegram_order_parser

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
        # Normalizar callback_data
        callback_data = callback_data.strip() if callback_data else ""
        
        logger.info("Processando callback", callback_data=callback_data)
        
        # Verificar se é menu_sair ANTES de processar
        if callback_data == "menu_sair":
            logger.info("Callback 'menu_sair' detectado diretamente - excluindo mensagem")
            return {
                "response": "",
                "has_keyboard": False,
                "delete_message": True
            }
        
        if callback_data.startswith("menu_"):
            menu_type = callback_data.replace("menu_", "", 1)  # Substituir apenas a primeira ocorrência
            result = await self._handle_menu_callback(menu_type)
            logger.info(
                "Resultado do callback de menu",
                callback_data=callback_data,
                menu_type=menu_type,
                delete_message=result.get("delete_message"),
                has_response=bool(result.get("response"))
            )
            return result
        
        # Outros tipos de callback podem ser adicionados aqui
        logger.warning("Callback não reconhecido", callback_data=callback_data)
        return {
            "response": "Callback não reconhecido",
            "has_keyboard": False
        }
    
    async def _handle_menu_callback(self, menu_type: str) -> Dict[str, Any]:
        """Processa callback de menu específico"""
        
        # Normalizar menu_type (remover espaços e converter para minúsculas)
        menu_type_normalized = menu_type.strip().lower() if menu_type else ""
        
        logger.info("Processando callback de menu", menu_type=menu_type, normalized=menu_type_normalized)
        
        # Verificar "sair" PRIMEIRO, antes de qualquer outra coisa
        # Isso evita que seja processado como um menu inexistente
        if menu_type_normalized == "sair" or menu_type == "sair":
            # Excluir mensagem do menu
            logger.info("Callback 'sair' detectado - excluindo mensagem")
            return {
                "response": "",  # Resposta vazia - não exibir nada
                "has_keyboard": False,
                "delete_message": True
            }
        
        if menu_type_normalized == "pedidos":
            return self._get_pedidos_menu()
        elif menu_type_normalized == "entregas":
            return self._get_entregas_menu()
        elif menu_type_normalized == "estoque":
            return self._get_estoque_menu()
        elif menu_type_normalized == "financeiro":
            return self._get_financeiro_menu()
        elif menu_type_normalized == "clientes":
            return self._get_clientes_menu()
        elif menu_type_normalized == "admin":
            return self._get_admin_menu()
        elif menu_type_normalized == "voltar":
            return self._get_main_menu()
        else:
            # Se não for nenhum menu conhecido, verificar se é "sair" novamente (caso a normalização tenha falhado)
            if "sair" in menu_type_normalized or "sair" in menu_type.lower():
                logger.info("Callback 'sair' detectado (fallback) - excluindo mensagem")
                return {
                    "response": "",  # Resposta vazia - não exibir nada
                    "has_keyboard": False,
                    "delete_message": True
                }
            
            logger.warning("Menu não encontrado", menu_type=menu_type, normalized=menu_type_normalized)
            # NÃO retornar mensagem de erro - apenas retornar resposta vazia
            # Isso evita exibir erro quando o usuário clica em "sair"
            return {
                "response": "",  # Resposta vazia ao invés de erro
                "has_keyboard": False,
                "delete_message": True  # Tentar excluir mesmo assim
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
                {"text": "🔙 Voltar", "callback_data": "menu_voltar"},
                {"text": "❌ Sair", "callback_data": "menu_sair"}
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
            [
                {"text": "🔙 Voltar", "callback_data": "menu_voltar"},
                {"text": "❌ Sair", "callback_data": "menu_sair"}
            ]
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
            [
                {"text": "🔙 Voltar", "callback_data": "menu_voltar"},
                {"text": "❌ Sair", "callback_data": "menu_sair"}
            ]
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
            [
                {"text": "🔙 Voltar", "callback_data": "menu_voltar"},
                {"text": "❌ Sair", "callback_data": "menu_sair"}
            ]
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
            [
                {"text": "🔙 Voltar", "callback_data": "menu_voltar"},
                {"text": "❌ Sair", "callback_data": "menu_sair"}
            ]
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
            [
                {"text": "🔙 Voltar", "callback_data": "menu_voltar"},
                {"text": "❌ Sair", "callback_data": "menu_sair"}
            ]
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
            ],
            [
                {"text": "❌ Sair", "callback_data": "menu_sair"}
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
    
    async def handle_pedido_callback(self, callback_data: str, user_id: str = None, token: Optional[str] = None) -> Dict[str, Any]:
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
        
        # Processar callbacks de pedido salvo (order:edit, order:delete, order:saved)
        if callback_data.startswith("order:"):
            return await self._handle_saved_order_callback(callback_data, user_id, token=token)
        
        # Processar novos callbacks do sistema melhorado
        if (callback_data.startswith("prod:") or 
            callback_data.startswith("sel:") or 
            callback_data.startswith("action:") or
            callback_data == "noop"):
            return await self._handle_pedido_inline_callback(callback_data, user_id, token=token)
        
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
    
    async def _handle_pedido_inline_callback(self, callback_data: str, user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
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
            logger.info("=" * 70)
            logger.info("ACTION:SAVE - INICIANDO SALVAMENTO DE PEDIDO")
            logger.info("=" * 70)
            logger.info(
                "Dados do pedido inline recebido",
                user_id=user_id,
                pedido_status=pedido.get("status"),
                pedido_nome=pedido.get("nome"),
                pedido_data=pedido.get("data"),
                pedido_endereco=pedido.get("endereco"),
                produtos_count=len([k for k, v in pedido.get("produtos", {}).items() if v > 0]),
                produtos={k: v for k, v in pedido.get("produtos", {}).items() if v > 0},
                pedido_completo=pedido
            )
            
            # Tentar salvar no e-commerce service ANTES de mostrar sucesso
            texto_sucesso = None
            texto_erro = None
            
            try:
                # Converter pedido inline para formato do e-commerce
                logger.info("ETAPA 1: Convertendo pedido inline para formato do e-commerce")
                order_data = _convert_inline_order_to_ecommerce(pedido)
                
                logger.info(
                    "ETAPA 1: Pedido convertido",
                    has_order_data=bool(order_data),
                    order_data=order_data if order_data else None
                )
                
                if order_data:
                    # Token já foi passado como parâmetro do método
                    logger.info("ETAPA 2: Verificando token")
                    if not token:
                        logger.warning(
                            "Token nao fornecido para salvar pedido inline",
                            user_id=user_id,
                            callback_data=callback_data
                        )
                    else:
                        logger.info(
                            "Token disponivel",
                            token_preview=token[:20] + "..." if token else None,
                            token_length=len(token) if token else 0
                        )
                    
                    # Gerar UUID válido para conversation_id (não usar string)
                    conversation_id = str(uuid.uuid4())
                    
                    logger.info("=" * 70)
                    logger.info("ETAPA 3: Chamando process_orders")
                    logger.info("=" * 70)
                    logger.info(
                        "Parametros da chamada",
                        conversation_id=conversation_id,
                        conversation_id_type=type(conversation_id).__name__,
                        orders_count=1,
                        has_token=bool(token),
                        token_preview=token[:20] + "..." if token else None,
                        order_data_enviado=order_data
                    )
                    
                    # Log do JSON que será enviado
                    try:
                        import json
                        order_json = json.dumps({"orders": [order_data], "conversation_id": conversation_id}, indent=2, ensure_ascii=False)
                        logger.info("=" * 70)
                        logger.info("JSON QUE SERA ENVIADO AO E-COMMERCE:")
                        logger.info(order_json)
                        logger.info("=" * 70)
                    except Exception as e:
                        logger.warning(f"Nao foi possivel serializar JSON: {e}")
                    
                    success, message, created_orders = await telegram_order_parser.process_orders(
                        [order_data],
                        conversation_id=conversation_id,
                        token=token
                    )
                    
                    logger.info("=" * 70)
                    logger.info("ETAPA 4: RESULTADO do process_orders")
                    logger.info("=" * 70)
                    logger.info(
                        "Resultado detalhado",
                        success=success,
                        message=message,
                        has_created_orders=bool(created_orders),
                        created_orders_count=len(created_orders) if created_orders else 0
                    )
                    
                    if created_orders:
                        try:
                            import json
                            created_orders_json = json.dumps(created_orders, indent=2, ensure_ascii=False, default=str)
                            logger.info("RESPOSTA COMPLETA DO E-COMMERCE (JSON):")
                            logger.info(created_orders_json)
                        except Exception as e:
                            logger.warning(f"Nao foi possivel serializar resposta: {e}")
                            logger.info("Resposta como string:", response=str(created_orders)[:1000])
                    
                    if success and created_orders:
                        # Pedido realmente salvo no e-commerce
                        order_id = created_orders[0].get("id")
                        logger.info("=" * 70)
                        logger.info("PEDIDO SALVO COM SUCESSO NO E-COMMERCE!")
                        logger.info("=" * 70)
                        logger.info(
                            "Detalhes do pedido salvo",
                            user_id=user_id,
                            order_id=order_id,
                            order_full=created_orders[0],
                            pedido_original=pedido
                        )
                        
                        pedido["status"] = "SALVO"
                        pedido["ecommerce_order_id"] = order_id
                        pedido_inline_service.user_pedidos[user_id] = pedido
                        
                        # Renderizar pedido salvo (apenas itens) com botões Editar/Deletar/Sair
                        texto = pedido_inline_service.render_saved_order(pedido, order_id=order_id)
                        keyboard = pedido_inline_service.build_saved_order_keyboard(order_id=order_id)
                        
                        return {
                            "response": texto,
                            "has_keyboard": True,
                            "keyboard_type": "inline",
                            "edit_message": True,
                            "reply_markup": keyboard,
                            "parse_mode": "HTML"
                        }
                    else:
                        # Falha ao salvar
                        logger.error("=" * 70)
                        logger.error("FALHA AO SALVAR PEDIDO NO E-COMMERCE")
                        logger.error("=" * 70)
                        logger.error(
                            "Detalhes do erro",
                            user_id=user_id,
                            success=success,
                            error_message=message,
                            has_created_orders=bool(created_orders),
                            created_orders=created_orders,
                            pedido_original=pedido,
                            order_data_enviado=order_data
                        )
                        texto_erro = message or "❌ Erro ao salvar pedido no e-commerce. O pedido NÃO foi salvo."
                else:
                    logger.error(
                        "Pedido invalido - sem dados para enviar",
                        user_id=user_id,
                        pedido=pedido
                    )
                    texto_erro = "❌ Erro: Pedido inválido. Verifique se há produtos no pedido."
                    
            except Exception as e:
                logger.error("=" * 70)
                logger.error("EXCECAO ao salvar pedido")
                logger.error("=" * 70)
                logger.error(
                    "Detalhes da excecao",
                    user_id=user_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    pedido=pedido,
                    exc_info=True
                )
                texto_erro = f"❌ Erro ao salvar pedido: {str(e)}. O pedido NÃO foi salvo."
            
            # Atualizar interface (apenas se não retornou antes)
            if texto_erro:
                texto = pedido_inline_service.render_text(pedido, panel_state, texto_erro)
                keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
            else:
                # Se chegou aqui e não retornou antes, algo deu errado
                texto = pedido_inline_service.render_text(pedido, panel_state, "⚠️ Erro desconhecido ao salvar pedido.")
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
        
        # action:close - Fechar e excluir mensagem
        elif callback_data == "action:close":
            pedido_inline_service.cancelar_pedido(user_id)
            return {
                "response": "",
                "has_keyboard": False,
                "delete_message": True
            }
        
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
    
    async def _handle_saved_order_callback(self, callback_data: str, user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa callbacks de pedido salvo (Editar, Deletar, Sair)
        
        Callbacks:
        - order:edit:{order_id} - Carrega pedido salvo para edição
        - order:delete:{order_id} - Deleta pedido salvo
        - order:saved:sair - Fecha e sai
        """
        logger.info(
            "Processando callback de pedido salvo",
            callback_data=callback_data,
            user_id=user_id
        )
        
        # order:saved:sair - Fechar e sair
        if callback_data == "order:saved:sair":
            return {
                "response": "",
                "has_keyboard": False,
                "delete_message": True
            }
        
        # order:edit:{order_id} - Carregar pedido para edição
        if callback_data.startswith("order:edit:"):
            order_id = callback_data.replace("order:edit:", "")
            
            # Buscar pedido salvo do usuário
            pedido = pedido_inline_service.init_pedido(user_id)
            
            # Verificar se o pedido foi salvo e tem o order_id
            if pedido.get("status") == "SALVO" and pedido.get("ecommerce_order_id"):
                logger.info(
                    "Carregando pedido salvo para edicao",
                    user_id=user_id,
                    order_id=pedido.get("ecommerce_order_id"),
                    pedido=pedido
                )
                
                # Resetar status para edição
                pedido["status"] = "EM_EDICAO"
                pedido_inline_service.user_pedidos[user_id] = pedido
                
                # Resetar estado do painel
                panel_state = pedido_inline_service.get_panel_state(user_id)
                panel_state["selected_key"] = None
                panel_state["awaiting"] = None
                pedido_inline_service.user_panel_state[user_id] = panel_state
                
                # Renderizar pedido no formato de edição
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
            else:
                logger.warning(
                    "Pedido nao encontrado ou nao salvo",
                    user_id=user_id,
                    pedido_status=pedido.get("status"),
                    has_order_id=bool(pedido.get("ecommerce_order_id"))
                )
                return {
                    "response": "⚠️ Pedido não encontrado ou não foi salvo.",
                    "has_keyboard": False
                }
        
        # order:delete:{order_id} - Deletar pedido
        if callback_data.startswith("order:delete:"):
            order_id = callback_data.replace("order:delete:", "")
            
            logger.info(
                "Deletando pedido salvo",
                user_id=user_id,
                order_id=order_id
            )
            
            # Limpar pedido do usuário
            pedido_inline_service.cancelar_pedido(user_id)
            
            return {
                "response": "🗑️ Pedido deletado com sucesso!",
                "has_keyboard": False,
                "delete_message": True
            }
        
        # Callback não reconhecido
        logger.warning(
            "Callback de pedido salvo nao reconhecido",
            callback_data=callback_data,
            user_id=user_id
        )
        return {
            "response": "⚠️ Ação não reconhecida.",
            "has_keyboard": False
        }
    
    async def _handle_saved_order_callback(self, callback_data: str, user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Processa callbacks de pedido salvo (Editar, Deletar, Sair)
        
        Callbacks:
        - order:edit:{order_id} - Carrega pedido salvo para edição
        - order:delete:{order_id} - Deleta pedido salvo
        - order:saved:sair - Fecha e sai
        """
        logger.info(
            "Processando callback de pedido salvo",
            callback_data=callback_data,
            user_id=user_id
        )
        
        # order:saved:sair - Fechar e sair
        if callback_data == "order:saved:sair":
            return {
                "response": "",
                "has_keyboard": False,
                "delete_message": True
            }
        
        # order:edit:{order_id} ou order:edit - Carregar pedido para edição
        if callback_data.startswith("order:edit"):
            order_id_param = callback_data.replace("order:edit:", "") if ":" in callback_data else None
            
            # Buscar pedido salvo do usuário
            pedido = pedido_inline_service.user_pedidos.get(user_id)
            
            if not pedido:
                logger.warning(
                    "Pedido nao encontrado para edicao",
                    user_id=user_id
                )
                return {
                    "response": "⚠️ Pedido não encontrado.",
                    "has_keyboard": False
                }
            
            # Verificar se o pedido foi salvo (mesmo que não tenha order_id ainda)
            if pedido.get("status") == "SALVO" or pedido.get("ecommerce_order_id"):
                logger.info(
                    "Carregando pedido salvo para edicao",
                    user_id=user_id,
                    order_id=pedido.get("ecommerce_order_id"),
                    pedido_status=pedido.get("status"),
                    pedido=pedido
                )
                
                # Criar uma cópia do pedido para edição (manter o original salvo)
                # Mas na verdade vamos reutilizar o mesmo pedido, apenas mudando o status
                pedido["status"] = "EM_EDICAO"
                # Manter o ecommerce_order_id para referência
                pedido_inline_service.user_pedidos[user_id] = pedido
                
                # Resetar estado do painel
                panel_state = pedido_inline_service.get_panel_state(user_id)
                panel_state["selected_key"] = None
                panel_state["awaiting"] = None
                pedido_inline_service.user_panel_state[user_id] = panel_state
                
                # Renderizar pedido no formato de edição
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
            else:
                logger.warning(
                    "Pedido nao esta salvo",
                    user_id=user_id,
                    pedido_status=pedido.get("status")
                )
                return {
                    "response": "⚠️ Pedido não foi salvo ainda.",
                    "has_keyboard": False
                }
        
        # order:delete:{order_id} ou order:delete - Deletar pedido
        if callback_data.startswith("order:delete"):
            order_id = callback_data.replace("order:delete:", "") if ":" in callback_data else None
            
            logger.info(
                "Deletando pedido salvo",
                user_id=user_id,
                order_id=order_id
            )
            
            # Limpar pedido do usuário
            pedido_inline_service.cancelar_pedido(user_id)
            
            return {
                "response": "🗑️ Pedido deletado com sucesso!",
                "has_keyboard": False,
                "delete_message": True
            }
        
        # Callback não reconhecido
        logger.warning(
            "Callback de pedido salvo nao reconhecido",
            callback_data=callback_data,
            user_id=user_id
        )
        return {
            "response": "⚠️ Ação não reconhecida.",
            "has_keyboard": False
        }
    
    async def _handle_pedido_inline_callback_old(self, callback_data: str, user_id: str) -> Dict[str, Any]:
        """Processa callbacks antigos (compatibilidade)"""
        # Manter código antigo para compatibilidade se necessário
        return {
            "response": "Callback antigo não suportado. Use o novo sistema.",
            "has_keyboard": False
        }


def _convert_inline_order_to_ecommerce(pedido: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Converte pedido do formato inline para formato do e-commerce service
    
    Args:
        pedido: Pedido no formato inline (com produtos como dict de chaves)
        
    Returns:
        Pedido no formato do e-commerce ou None se inválido
    """
    # Verificar se há produtos com quantidade > 0
    produtos = pedido.get("produtos", {})
    items = []
    
    for produto_key, quantidade in produtos.items():
        if quantidade > 0 and produto_key in PRODUTOS:
            produto_info = PRODUTOS[produto_key]
            items.append({
                "qty": quantidade,
                "product_name": produto_info["nome"]
            })
    
    if not items:
        return None
    
    # Montar pedido no formato do e-commerce
    order_data = {
        "contact_name": pedido.get("nome") or None,
        "establishment_name": None,
        "contact_phone": None,
        "price_profile_hint": None,
        "items": items
    }
    
    return order_data


# Instância global
telegram_menu_handler = TelegramMenuHandler()
