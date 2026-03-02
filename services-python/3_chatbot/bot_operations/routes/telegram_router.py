"""
Router para integração com Telegram
"""

import structlog
import re
import uuid
import json
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel

from services.product_conversation_flow import product_flow
from services.security import input_validator, ValidationLevel, permission_manager, PermissionLevel
from services.commands.analyzer import CommandAnalyzer
from services.commands.executor import CommandExecutor
from services.commands.types import CommandRequest, CommandAnalysis
from services.telegram_menu_handler import telegram_menu_handler
from services.telegram_order_parser import telegram_order_parser
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


def extract_bearer_token(request: Request) -> Optional[str]:
    """Extrai token Bearer do header Authorization"""
    authorization = request.headers.get("Authorization", "")
    
    # Log para debug
    logger.debug(
        "Extraindo token do header Authorization",
        has_authorization_header=bool(authorization),
        authorization_preview=authorization[:30] + "..." if authorization else None,
        all_headers=list(request.headers.keys())
    )
    
    if not authorization:
        logger.warning("Header Authorization nao encontrado no request")
        return None
    
    if authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer "
        logger.debug(
            "Token extraido com sucesso",
            token_preview=token[:20] + "..." if token else None,
            token_length=len(token) if token else 0
        )
        return token
    
    logger.warning(
        "Header Authorization nao comeca com 'Bearer '",
        authorization_preview=authorization[:30]
    )
    return None


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


async def process_telegram_message(
    request: Request,
    x_telegram_bot_token: Optional[str] = None,
    current_user: Dict[str, Any] = None
):
    """
    Função para processar mensagens do Telegram
    Pode ser chamada diretamente ou via endpoint
    """
    # LOG IMEDIATO: Processando mensagem do Telegram
    logger.info(
        "📱 Processando mensagem do Telegram",
        method=request.method,
        url=str(request.url),
        path=request.url.path,
        has_telegram_token=bool(x_telegram_bot_token),
        has_authorization="authorization" in [k.lower() for k in request.headers.keys()],
        client_host=request.client.host if request.client else None
    )
    
    try:
        # Verifica autenticação do bot Telegram (se token fornecido)
        if x_telegram_bot_token:
            logger.info("🔐 Verificando token do bot Telegram", has_token=True)
            if not verify_telegram_token(request, x_telegram_bot_token):
                logger.warning("❌ Token do bot inválido", has_token=True)
                raise HTTPException(status_code=401, detail="Token do bot inválido")
            logger.info("✅ Token do bot verificado com sucesso")
        
        # Verificar autenticação do usuário (se fornecido)
        if current_user:
            logger.info(
                "👤 Usuário autenticado (Keycloak)",
                username=current_user.get('preferred_username'),
                user_id=current_user.get('sub'),
                email=current_user.get('email'),
                roles=current_user.get('realm_access', {}).get('roles', [])
            )
            
            # Verificar se o usuário tem role 'colaborador'
            if not check_colaborador_role(current_user):
                username = current_user.get('preferred_username', 'unknown')
                logger.warning(
                    "❌ Acesso negado: usuário sem role 'colaborador'",
                    username=username,
                    user_id=current_user.get('sub'),
                    user_roles=current_user.get('realm_access', {}).get('roles', [])
                )
                raise HTTPException(
                    status_code=403,
                    detail="Acesso negado: role 'colaborador' é necessário"
                )
            
            logger.info(
                "✅ Acesso autorizado: usuário com role 'colaborador'",
                username=current_user.get('preferred_username'),
                user_id=current_user.get('sub')
            )
        
        # Extrai dados do Telegram
        body = await request.json()
        
        # LOG DETALHADO: Mensagem recebida do Telegram Service
        logger.info("=" * 70)
        logger.info("MENSAGEM RECEBIDA DO TELEGRAM SERVICE")
        logger.info("=" * 70)
        
        # Log do body completo
        try:
            body_json = json.dumps(body, indent=2, ensure_ascii=False, default=str)
            logger.info("BODY COMPLETO RECEBIDO DO TELEGRAM SERVICE:")
            logger.info(body_json)
        except Exception as e:
            logger.warning(f"Nao foi possivel serializar body JSON: {e}")
            logger.info("Body como string:", body_str=str(body)[:1000])
        
        logger.info(
            "Resumo do body",
            body_keys=list(body.keys()),
            has_callback_query="callback_query" in body,
            has_message="message" in body,
            has_edited_message="edited_message" in body,
            has_channel_post="channel_post" in body,
            update_id=body.get("update_id"),
            user_id=current_user.get('sub') if current_user else None,
            username=current_user.get('preferred_username') if current_user else None
        )
        
        # Verificar se é um callback_query (clique em botão)
        callback_query = body.get("callback_query")
        if callback_query:
            logger.info(
                "🔄 Processando callback_query",
                callback_data=callback_query.get("data"),
                callback_id=callback_query.get("id")
            )
            return await _handle_callback_query(callback_query, current_user, request=request)
        
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
            logger.warning("❌ Mensagem inválida: sem campo 'message' no body")
            raise HTTPException(status_code=400, detail="Mensagem inválida")
        
        # LOG DETALHADO: Mensagem recebida
        logger.info("=" * 70)
        logger.info("MENSAGEM DE TEXTO RECEBIDA")
        logger.info("=" * 70)
        
        try:
            message_json = json.dumps(message_data, indent=2, ensure_ascii=False, default=str)
            logger.info("MESSAGE_DATA COMPLETO:")
            logger.info(message_json)
        except Exception as e:
            logger.warning(f"Nao foi possivel serializar message_data JSON: {e}")
        
        # Extrai informações do usuário
        from_user = message_data.get("from", {})
        user_id = str(from_user.get("id", "unknown"))
        username = from_user.get("username") or from_user.get("first_name", "Usuário")
        message_text = message_data.get("text", "").strip()
        
        logger.info(
            "Detalhes da mensagem",
            user_id=user_id,
            username=username,
            from_user=from_user,
            message_id=message_data.get("message_id"),
            chat_id=message_data.get("chat", {}).get("id"),
            chat=message_data.get("chat", {}),
            date=message_data.get("date"),
            message_length=len(message_text),
            message_preview=message_text[:100] if message_text else "(vazia)",
            message_full=message_text
        )
        
        if not message_text:
            logger.warning("⚠️ Mensagem vazia recebida", user_id=user_id, username=username)
            return {
                "success": True,
                "response": "Por favor, envie uma mensagem de texto.",
                "metadata": {
                    "user_id": user_id,
                    "username": username
                }
            }
        
        # LOG: Iniciando validação de segurança
        logger.info("🔒 Iniciando validação de segurança", user_id=user_id, message_length=len(message_text))
        
        # Validação de segurança
        security_validation = input_validator.validate_message(
            user_id=user_id,
            message=message_text,
            content_type="text/plain"
        )
        
        # LOG: Resultado da validação
        logger.info(
            "🔒 Validação de segurança concluída",
            user_id=user_id,
            is_valid=security_validation.is_valid,
            validation_level=security_validation.level.value if hasattr(security_validation.level, 'value') else str(security_validation.level),
            original_length=len(message_text),
            sanitized_length=len(security_validation.sanitized_content) if security_validation.sanitized_content else 0
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
        
        # LOG: Mensagem sanitizada
        logger.info(
            "🧹 Mensagem sanitizada",
            user_id=user_id,
            original=message_text[:100],
            sanitized=sanitized_message[:100] if sanitized_message else "(vazia)",
            was_sanitized=(security_validation.sanitized_content != message_text)
        )
        
        # Ignorar palavras que são apenas callbacks de botões (não devem ser processadas como comandos)
        # Isso evita que "sair", "voltar", etc. sejam interpretados como comandos quando o usuário
        # apenas clicou no botão e o Telegram enviou como mensagem de texto
        ignored_words = ["sair", "voltar", "cancelar", "fechar"]
        if sanitized_message.lower().strip() in ignored_words:
            logger.info("🚫 Ignorando palavra de callback", word=sanitized_message, user_id=user_id)
            logger.info(
                "Ignorando palavra que é apenas callback de botão",
                word=sanitized_message,
                user_id=user_id
            )
            return {
                "success": True,
                "response": "",  # Resposta vazia - não exibir nada
                "metadata": {
                    "user_id": user_id,
                    "username": username,
                    "ignored_callback_word": True
                }
            }
        
        # Verificar se a mensagem parece ser um pedido (contém padrão de pedido)
        # Padrão: "Nome: quantidade produto" ou "Nome quantidade produto"
        # Aceita com ou sem espaços: "Dona Dilma:08 Couve04 Coentros" ou "Dona Dilma: 08 Couve 04 Coentros"
        # Exemplo: "Dona Dilma:08 Couve04 Coentros04 Cebolinhas01 palito alface roxa"
        is_order_pattern = (
            # Padrão com dois pontos seguido de número (com ou sem espaço)
            re.search(r':\s*\d+[A-Za-zÀ-ÿ]', sanitized_message, re.IGNORECASE) or
            # Padrão: número seguido de letra (com ou sem espaço)
            re.search(r'\d+\s*[A-Za-zÀ-ÿ]', sanitized_message, re.IGNORECASE) or
            # Padrão: letra seguida de número seguido de letra (com ou sem espaços)
            re.search(r'[A-Za-zÀ-ÿ]+\s*\d+\s*[A-Za-zÀ-ÿ]', sanitized_message, re.IGNORECASE)
        )
        
        # LOG: Verificação de padrão de pedido
        logger.info(
            "🔍 Verificando padrão de pedido",
            user_id=user_id,
            is_order_pattern=bool(is_order_pattern),
            starts_with_slash=sanitized_message.startswith('/'),
            message_preview=sanitized_message[:100]
        )
        
        if is_order_pattern and not sanitized_message.startswith('/'):
            # Tentar processar como pedido
            logger.info("📦 Tentando processar mensagem como pedido", user_id=user_id, message=sanitized_message)
            
            try:
                # Extrair token do header Authorization
                token = extract_bearer_token(request)
                
                logger.info(
                    "Token extraido do request",
                    user_id=user_id,
                    has_token=bool(token),
                    token_preview=token[:20] + "..." if token else None,
                    authorization_header=request.headers.get("Authorization", "N/A")[:30] if request.headers.get("Authorization") else "N/A"
                )
                
                # Parsear pedidos do texto
                logger.info("🔍 Parseando pedidos do texto", user_id=user_id, text_length=len(sanitized_message))
                orders = telegram_order_parser.parse_order_text(sanitized_message)
                
                logger.info(
                    "📋 Pedidos parseados",
                    user_id=user_id,
                    orders_count=len(orders) if orders else 0,
                    orders_details=[{
                        "contact_name": o.get("contact_name"),
                        "items_count": len(o.get("items", []))
                    } for o in (orders or [])]
                )
                
                if orders:
                    # Processar pedidos (buscar produtos e enviar para e-commerce)
                    # Gerar UUID válido para conversation_id (não usar string)
                    conversation_id = str(uuid.uuid4())
                    
                    logger.info(
                        "Iniciando processamento de pedidos",
                        user_id=user_id,
                        orders_count=len(orders),
                        conversation_id=conversation_id,
                        has_token=bool(token),
                        token_preview=token[:20] + "..." if token else None,
                        message_id=message_data.get('message_id')
                    )
                    
                    success, message, created_orders = await telegram_order_parser.process_orders(
                        orders,
                        conversation_id=conversation_id,
                        token=token
                    )
                    
                    logger.info(
                        "Pedidos processados - RESULTADO",
                        user_id=user_id,
                        success=success,
                        orders_count=len(orders),
                        created_count=len(created_orders) if created_orders else 0,
                        message=message,
                        has_created_orders=bool(created_orders)
                    )
                    
                    if not success:
                        logger.error(
                            "FALHA ao processar pedidos",
                            user_id=user_id,
                            error_message=message,
                            orders_count=len(orders)
                        )
                    
                    return {
                        "success": success,
                        "response": message,
                        "metadata": {
                            "user_id": user_id,
                            "username": username,
                            "is_order": True,
                            "orders_count": len(orders),
                            "created_orders": created_orders
                        }
                    }
                else:
                    logger.info("Mensagem não contém pedidos válidos", user_id=user_id)
                    # Continuar processamento normal
            except Exception as e:
                logger.error(f"Erro ao processar pedido: {e}", exc_info=True, user_id=user_id)
                # Em caso de erro, continuar processamento normal (não bloquear)
                pass
        
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
        
        logger.info(
            "🔐 Permissões do usuário obtidas",
            user_id=user_id,
            permissions_count=len(user_permissions),
            permissions=user_permissions
        )
        
        # Verificar se é um comando que começa com "/" (comando direto do Telegram)
        # Comandos do Telegram começam com "/" e devem ser processados antes de qualquer outra coisa
        if message_text.startswith('/'):
            logger.info("⚡ Comando direto detectado (começa com /)", user_id=user_id, command=message_text)
            
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
            logger.info("🔍 Analisando mensagem para detectar comandos", user_id=user_id, message_preview=sanitized_message[:50])
            command_analysis = await command_analyzer.analyze_message(
                sanitized_message,
                user_permissions
            )
            
            logger.info(
                "🔍 Análise de comando concluída",
                user_id=user_id,
                is_command=command_analysis.is_command,
                command_id=command_analysis.command_id,
                confidence=command_analysis.confidence,
                parameters=command_analysis.parameters
            )
        
        # Ignorar se o comando detectado for relacionado a "sair" ou "menu sair"
        # Isso evita que palavras de callback sejam interpretadas como comandos
        if command_analysis.is_command:
            command_id = command_analysis.command_id or ""
            # Se o comando detectado for show_menu e a mensagem for apenas "sair", ignorar
            if command_id == "show_menu" and sanitized_message.lower().strip() in ["sair", "menu sair"]:
                logger.info(
                    "Ignorando comando show_menu para palavra 'sair' (é apenas callback)",
                    user_id=user_id
                )
                return {
                    "success": True,
                    "response": "",  # Resposta vazia - não exibir nada
                    "metadata": {
                        "user_id": user_id,
                        "username": username,
                        "ignored_callback_word": True
                    }
                }
        
        # Se for um comando com boa confiança, executar comando
        # Para comandos que começam com "/", aceitar confiança menor (0.3)
        confidence_threshold = 0.3 if message_text.startswith('/') else 0.5
        
        logger.info(
            "⚖️ Verificando se deve executar comando",
            user_id=user_id,
            is_command=command_analysis.is_command,
            confidence=command_analysis.confidence,
            threshold=confidence_threshold,
            will_execute=(command_analysis.is_command and command_analysis.confidence >= confidence_threshold)
        )
        
        if command_analysis.is_command and command_analysis.confidence >= confidence_threshold:
            logger.info(
                "✅ Comando detectado no Telegram - executando",
                user_id=user_id,
                command_id=command_analysis.command_id,
                confidence=command_analysis.confidence,
                parameters=command_analysis.parameters
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
        logger.info("🔄 Processando mensagem no fluxo de produtos", user_id=user_id, message_preview=sanitized_message[:50])
        result = await product_flow.process_message(user_id, sanitized_message)
        
        logger.info(
            "✅ Mensagem do Telegram processada no fluxo de produtos",
            user_id=user_id,
            username=username,
            state=result.get("state", {}).value if hasattr(result.get("state"), 'value') else str(result.get("state")),
            completed=result.get("completed", False),
            has_product=bool(result.get("product"))
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
    current_user: Dict[str, Any],
    request: Optional[Request] = None
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
        
        logger.info("=" * 70)
        logger.info("PROCESSANDO CALLBACK_QUERY")
        logger.info("=" * 70)
        logger.info(
            "Detalhes do callback",
            callback_id=callback_id,
            callback_data=callback_data,
            user_id=user_id,
            username=username,
            from_user=from_user,
            chat_id=chat_id,
            message=message,
            chat_instance=callback_query.get("chat_instance"),
            inline_message_id=callback_query.get("inline_message_id")
        )
        
        # Processar callback usando menu handler
        if callback_data.startswith("menu_"):
            # Callback de menu principal
            menu_response = await telegram_menu_handler.handle_callback(callback_data)
            
            # Verificar se deve excluir mensagem IMEDIATAMENTE após processar callback de menu
            # Esta verificação DEVE ser feita ANTES de qualquer outra lógica
            if menu_response.get("delete_message") or callback_data == "menu_sair":
                logger.info(
                    "Excluindo mensagem do menu (callback menu_)",
                    callback_data=callback_data,
                    message_id=message.get("message_id"),
                    chat_id=chat_id,
                    delete_message_flag=menu_response.get("delete_message")
                )
                # RETORNAR IMEDIATAMENTE - não continuar processamento
                return {
                    "success": True,
                    "response": "",  # Resposta vazia para não exibir nada
                    "callback_query_id": callback_id,
                    "delete_message": True,
                    "message_id": message.get("message_id"),
                    "chat_id": chat_id,
                    "has_keyboard": False,
                    "metadata": {
                        "user_id": user_id,
                        "username": username,
                        "callback_data": callback_data,
                        "is_callback": True,
                        "chat_id": chat_id
                    }
                }
        elif (callback_data.startswith("pedido_") or 
              callback_data.startswith("prod:") or 
              callback_data.startswith("sel:") or 
              callback_data.startswith("action:") or
              callback_data == "noop"):
            # Callback específico de pedidos - passar user_id e token
            # Extrair token do request se disponível
            token = extract_bearer_token(request) if request else None
            logger.info(
                "Processando callback de pedido",
                callback_data=callback_data,
                user_id=user_id,
                has_token=bool(token),
                token_preview=token[:20] + "..." if token else None
            )
            menu_response = await telegram_menu_handler.handle_pedido_callback(callback_data, user_id, token=token)
            
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
            
            # Verificar se deve excluir mensagem (para action:close)
            if menu_response.get("delete_message"):
                logger.info(
                    "Excluindo mensagem do pedido",
                    callback_data=callback_data,
                    message_id=message.get("message_id"),
                    chat_id=chat_id
                )
                return {
                    "success": True,
                    "response": "",
                    "callback_query_id": callback_id,
                    "delete_message": True,
                    "message_id": message.get("message_id"),
                    "chat_id": chat_id,
                    "has_keyboard": False,
                    "metadata": {
                        "user_id": user_id,
                        "username": username,
                        "callback_data": callback_data,
                        "is_callback": True,
                        "chat_id": chat_id
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
            
            # Verificar se deve excluir mensagem
            if menu_response.get("delete_message"):
                logger.info(
                    "Excluindo mensagem (outros callbacks)",
                    callback_data=callback_data,
                    message_id=message.get("message_id"),
                    chat_id=chat_id
                )
                return {
                    "success": True,
                    "response": "",
                    "callback_query_id": callback_id,
                    "delete_message": True,
                    "message_id": message.get("message_id"),
                    "chat_id": chat_id,
                    "has_keyboard": False,
                    "metadata": {
                        "user_id": user_id,
                        "username": username,
                        "callback_data": callback_data,
                        "is_callback": True,
                        "chat_id": chat_id
                    }
                }
        
        # Se a resposta estiver vazia e não tiver delete_message, pode ser um caso especial
        # Verificar se é callback de "sair" e não exibir nada
        if not menu_response.get("response") and callback_data == "menu_sair":
            logger.info("Callback 'menu_sair' - retornando resposta vazia para exclusão")
            return {
                "success": True,
                "response": "",  # Resposta vazia
                "callback_query_id": callback_id,
                "delete_message": True,
                "message_id": message.get("message_id"),
                "chat_id": chat_id,
                "has_keyboard": False,
                "metadata": {
                    "user_id": user_id,
                    "username": username,
                    "callback_data": callback_data,
                    "is_callback": True,
                    "chat_id": chat_id
                }
            }
        
        # Verificar se a resposta contém mensagem de erro relacionada a "sair"
        # Se sim, não exibir e tentar excluir a mensagem
        # Esta verificação DEVE ser feita ANTES de preparar qualquer resposta
        response_text = menu_response.get("response", "") or ""
        if callback_data == "menu_sair" or ("sair" in response_text.lower() and ("não encontrado" in response_text.lower() or "nao encontrado" in response_text.lower())):
            logger.warning(
                "Mensagem de erro detectada para 'sair' - ignorando e excluindo mensagem",
                callback_data=callback_data,
                response_text=response_text,
                delete_message_flag=menu_response.get("delete_message")
            )
            # RETORNAR IMEDIATAMENTE - não continuar processamento
            return {
                "success": True,
                "response": "",  # Resposta vazia - não exibir erro
                "callback_query_id": callback_id,
                "delete_message": True,
                "message_id": message.get("message_id"),
                "chat_id": chat_id,
                "has_keyboard": False,
                "metadata": {
                    "user_id": user_id,
                    "username": username,
                    "callback_data": callback_data,
                    "is_callback": True,
                    "chat_id": chat_id
                }
            }
        
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
