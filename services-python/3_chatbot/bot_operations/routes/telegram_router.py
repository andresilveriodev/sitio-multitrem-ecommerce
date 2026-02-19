"""
Router para integração com Telegram
"""

import structlog
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel

from services.product_conversation_flow import product_flow
from services.security import input_validator, ValidationLevel, permission_manager, PermissionLevel
from services.commands.analyzer import CommandAnalyzer
from services.commands.executor import CommandExecutor
from services.commands.types import CommandRequest, CommandAnalysis
from services.telegram_menu_handler import telegram_menu_handler
from auth.dependencies import get_current_user, check_colaborador_role
from config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chatbot", tags=["telegram"])

# Instâncias dos serviços de comandos
command_analyzer = CommandAnalyzer()
command_executor = CommandExecutor()


class TelegramMessage(BaseModel):
    """Modelo de mensagem do Telegram"""
    message: dict
    update_id: Optional[int] = None


def verify_telegram_token(request: Request, x_telegram_bot_token: Optional[str] = Header(None)) -> bool:
    """
    Verifica token do Telegram
    Por segurança, você deve configurar TELEGRAM_BOT_TOKEN no .env
    """
    # Token esperado (configure no .env)
    expected_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    
    if not expected_token:
        logger.warning("TELEGRAM_BOT_TOKEN não configurado no .env")
        # Em desenvolvimento, permite sem token (remova em produção!)
        return True
    
    # Verifica token no header
    if x_telegram_bot_token and x_telegram_bot_token == expected_token:
        return True
    
    # Verifica token no body (se enviado)
    return False


@router.post("/process-message-authenticated")
async def process_telegram_message(
    request: Request,
    x_telegram_bot_token: Optional[str] = Header(None, alias="X-Telegram-Bot-Token"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Endpoint para receber mensagens do Telegram
    Autenticação via:
    - Header X-Telegram-Bot-Token (validação do bot)
    - Header Authorization: Bearer <token> (validação do usuário Keycloak)
    Requer role 'colaborador' no token Keycloak
    """
    try:
        # Verifica autenticação do bot Telegram
        if not verify_telegram_token(request, x_telegram_bot_token):
            logger.warning("Tentativa de acesso sem token válido do bot")
            raise HTTPException(status_code=401, detail="Token do bot inválido")
        
        # Verificar se o usuário tem role 'colaborador'
        if not check_colaborador_role(current_user):
            username = current_user.get('preferred_username', 'unknown')
            logger.warning(
                "Acesso negado: usuário sem role 'colaborador'",
                username=username,
                user_id=current_user.get('sub'),
                telegram_endpoint=True
            )
            raise HTTPException(
                status_code=403,
                detail="Acesso negado: role 'colaborador' é necessário"
            )
        
        logger.info(
            "Acesso autorizado: usuário com role 'colaborador'",
            username=current_user.get('preferred_username'),
            user_id=current_user.get('sub'),
            telegram_endpoint=True
        )
        
        # Extrai dados do Telegram
        body = await request.json()
        
        # Verificar se é um callback_query (clique em botão)
        callback_query = body.get("callback_query")
        if callback_query:
            return await _handle_callback_query(callback_query, current_user)
        
        # Telegram envia updates no formato:
        # {
        #   "update_id": 123,
        #   "message": {
        #     "message_id": 456,
        #     "from": {"id": 789, "username": "user", "first_name": "Nome"},
        #     "chat": {"id": 789, "type": "private"},
        #     "date": 1234567890,
        #     "text": "mensagem"
        #   }
        # }
        
        message_data = body.get("message") or body
        if not message_data:
            raise HTTPException(status_code=400, detail="Mensagem inválida")
        
        # Extrai informações do usuário
        from_user = message_data.get("from", {})
        user_id = str(from_user.get("id", "unknown"))
        username = from_user.get("username") or from_user.get("first_name", "Usuário")
        message_text = message_data.get("text", "").strip()
        
        if not message_text:
            return {
                "success": True,
                "response": "Por favor, envie uma mensagem de texto.",
                "metadata": {
                    "user_id": user_id,
                    "username": username
                }
            }
        
        # Validação de segurança
        security_validation = input_validator.validate_message(
            user_id=user_id,
            message=message_text,
            content_type="text/plain"
        )
        
        if not security_validation.is_valid:
            if security_validation.level == ValidationLevel.REJECT:
                return {
                    "success": False,
                    "response": security_validation.message,
                    "metadata": {
                        "user_id": user_id,
                        "validation_error": True
                    }
                }
        
        # Usa conteúdo sanitizado
        sanitized_message = security_validation.sanitized_content or message_text
        
        # Verificar se está aguardando input de pedido inline (ANTES de processar comandos)
        from services.pedido_inline_service import pedido_inline_service
        aguardando = pedido_inline_service.get_awaiting(user_id)
        if aguardando and not message_text.startswith('/'):
            pedido = pedido_inline_service.init_pedido(user_id)
            panel_state = pedido_inline_service.get_panel_state(user_id)
            message_id = message_data.get("message_id")
            
            if aguardando == "nome":
                pedido["nome"] = sanitized_message
                pedido_inline_service.user_pedidos[user_id] = pedido
                pedido_inline_service.set_awaiting(user_id, None)
                
            elif aguardando == "endereco":
                pedido["endereco"] = sanitized_message
                pedido_inline_service.user_pedidos[user_id] = pedido
                pedido_inline_service.set_awaiting(user_id, None)
                
            elif aguardando == "data":
                pedido["data"] = sanitized_message
                pedido_inline_service.user_pedidos[user_id] = pedido
                pedido_inline_service.set_awaiting(user_id, None)
                
            elif aguardando == "outros":
                pedido["outros"] = sanitized_message
                pedido_inline_service.user_pedidos[user_id] = pedido
                pedido_inline_service.set_awaiting(user_id, None)
                
            elif aguardando == "set_qty":
                # Digitar quantidade do produto selecionado
                selected_key = pedido_inline_service.get_selected_key(user_id)
                if selected_key:
                    try:
                        nova_qtde = int(sanitized_message)
                        pedido_inline_service.set_quantidade(user_id, selected_key, nova_qtde)
                        pedido_inline_service.set_awaiting(user_id, None)
                    except ValueError:
                        return {
                            "success": True,
                            "response": "❌ Por favor, digite um número válido.",
                            "delete_user_message": True,
                            "user_message_id": message_id,
                            "metadata": {"user_id": user_id}
                        }
                else:
                    pedido_inline_service.set_awaiting(user_id, None)
            
            elif aguardando.startswith("qty_"):
                # Compatibilidade com sistema antigo
                produto_key = aguardando.replace("qty_", "")
                try:
                    nova_qtde = int(sanitized_message)
                    if nova_qtde < 0:
                        nova_qtde = 0
                    pedido["produtos"][produto_key] = nova_qtde
                    pedido_inline_service.user_pedidos[user_id] = pedido
                    pedido_inline_service.set_awaiting(user_id, None)
                except ValueError:
                    return {
                        "success": True,
                        "response": "❌ Por favor, digite um número válido.",
                        "delete_user_message": True,
                        "user_message_id": message_id,
                        "metadata": {"user_id": user_id}
                    }
            
            # Atualizar painel
            panel_state = pedido_inline_service.get_panel_state(user_id)
            texto = pedido_inline_service.render_text(pedido, panel_state)
            keyboard = pedido_inline_service.build_keyboard(pedido, panel_state)
            
            return {
                "success": True,
                "response": texto,
                "has_keyboard": True,
                "keyboard_type": "inline",
                "edit_message": True,
                "message_id": pedido_inline_service.get_panel_message_id(user_id),
                "reply_markup": keyboard,
                "parse_mode": "HTML",
                "delete_user_message": True,  # Flag para Telegram Service deletar mensagem do usuário
                "user_message_id": message_id,
                "metadata": {"user_id": user_id}
            }
        
        # Obter permissões do usuário
        user_permissions = permission_manager.get_user_permissions(
            PermissionLevel.BASIC
        )
        
        # Verificar se é um comando que começa com "/" (comando direto do Telegram)
        # Comandos do Telegram começam com "/" e devem ser processados antes de qualquer outra coisa
        if message_text.startswith('/'):
            logger.info(f"Comando direto detectado: {message_text}", user_id=user_id)
            
            # Verificar se é um comando conhecido diretamente (fallback rápido)
            command_text = message_text.lower().strip().lstrip('/').split()[0]  # Pega apenas o primeiro "palavra"
            if command_text in ['menu', 'm', 'início', 'inicio', 'home']:
                logger.info(f"Comando /menu detectado diretamente", user_id=user_id)
                # Criar análise direta para o comando menu
                command_analysis = CommandAnalysis(
                    is_command=True,
                    confidence=0.95,
                    command_id='show_menu',
                    parameters={},
                    original_message=message_text,
                    processed_message=message_text
                )
            elif command_text in ['pedidos', 'p']:
                logger.info(f"Comando /pedidos detectado diretamente", user_id=user_id)
                # Criar análise direta para o comando pedidos
                command_analysis = CommandAnalysis(
                    is_command=True,
                    confidence=0.95,
                    command_id='show_pedidos_menu',
                    parameters={},
                    original_message=message_text,
                    processed_message=message_text
                )
            else:
                # Analisar mensagem para detectar comandos
                command_analysis = await command_analyzer.analyze_message(
                    message_text,  # Usar mensagem original, não sanitizada, para preservar "/"
                    user_permissions
                )
        else:
            # Verificar se é um comando antes de processar no fluxo de produtos
            # Analisar mensagem para detectar comandos
            command_analysis = await command_analyzer.analyze_message(
                sanitized_message,
                user_permissions
            )
        
        # Se for um comando com boa confiança, executar comando
        # Para comandos que começam com "/", aceitar confiança menor (0.3)
        confidence_threshold = 0.3 if message_text.startswith('/') else 0.5
        
        if command_analysis.is_command and command_analysis.confidence >= confidence_threshold:
            logger.info(
                "Comando detectado no Telegram",
                user_id=user_id,
                command_id=command_analysis.command_id,
                confidence=command_analysis.confidence
            )
            
            # Criar requisição de comando
            command_request = CommandRequest(
                command_id=command_analysis.command_id,
                parameters=command_analysis.parameters or {},
                user_id=user_id
            )
            
            # Executar comando
            success, message, result, confirmation = await command_executor.execute_command(
                command_request,
                user_permissions
            )
            
            if success:
                if confirmation:
                    # Comando requer confirmação
                    return {
                        "success": True,
                        "response": confirmation.message,
                        "requires_confirmation": True,
                        "confirmation_id": confirmation.execution_id,
                        "metadata": {
                            "user_id": user_id,
                            "username": username,
                            "command_id": command_analysis.command_id,
                            "is_command": True
                        }
                    }
                else:
                    # Comando executado diretamente
                    response_message = result.message if result else message
                    response_data = {
                        "success": True,
                        "response": response_message,
                        "metadata": {
                            "user_id": user_id,
                            "username": username,
                            "command_id": command_analysis.command_id,
                            "is_command": True,
                            "command_result": result.data if result else None
                        }
                    }
                    
                    # Verifica se o comando retornou botões do Telegram
                    if result and result.data:
                        command_data = result.data
                        # Verificar se tem reply_markup ou telegram_keyboard
                        reply_markup = command_data.get("reply_markup") or command_data.get("telegram_keyboard")
                        
                        if command_data.get("target") == "telegram" and reply_markup:
                            # Formato correto para Telegram: reply_markup com inline_keyboard
                            response_data["reply_markup"] = reply_markup
                            # Flags explícitas para facilitar processamento no Telegram Service
                            response_data["has_keyboard"] = command_data.get("has_keyboard", True)
                            response_data["keyboard_type"] = command_data.get("keyboard_type", "inline")
                            # Também manter telegram_keyboard para compatibilidade
                            response_data["telegram_keyboard"] = reply_markup
                            logger.info(
                                "Botões do Telegram adicionados à resposta",
                                command_id=command_analysis.command_id,
                                buttons_count=len(reply_markup.get("inline_keyboard", [])),
                                keyboard_type=response_data.get("keyboard_type")
                            )
                    
                    return response_data
            else:
                # Erro na execução do comando
                return {
                    "success": False,
                    "response": message or "Erro ao executar comando",
                    "metadata": {
                        "user_id": user_id,
                        "username": username,
                        "command_id": command_analysis.command_id,
                        "is_command": True
                    }
                }
        
        # Se não for comando, processa no fluxo de produtos
        result = await product_flow.process_message(user_id, sanitized_message)
        
        logger.info(
            "Mensagem do Telegram processada",
            user_id=user_id,
            username=username,
            state=result["state"].value,
            completed=result["completed"]
        )
        
        return {
            "success": True,
            "response": result["response"],
            "metadata": {
                "user_id": user_id,
                "username": username,
                "state": result["state"].value,
                "completed": result["completed"],
                "product_id": result["product"].id if result["product"] else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar mensagem do Telegram: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )


async def _handle_callback_query(
    callback_query: Dict[str, Any],
    current_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Processa callback_query (clique em botão) do Telegram
    
    Args:
        callback_query: Dados do callback_query do Telegram
        current_user: Usuário autenticado do Keycloak
        
    Returns:
        Dict com resposta e botões se necessário
    """
    try:
        callback_id = callback_query.get("id")
        callback_data = callback_query.get("data", "")
        from_user = callback_query.get("from", {})
        user_id = str(from_user.get("id", "unknown"))
        username = from_user.get("username") or from_user.get("first_name", "Usuário")
        message = callback_query.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        
        logger.info(
            "Callback recebido",
            callback_id=callback_id,
            callback_data=callback_data,
            user_id=user_id,
            chat_id=chat_id
        )
        
        # Processar callback usando menu handler
        if callback_data.startswith("menu_"):
            # Callback de menu principal
            menu_response = await telegram_menu_handler.handle_callback(callback_data)
        elif (callback_data.startswith("pedido_") or 
              callback_data.startswith("prod:") or 
              callback_data.startswith("sel:") or 
              callback_data.startswith("action:") or
              callback_data == "noop"):
            # Callback específico de pedidos - passar user_id
            menu_response = await telegram_menu_handler.handle_pedido_callback(callback_data, user_id)
            
            # Tratar noop - apenas responder ao callback
            if menu_response.get("noop"):
                return {
                    "success": True,
                    "response": "",
                    "callback_query_id": callback_id,
                    "has_keyboard": False,
                    "metadata": {
                        "user_id": user_id,
                        "is_callback": True,
                        "noop": True
                    }
                }
            
            # Armazenar message_id do painel quando for criado ou editado
            from services.pedido_inline_service import pedido_inline_service
            chat_id = message.get("chat", {}).get("id")
            message_id = message.get("message_id")
            
            if chat_id and message_id:
                # Se for nova mensagem (pedido_novo) ou se já existe painel, atualizar
                if callback_data == "pedido_novo" or pedido_inline_service.get_panel_message_id(user_id):
                    pedido_inline_service.set_panel_message_id(user_id, message_id, chat_id)
        else:
            # Outros callbacks
            menu_response = await telegram_menu_handler.handle_callback(callback_data)
        
        # Preparar resposta
        response_data = {
            "success": True,
            "response": menu_response.get("response", ""),
            "callback_query_id": callback_id,  # Para responder ao callback
            "edit_message": True,  # Flag para editar mensagem ao invés de criar nova
            "message_id": message.get("message_id"),  # ID da mensagem a ser editada
            "metadata": {
                "user_id": user_id,
                "username": username,
                "callback_data": callback_data,
                "is_callback": True,
                "chat_id": chat_id
            }
        }
        
        # Adicionar botões se houver
        if menu_response.get("has_keyboard") and menu_response.get("reply_markup"):
            response_data["has_keyboard"] = menu_response["has_keyboard"]
            response_data["keyboard_type"] = menu_response.get("keyboard_type", "inline")
            response_data["reply_markup"] = menu_response["reply_markup"]
            # Flag para editar mensagem (sempre true para callbacks de menu)
            response_data["edit_message"] = menu_response.get("edit_message", True)
        
        logger.info(
            "Callback processado - mensagem será editada",
            callback_data=callback_data,
            message_id=response_data.get("message_id"),
            chat_id=chat_id
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"Erro ao processar callback_query: {e}", exc_info=True)
        return {
            "success": False,
            "response": f"Erro ao processar callback: {str(e)}",
            "callback_query_id": callback_query.get("id"),
            "metadata": {
                "is_callback": True,
                "error": str(e)
            }
        }
