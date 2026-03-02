"""
Serviço para interagir com a API do Telegram
"""

import httpx
import structlog
import asyncio
from typing import Optional, Dict, Any
from config import settings
from services.chatbot_client import ChatbotClient
from services.auth_service import telegram_auth_service
from services.keycloak_auth_service import keycloak_auth_service

logger = structlog.get_logger(__name__)


class TelegramService:
    """Serviço para comunicação com Telegram Bot API"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        if not self.bot_token or self.bot_token == "your_telegram_bot_token_here":
            logger.error("TELEGRAM_BOT_TOKEN não configurado! Configure no arquivo .env")
            raise ValueError("TELEGRAM_BOT_TOKEN não configurado. Configure no arquivo .env")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.client: Optional[httpx.AsyncClient] = None
        self.chatbot_client = ChatbotClient()
        # Controle de atualizações processadas para evitar duplicação
        self._processed_updates: set = set()
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtém ou cria cliente HTTP"""
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
            )
        return self.client
    
    async def close(self):
        """Fecha cliente HTTP"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def process_update(self, update_data: Dict[str, Any]):
        """
        Processa uma atualização recebida do Telegram
        
        Args:
            update_data: Dados da atualização do Telegram
        """
        import sys
        update_id = update_data.get('update_id')
        print("=" * 80, file=sys.stderr)
        print(f"PROCESS_UPDATE CHAMADO - update_id={update_id}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        
        logger.info("PROCESS_UPDATE CHAMADO - Iniciando processamento", update_id=update_id)
        
        # FLAG DE SEGURANÇA: Garantir que não processe duas vezes
        processed_updates = getattr(self, '_processed_updates', set())
        if update_id in processed_updates:
            print(f"ATUALIZACAO {update_id} JA FOI PROCESSADA - IGNORANDO", file=sys.stderr)
            logger.warning(f"Atualização {update_id} já foi processada - ignorando")
            return
        
        # Marcar como processando
        processed_updates.add(update_id)
        self._processed_updates = processed_updates
        
        try:
            # Verificar se é uma mensagem
            message = update_data.get("message")
            if not message:
                # Pode ser edited_message ou callback_query
                message = update_data.get("edited_message")
                if not message:
                    callback_query = update_data.get("callback_query")
                    if callback_query:
                        await self._process_callback_query(callback_query)
                    return
            
            # Extrair informações da mensagem PRIMEIRO
            chat_id = message.get("chat", {}).get("id")
            user_id = str(message.get("from", {}).get("id", ""))
            username = message.get("from", {}).get("username", "")
            text = message.get("text", "")
            message_id = message.get("message_id")
            
            print("=" * 80, file=sys.stderr)
            print(f"MENSAGEM EXTRAIDA - user_id={user_id}, chat_id={chat_id}, text={text[:50]}", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            
            if not text:
                # Pode ser foto, documento, etc. Por enquanto, ignoramos
                logger.info("Mensagem sem texto recebida", chat_id=chat_id, message_type=message.get("content_type"))
                return
            
            # ========== TRATAMENTO DE COMANDOS ESPECIAIS (ANTES DA VERIFICAÇÃO DE AUTENTICAÇÃO) ==========
            # Comandos que não precisam de autenticação ou têm tratamento especial
            text_lower = text.strip().lower()
            
            # Comando /logout - fazer logout e limpar sessão
            if text_lower == "/logout":
                print("=" * 80, file=sys.stderr)
                print(f"COMANDO /logout RECEBIDO - user_id={user_id}", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                logger.info("Comando /logout recebido", telegram_user_id=user_id)
                
                try:
                    # Fazer logout no Keycloak e limpar tokens locais
                    logout_result = await keycloak_auth_service.logout(user_id)
                    
                    if logout_result:
                        logout_message = "✅ Logout realizado com sucesso!\n\nVocê foi desconectado. Para usar o bot novamente, envie qualquer mensagem para fazer login."
                    else:
                        # Mesmo se não houver tokens, limpar qualquer estado residual
                        keycloak_auth_service.clear_user_session(user_id)
                        logout_message = "✅ Sessão limpa com sucesso!\n\nVocê não estava autenticado, mas qualquer estado residual foi limpo."
                    
                    await self.send_message(chat_id=chat_id, text=logout_message)
                    logger.info("Logout realizado", telegram_user_id=user_id, success=logout_result)
                    
                except Exception as e:
                    logger.error(f"Erro ao fazer logout: {e}", exc_info=True)
                    # Limpar sessão local mesmo em caso de erro
                    keycloak_auth_service.clear_user_session(user_id)
                    await self.send_message(
                        chat_id=chat_id,
                        text="✅ Sessão local limpa.\n\nHouve um erro ao fazer logout no servidor, mas sua sessão local foi limpa."
                    )
                
                # Retornar após processar logout (não continuar para chatbot)
                return
            
            # ========== VERIFICAÇÃO DE AUTENTICAÇÃO ==========
            # SEMPRE verificar autenticação e enviar link de login se não autenticado
            # SEMPRE bloquear processamento com chatbot se não autenticado (não depende de REQUIRE_AUTH)
            auth_status = None
            is_authenticated = False
            
            try:
                auth_status = keycloak_auth_service.get_user_auth_status(user_id)
                is_authenticated = auth_status and auth_status.get("is_authenticated", False)
                
                logger.info(
                    "Status de autenticação verificado",
                    telegram_user_id=user_id,
                    is_authenticated=is_authenticated,
                    require_auth=settings.REQUIRE_AUTH
                )
                
                # Se usuário não estiver autenticado, SEMPRE enviar link de login
                if not auth_status or not is_authenticated or not auth_status.get("is_authenticated", False):
                    print("=" * 80, file=sys.stderr)
                    print(f"USUARIO NAO AUTENTICADO - user_id={user_id}", file=sys.stderr)
                    print(f"REQUIRE_AUTH={settings.REQUIRE_AUTH}", file=sys.stderr)
                    print("=" * 80, file=sys.stderr)
                    
                    logger.warning("USUARIO NAO AUTENTICADO - Enviando link de login", telegram_user_id=user_id, auth_status=auth_status)
                    
                    auth_url, state = keycloak_auth_service.generate_authorization_url(
                        telegram_user_id=user_id,
                        telegram_chat_id=str(chat_id)
                    )
                    
                    auth_message = (
                        "🔐 Você precisa estar autenticado para usar este bot.\n\n"
                        "Por favor, <a href=\"{}\">clique aqui para fazer login</a>.\n\n"
                        "Após fazer login, você será redirecionado de volta para o Telegram."
                    ).format(auth_url)
                    
                    await self.send_message(chat_id=chat_id, text=auth_message, parse_mode="HTML")
                    logger.info("Mensagem de autenticacao enviada - RETORNANDO SEM PROCESSAR COM CHATBOT", telegram_user_id=user_id)
                    return  # SEMPRE bloquear processamento com chatbot se não autenticado
                    
            except Exception as e:
                logger.error(
                    "Erro ao verificar autenticação",
                    telegram_user_id=user_id,
                    error=str(e),
                    exc_info=True
                )
                # Em caso de erro, tentar enviar link de login
                try:
                    auth_url, state = keycloak_auth_service.generate_authorization_url(
                        telegram_user_id=user_id,
                        telegram_chat_id=str(chat_id)
                    )
                    auth_message = (
                        "🔐 Você precisa estar autenticado para usar este bot.\n\n"
                        "Por favor, <a href=\"{}\">clique aqui para fazer login</a>.\n\n"
                        "Após fazer login, você será redirecionado de volta para o Telegram."
                    ).format(auth_url)
                    await self.send_message(chat_id=chat_id, text=auth_message, parse_mode="HTML")
                    logger.info("Mensagem de autenticacao enviada apos erro na verificacao - RETORNANDO SEM PROCESSAR", telegram_user_id=user_id)
                except Exception as e2:
                    logger.error("Erro ao enviar mensagem de autenticação", error=str(e2))
                
                # SEMPRE bloquear processamento com chatbot se não autenticado
                return
            
            # ========== PROCESSAR MENSAGEM COM CHATBOT ==========
            # Só chega aqui se o usuário estiver autenticado
            # Se autenticado, usar token para processar com chatbot
            print("=" * 80, file=sys.stderr)
            if is_authenticated:
                print(f"USUARIO AUTENTICADO - Processando com chatbot (com token) - user_id={user_id}", file=sys.stderr)
                logger.info("USUARIO AUTENTICADO - Processando mensagem com chatbot", telegram_user_id=user_id)
            else:
                print(f"USUARIO NAO AUTENTICADO - Processando com chatbot (sem token) - user_id={user_id}", file=sys.stderr)
                logger.info("USUARIO NAO AUTENTICADO - Processando mensagem sem autenticação", telegram_user_id=user_id)
            print("=" * 80, file=sys.stderr)
            
            # Enviar indicador de digitação
            await self.send_chat_action(chat_id=chat_id, action="typing")
            
            # Obter token e userinfo se autenticado
            access_token = None
            userinfo = {}
            if is_authenticated and auth_status:
                access_token = keycloak_auth_service.get_access_token(user_id)
                userinfo = auth_status.get("userinfo", {})
                logger.info(
                    "Informações do usuário autenticado",
                    telegram_user_id=user_id,
                    preferred_username=userinfo.get("preferred_username"),
                    keycloak_user_id=userinfo.get("sub")
                )
            
            # Processar mensagem com o chatbot
            chatbot_response = await self._process_message_with_chatbot(
                user_id=user_id,
                username=username,
                message=text,
                chat_id=chat_id,
                access_token=access_token,
                userinfo=userinfo,
                telegram_message=message,
                update_id=update_id
            )
            
            # Enviar resposta para o Telegram
            # IMPORTANTE: Verificar delete_message ANTES de qualquer outra ação
            delete_message = chatbot_response.get("delete_message", False) if chatbot_response else False
            message_id_to_delete = chatbot_response.get("message_id") if chatbot_response else None
            chat_id_to_delete = chatbot_response.get("chat_id") if chatbot_response else None
            
            # Usar chat_id do chatbot_response se disponível, caso contrário usar do message
            chat_id_to_delete = chat_id_to_delete or chat_id
            
            logger.info(
                "Verificando delete_message (mensagem)",
                delete_message=delete_message,
                message_id_to_delete=message_id_to_delete,
                chat_id_to_delete=chat_id_to_delete,
                has_text=bool(chatbot_response.get("text") if chatbot_response else False),
                text_preview=chatbot_response.get("text", "")[:50] if chatbot_response and chatbot_response.get("text") else "",
                edit_message=chatbot_response.get("edit_message", False) if chatbot_response else False
            )
            
            if delete_message and message_id_to_delete and chat_id_to_delete:
                # Deletar mensagem do bot (NÃO editar nem enviar nova)
                try:
                    await self.delete_message(chat_id=chat_id_to_delete, message_id=message_id_to_delete)
                    logger.info(
                        "Mensagem do bot deletada",
                        chat_id=chat_id_to_delete,
                        message_id=message_id_to_delete
                    )
                except Exception as e:
                    logger.warning(
                        "Erro ao deletar mensagem do bot",
                        chat_id=chat_id_to_delete,
                        message_id=message_id_to_delete,
                        error=str(e)
                    )
                # Retornar após deletar (não processar mais nada)
                return
            
            if chatbot_response and chatbot_response.get("text"):
                text_response = chatbot_response.get("text")
                reply_markup = chatbot_response.get("reply_markup")
                parse_mode = chatbot_response.get("parse_mode")
                edit_message = chatbot_response.get("edit_message", False)
                message_id_to_edit = chatbot_response.get("message_id")
                delete_user_message = chatbot_response.get("delete_user_message", False)
                
                # Verificar se deve editar mensagem existente (mantém chat limpo)
                if edit_message and message_id_to_edit:
                    # Editar mensagem existente
                    try:
                        await self.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id_to_edit,
                            text=text_response,
                            parse_mode=parse_mode,
                            reply_markup=reply_markup
                        )
                    except ValueError as e:
                        error_str = str(e)
                        # Verificar tipo de erro
                        if "not_modified:" in error_str:
                            # Mensagem já tem o mesmo conteúdo - não fazer nada (não criar nova mensagem)
                            logger.info(
                                "Mensagem já tem o mesmo conteúdo - não precisa editar (texto)",
                                chat_id=chat_id,
                                message_id=message_id_to_edit
                            )
                            # Não fazer nada - mensagem já está correta
                        elif "too_old:" in error_str:
                            # Mensagem muito antiga (>48h) - deletar antiga e enviar nova
                            logger.warning(
                                "Mensagem muito antiga - deletando e enviando nova (texto)",
                                chat_id=chat_id,
                                message_id=message_id_to_edit
                            )
                            # Tentar deletar mensagem antiga
                            try:
                                await self.delete_message(chat_id=chat_id, message_id=message_id_to_edit)
                                logger.info("Mensagem antiga deletada com sucesso", chat_id=chat_id, message_id=message_id_to_edit)
                            except Exception as delete_error:
                                logger.warning(
                                    "Não foi possível deletar mensagem antiga",
                                    chat_id=chat_id,
                                    message_id=message_id_to_edit,
                                    error=str(delete_error)
                                )
                            # Enviar nova mensagem
                            telegram_result = await self.send_message(
                                chat_id=chat_id,
                                text=text_response,
                                parse_mode=parse_mode,
                                reply_markup=reply_markup
                            )
                            logger.info(
                                "Nova mensagem enviada (mensagem antiga deletada)",
                                chat_id=chat_id,
                                new_message_id=telegram_result.get("result", {}).get("message_id") if telegram_result.get("ok") else None
                            )
                        else:
                            # Outro tipo de erro - tentar enviar nova mensagem (mas não deletar)
                            logger.warning(
                                "Erro ao editar mensagem - enviando nova mensagem (texto)",
                                chat_id=chat_id,
                                message_id=message_id_to_edit,
                                error=error_str
                            )
                            telegram_result = await self.send_message(
                                chat_id=chat_id,
                                text=text_response,
                                parse_mode=parse_mode,
                                reply_markup=reply_markup
                            )
                            logger.info(
                                "Nova mensagem enviada (fallback)",
                                chat_id=chat_id,
                                new_message_id=telegram_result.get("result", {}).get("message_id") if telegram_result.get("ok") else None
                            )
                else:
                    # Enviar nova mensagem
                    telegram_result = await self.send_message(
                        chat_id=chat_id,
                        text=text_response,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup
                    )
                    
                    # Capturar message_id da nova mensagem criada
                    if telegram_result.get("ok") and telegram_result.get("result", {}).get("message_id"):
                        new_message_id = telegram_result["result"]["message_id"]
                        logger.info(
                            "Nova mensagem criada",
                            chat_id=chat_id,
                            message_id=new_message_id
                        )
                
                # Deletar mensagem do usuário se solicitado
                if delete_user_message and message_id:
                    try:
                        await self.delete_message(chat_id=chat_id, message_id=message_id)
                        logger.info(
                            "Mensagem do usuário deletada",
                            chat_id=chat_id,
                            message_id=message_id
                        )
                    except Exception as e:
                        logger.warning(
                            "Erro ao deletar mensagem do usuário",
                            chat_id=chat_id,
                            message_id=message_id,
                            error=str(e)
                        )
            else:
                # Se não houve resposta, enviar mensagem de erro padrão
                error_msg = "Desculpe, não consegui processar sua mensagem. Tente novamente."
                await self.send_message(
                    chat_id=chat_id,
                    text=error_msg
                )
                
        except Exception as e:
            import sys
            print("=" * 80, file=sys.stderr)
            print(f"EXCEÇÃO CAPTURADA NO PROCESS_UPDATE: {e}", file=sys.stderr)
            print(f"Tipo: {type(e).__name__}", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            logger.error(f"❌ ERRO AO PROCESSAR ATUALIZAÇÃO: {e}", exc_info=True)
            logger.error(f"Tipo de erro: {type(e).__name__}", exc_info=True)
            # IMPORTANTE: Em caso de erro, NÃO processar com chatbot
            # Apenas enviar mensagem de erro se possível
            try:
                chat_id = update_data.get("message", {}).get("chat", {}).get("id")
                if not chat_id:
                    chat_id = update_data.get("edited_message", {}).get("chat", {}).get("id")
                if chat_id:
                    await self.send_message(
                        chat_id=chat_id,
                        text="❌ Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
                    )
            except Exception as e2:
                logger.error(f"Erro ao enviar mensagem de erro: {e2}")
            # NÃO CONTINUAR - RETORNAR IMEDIATAMENTE
            return
    
    async def _process_callback_query(self, callback_query: Dict[str, Any]):
        """Processa callback query (botões inline)"""
        import sys
        try:
            query_id = callback_query.get("id")
            chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
            data = callback_query.get("data")
            user_id = str(callback_query.get("from", {}).get("id", ""))
            
            message_id = callback_query.get("message", {}).get("message_id")
            username = callback_query.get("from", {}).get("username", "")
            
            logger.info(
                "Callback query recebido",
                query_id=query_id,
                data=data,
                chat_id=chat_id,
                message_id=message_id
            )
            
            # Verificar autenticação (mas NÃO bloquear - deixar chatbot retornar erro 401)
            # Quando chatbot retornar erro 401, vamos editar a mensagem do pedido com link de login
            auth_status = keycloak_auth_service.get_user_auth_status(user_id)
            is_authenticated = auth_status and auth_status.get("is_authenticated", False)
            
            # Obter token e userinfo se autenticado (pode ser None se não autenticado)
            access_token = keycloak_auth_service.get_access_token(user_id) if is_authenticated else None
            userinfo = auth_status.get("userinfo") if is_authenticated else None
            
            logger.info(
                "Processando callback (autenticação verificada mas não bloqueando)",
                telegram_user_id=user_id,
                is_authenticated=is_authenticated,
                has_token=bool(access_token)
            )
            
            # ✅ INTERCEPTAR AÇÃO "SAIR" ANTES DO LOOKUP DE MENUS
            # "sair" não é menu, é ação - tratar aqui para evitar erro "Menu 'sair' não encontrado"
            callback_data_lower = (data or "").strip().lower()
            is_exit_action = callback_data_lower in (
                "sair", 
                "action:sair", 
                "exit", 
                "menu_sair",
                "action:exit",
                "close",
                "action:close"
            )
            
            if is_exit_action:
                logger.info(
                    "Ação 'sair' detectada - fechando menu",
                    callback_data=data,
                    chat_id=chat_id,
                    message_id=message_id
                )
                
                # Responder ao callback (obrigatório para remover loading)
                await self.answer_callback_query(query_id=query_id, text="")
                
                # Tentar deletar a mensagem do menu (melhor opção - não polui o chat)
                try:
                    await self.delete_message(chat_id=chat_id, message_id=message_id)
                    logger.info(
                        "Menu fechado - mensagem deletada",
                        chat_id=chat_id,
                        message_id=message_id
                    )
                except Exception as e:
                    # Se não conseguir deletar (ex: mensagem muito antiga), editar removendo botões
                    logger.warning(
                        "Não foi possível deletar mensagem, editando para remover botões",
                        chat_id=chat_id,
                        message_id=message_id,
                        error=str(e)
                    )
                    try:
                        await self.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text="✅ Menu fechado.",
                            reply_markup=None
                        )
                        logger.info(
                            "Menu fechado - botões removidos",
                            chat_id=chat_id,
                            message_id=message_id
                        )
                    except (ValueError, Exception) as e2:
                        # Mensagem muito antiga ou outro erro - apenas logar
                        logger.warning(
                            "Não foi possível editar mensagem para fechar menu (mensagem muito antiga ou outro erro)",
                            chat_id=chat_id,
                            message_id=message_id,
                            error=str(e2)
                        )
                        # Não enviar nova mensagem aqui - o menu já foi fechado via delete
                
                # Retornar imediatamente - não processar com chatbot
                return
            
            # Processar com chatbot - enviar callback_query completo conforme especificação
            chatbot_response = await self._process_callback_with_chatbot(
                callback_query=callback_query,
                user_id=user_id,
                username=username,
                chat_id=chat_id,
                access_token=access_token,
                userinfo=userinfo
            )
            
            # Responder ao callback (obrigatório para remover loading)
            # Texto vazio para não mostrar popup conforme especificação
            await self.answer_callback_query(query_id=query_id, text="")
            
            # IMPORTANTE: Verificar delete_message ANTES de qualquer outra ação
            delete_message = chatbot_response.get("delete_message", False) if chatbot_response else False
            message_id_to_delete = chatbot_response.get("message_id") if chatbot_response else None
            chat_id_to_delete = chatbot_response.get("chat_id") if chatbot_response else None
            
            # Usar chat_id do chatbot_response se disponível, caso contrário usar do callback
            chat_id_to_delete = chat_id_to_delete or chat_id
            
            logger.info(
                "Verificando delete_message (callback)",
                delete_message=delete_message,
                message_id_to_delete=message_id_to_delete,
                chat_id_to_delete=chat_id_to_delete,
                has_text=bool(chatbot_response.get("text") if chatbot_response else False),
                text_preview=chatbot_response.get("text", "")[:50] if chatbot_response and chatbot_response.get("text") else "",
                edit_message=chatbot_response.get("edit_message", False) if chatbot_response else False
            )
            
            if delete_message and message_id_to_delete and chat_id_to_delete:
                # Deletar mensagem do bot (NÃO editar nem enviar nova)
                try:
                    await self.delete_message(chat_id=chat_id_to_delete, message_id=message_id_to_delete)
                    logger.info(
                        "Mensagem do bot deletada (callback)",
                        chat_id=chat_id_to_delete,
                        message_id=message_id_to_delete
                    )
                except Exception as e:
                    logger.warning(
                        "Erro ao deletar mensagem do bot (callback)",
                        chat_id=chat_id_to_delete,
                        message_id=message_id_to_delete,
                        error=str(e)
                    )
                # Retornar após deletar (não processar mais nada)
                return
            
            if chatbot_response and chatbot_response.get("text"):
                text_response = chatbot_response.get("text")
                reply_markup = chatbot_response.get("reply_markup")
                parse_mode = chatbot_response.get("parse_mode")
                edit_message = chatbot_response.get("edit_message", False)
                # IMPORTANTE: Se chatbot_response tem message_id, usar ele (para erros 401, por exemplo)
                # Caso contrário, usar message_id do callback
                message_id_to_edit = chatbot_response.get("message_id")
                if not message_id_to_edit:
                    message_id_to_edit = message_id
                delete_user_message = chatbot_response.get("delete_user_message", False)
                user_message_id = chatbot_response.get("user_message_id")
                
                logger.info(
                    "Processando resposta do chatbot (callback)",
                    has_text=bool(text_response),
                    edit_message=edit_message,
                    message_id_to_edit=message_id_to_edit,
                    parse_mode=parse_mode,
                    has_reply_markup=bool(reply_markup)
                )
                
                # Verificar se deve editar mensagem existente (mantém chat limpo)
                if edit_message and message_id_to_edit:
                    # Editar mensagem existente (RECOMENDADO - mantém chat limpo)
                    logger.info(
                        "Editando mensagem do pedido (callback)",
                        chat_id=chat_id,
                        message_id=message_id_to_edit,
                        text_preview=text_response[:50]
                    )
                    try:
                        await self.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id_to_edit,
                            text=text_response,
                            parse_mode=parse_mode,
                            reply_markup=reply_markup
                        )
                    except ValueError as e:
                        error_str = str(e)
                        # Verificar tipo de erro
                        if "not_modified:" in error_str:
                            # Mensagem já tem o mesmo conteúdo - não fazer nada (não criar nova mensagem)
                            logger.info(
                                "Mensagem já tem o mesmo conteúdo - não precisa editar",
                                chat_id=chat_id,
                                message_id=message_id_to_edit
                            )
                            # Não fazer nada - mensagem já está correta
                        elif "too_old:" in error_str:
                            # Mensagem muito antiga (>48h) - deletar antiga e enviar nova
                            logger.warning(
                                "Mensagem muito antiga - deletando e enviando nova",
                                chat_id=chat_id,
                                message_id=message_id_to_edit
                            )
                            # Tentar deletar mensagem antiga
                            try:
                                await self.delete_message(chat_id=chat_id, message_id=message_id_to_edit)
                                logger.info("Mensagem antiga deletada com sucesso", chat_id=chat_id, message_id=message_id_to_edit)
                            except Exception as delete_error:
                                logger.warning(
                                    "Não foi possível deletar mensagem antiga",
                                    chat_id=chat_id,
                                    message_id=message_id_to_edit,
                                    error=str(delete_error)
                                )
                            # Enviar nova mensagem
                            telegram_result = await self.send_message(
                                chat_id=chat_id,
                                text=text_response,
                                parse_mode=parse_mode,
                                reply_markup=reply_markup
                            )
                            logger.info(
                                "Nova mensagem enviada (mensagem antiga deletada)",
                                chat_id=chat_id,
                                new_message_id=telegram_result.get("result", {}).get("message_id") if telegram_result.get("ok") else None
                            )
                        else:
                            # Outro tipo de erro - tentar enviar nova mensagem (mas não deletar)
                            logger.warning(
                                "Erro ao editar mensagem - enviando nova mensagem",
                                chat_id=chat_id,
                                message_id=message_id_to_edit,
                                error=error_str
                            )
                            telegram_result = await self.send_message(
                                chat_id=chat_id,
                                text=text_response,
                                parse_mode=parse_mode,
                                reply_markup=reply_markup
                            )
                            logger.info(
                                "Nova mensagem enviada (fallback)",
                                chat_id=chat_id,
                                new_message_id=telegram_result.get("result", {}).get("message_id") if telegram_result.get("ok") else None
                            )
                else:
                    # Enviar nova mensagem (apenas se não tiver message_id)
                    telegram_result = await self.send_message(
                        chat_id=chat_id,
                        text=text_response,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup
                    )
                    
                    # Capturar message_id da nova mensagem criada
                    if telegram_result.get("ok") and telegram_result.get("result", {}).get("message_id"):
                        new_message_id = telegram_result["result"]["message_id"]
                        logger.info(
                            "Nova mensagem criada (callback)",
                            chat_id=chat_id,
                            message_id=new_message_id
                        )
                
                # Deletar mensagem do usuário se solicitado
                # Usar user_message_id se fornecido, caso contrário usar message_id do callback
                message_to_delete = user_message_id if user_message_id else None
                if delete_user_message and message_to_delete:
                    try:
                        await self.delete_message(chat_id=chat_id, message_id=message_to_delete)
                        logger.info(
                            "Mensagem do usuário deletada (callback)",
                            chat_id=chat_id,
                            message_id=message_to_delete
                        )
                    except Exception as e:
                        logger.warning(
                            "Erro ao deletar mensagem do usuário (callback)",
                            chat_id=chat_id,
                            message_id=message_to_delete,
                            error=str(e)
                        )
                    
        except Exception as e:
            logger.error(f"Erro ao processar callback query: {e}", exc_info=True)
            # NÃO PROCESSAR EM CASO DE ERRO
            return
    
    async def _process_callback_with_chatbot(
        self,
        callback_query: Dict[str, Any],
        user_id: str,
        username: str,
        chat_id: int,
        access_token: Optional[str] = None,
        userinfo: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processa callback_query com o chatbot service
        Envia callback_query completo conforme especificação
        
        Args:
            callback_query: Objeto callback_query completo do Telegram
            user_id: ID do usuário do Telegram
            username: Nome de usuário do Telegram
            chat_id: ID do chat do Telegram
            access_token: Token de acesso do Keycloak (opcional)
            userinfo: Informações do usuário do Keycloak (opcional)
            
        Returns:
            Dicionário com 'text' (str) e opcionalmente 'reply_markup' (dict), 'edit_message' (bool) e 'message_id' (int)
        """
        try:
            # Criar user_id único combinando telegram_id e chat_id
            telegram_user_id = f"telegram_{user_id}_{chat_id}"
            
            # Preparar metadata com informações de autenticação
            is_authenticated = access_token is not None and userinfo is not None
            metadata = {
                "telegram_user_id": user_id,
                "telegram_username": username,
                "telegram_chat_id": chat_id,
                "platform": "telegram",
                "is_authenticated": is_authenticated
            }
            
            # Adicionar informações do usuário autenticado se disponível
            if userinfo:
                metadata.update({
                    "keycloak_user_id": userinfo.get("sub"),
                    "preferred_username": userinfo.get("preferred_username"),
                    "email": userinfo.get("email"),
                    "name": userinfo.get("name")
                })
            
            # Chamar chatbot service com callback_query completo conforme especificação
            if is_authenticated and access_token:
                # Usar endpoint autenticado que valida perfil "colaborador"
                response = await self.chatbot_client.process_message_authenticated(
                    user_id=telegram_user_id,
                    message="",  # Vazio pois vamos enviar callback_query
                    token=access_token,
                    session_id=f"telegram_{chat_id}",
                    conversation_id=None,
                    callback_query=callback_query  # Enviar callback_query completo
                )
            else:
                # Fallback para endpoint não autenticado (não deveria acontecer se autenticação estiver correta)
                logger.warning("Processando callback sem autenticação", user_id=user_id)
                response = await self.chatbot_client.process_message(
                    user_id=telegram_user_id,
                    message="",
                    session_id=f"telegram_{chat_id}",
                    metadata=metadata,
                    callback_query=callback_query
                )
            
            if response and response.get("success"):
                # Extrair texto da resposta
                text = response.get("response", "")
                if not text:
                    text = "Não consegui gerar uma resposta."
                
                # Verificar se tem botões usando flag explícita
                result = {"text": text}
                
                # Adicionar parse_mode se fornecido
                if response.get("parse_mode"):
                    result["parse_mode"] = response["parse_mode"]
                
                # Adicionar delete_message e message_id se fornecidos (para deletar mensagem do bot)
                if response.get("delete_message"):
                    result["delete_message"] = response["delete_message"]
                if response.get("message_id"):
                    result["message_id"] = response["message_id"]
                
                # Adicionar delete_user_message e user_message_id se fornecidos
                if response.get("delete_user_message"):
                    result["delete_user_message"] = response["delete_user_message"]
                if response.get("user_message_id"):
                    result["user_message_id"] = response["user_message_id"]
                
                if response.get("has_keyboard") and response.get("reply_markup"):
                    result["reply_markup"] = response["reply_markup"]
                    
                    # Log para depuração
                    keyboard_type = response.get("keyboard_type", "inline")
                    buttons_count = len(response["reply_markup"].get("inline_keyboard", []))
                    logger.info(
                        "Adicionando teclado à resposta (callback)",
                        chat_id=chat_id,
                        keyboard_type=keyboard_type,
                        buttons_count=buttons_count
                    )
                elif response.get("telegram_keyboard"):
                    # Compatibilidade com alias telegram_keyboard
                    result["reply_markup"] = response["telegram_keyboard"]
                    logger.info("Adicionando teclado (via telegram_keyboard)", chat_id=chat_id)
                
                # Verificar se deve editar mensagem existente
                edit_message = response.get("edit_message", False)
                message_id_to_edit = response.get("message_id")
                
                if edit_message and message_id_to_edit:
                    result["edit_message"] = True
                    result["message_id"] = message_id_to_edit
                    logger.info(
                        "Resposta requer edição de mensagem (callback)",
                        chat_id=chat_id,
                        message_id=message_id_to_edit
                    )
                else:
                    result["edit_message"] = False
                
                return result
            else:
                error = response.get("error", "Erro desconhecido") if response else "Erro ao processar callback"
                status_code = response.get("status_code") if response else None
                
                logger.warning(f"Erro no chatbot (callback): {error}", status_code=status_code, user_id=user_id)
                
                # IMPORTANTE: Verificar se o chatbot retornou delete_message mesmo com erro
                # Se sim, retornar delete_message para que a mensagem seja deletada
                delete_message = response.get("delete_message", False) if response else False
                message_id_to_delete = response.get("message_id") if response else None
                
                if delete_message and message_id_to_delete:
                    # Retornar delete_message mesmo em caso de erro
                    return {
                        "delete_message": True,
                        "message_id": message_id_to_delete,
                        "text": "",  # Texto vazio pois vamos deletar
                        "edit_message": False
                    }
                
                # Tratamento específico para erros de autenticação/autorização
                error_text = ""
                auth_url = None
                if status_code == 401:
                    # Gerar link de login quando token expirar
                    try:
                        auth_url, state = keycloak_auth_service.generate_authorization_url(
                            telegram_user_id=user_id,
                            telegram_chat_id=str(chat_id)
                        )
                        error_text = (
                            "❌ Erro de autenticação: Token inválido ou expirado. Não foi possível salvar o pedido.\n\n"
                            "Por favor, <a href=\"{}\">clique aqui para fazer login novamente</a>.\n\n"
                            "Após fazer login, você poderá continuar editando seu pedido."
                        ).format(auth_url)
                    except Exception as e:
                        logger.error(f"Erro ao gerar link de login: {e}", exc_info=True)
                        error_text = "🔐 Seu token de autenticação expirou. Por favor, faça login novamente."
                elif status_code == 403:
                    error_text = "🔒 Acesso negado. Você precisa ter o perfil 'colaborador' para usar este recurso. Entre em contato com o administrador."
                elif "connection" in str(error).lower() or "failed" in str(error).lower() or "unreachable" in str(error).lower():
                    error_text = "Desculpe, o serviço de chatbot não está disponível no momento. Por favor, tente novamente em alguns instantes."
                else:
                    error_text = f"Desculpe, ocorreu um erro: {error}"
                
                # IMPORTANTE: Para callbacks, editar a mensagem do pedido existente (não criar nova)
                # O message_id do pedido está no callback_query.message.message_id
                callback_message_id = callback_query.get("message", {}).get("message_id") if callback_query else None
                if callback_message_id:
                    # Editar a mensagem do pedido com o erro
                    # IMPORTANTE: Tentar preservar botões originais da mensagem e adicionar botão de login
                    original_reply_markup = callback_query.get("message", {}).get("reply_markup")
                    final_reply_markup = None
                    
                    if status_code == 401 and auth_url:
                        # Criar botão de login
                        login_button = {
                            "text": "🔐 Fazer Login",
                            "url": auth_url
                        }
                        
                        # Se tiver botões originais, tentar adicionar botão de login
                        if original_reply_markup:
                            # Tentar adicionar botão de login aos botões existentes
                            inline_keyboard = original_reply_markup.get("inline_keyboard", [])
                            # Adicionar linha com botão de login no início
                            login_row = [[login_button]]
                            final_keyboard = login_row + inline_keyboard
                            final_reply_markup = {"inline_keyboard": final_keyboard}
                        else:
                            # Se não tiver botões originais, criar apenas botão de login
                            final_reply_markup = {"inline_keyboard": [[login_button]]}
                    # Para outros erros, remover botões (final_reply_markup já é None)
                    
                    logger.info(
                        "Retornando erro 401 para editar mensagem do pedido",
                        callback_message_id=callback_message_id,
                        chat_id=chat_id,
                        has_original_keyboard=bool(original_reply_markup),
                        has_login_button=status_code == 401 and auth_url is not None
                    )
                    return {
                        "text": error_text, 
                        "edit_message": True, 
                        "message_id": callback_message_id,
                        "parse_mode": "HTML",
                        "reply_markup": final_reply_markup
                    }
                else:
                    # Se não houver message_id, criar nova mensagem
                    logger.warning("Erro 401 mas sem message_id do callback - criando nova mensagem", chat_id=chat_id)
                    return {"text": error_text, "edit_message": False, "parse_mode": "HTML"}
                
        except Exception as e:
            logger.error(f"Erro ao processar callback com chatbot: {e}", exc_info=True)
            return {"text": "Desculpe, ocorreu um erro ao processar sua ação.", "edit_message": False}
    
    async def _process_message_with_chatbot(
        self,
        user_id: str,
        username: str,
        message: str,
        chat_id: int,
        access_token: Optional[str] = None,
        userinfo: Optional[Dict[str, Any]] = None,
        telegram_message: Optional[Dict[str, Any]] = None,
        update_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Processa mensagem com o chatbot service
        
        Args:
            user_id: ID do usuário do Telegram
            username: Nome de usuário do Telegram
            message: Texto da mensagem
            chat_id: ID do chat do Telegram
            access_token: Token de acesso do Keycloak (opcional)
            userinfo: Informações do usuário do Keycloak (opcional)
            telegram_message: Objeto message completo do Telegram (opcional)
            update_id: ID da atualização do Telegram (opcional)
            
        Returns:
            Dicionário com 'text' (str) e opcionalmente 'reply_markup' (dict)
        """
        try:
            # Criar user_id único combinando telegram_id e chat_id
            telegram_user_id = f"telegram_{user_id}_{chat_id}"
            
            # Preparar metadata com informações de autenticação
            is_authenticated = access_token is not None and userinfo is not None
            metadata = {
                "telegram_user_id": user_id,
                "telegram_username": username,
                "telegram_chat_id": chat_id,
                "platform": "telegram",
                "is_authenticated": is_authenticated
            }
            
            # Adicionar informações do usuário autenticado se disponível
            if userinfo:
                metadata.update({
                    "keycloak_user_id": userinfo.get("sub"),
                    "preferred_username": userinfo.get("preferred_username"),
                    "email": userinfo.get("email"),
                    "name": userinfo.get("name")
                })
            
            # Chamar chatbot service
            # Se usuário estiver autenticado, usar endpoint autenticado
            if is_authenticated and access_token:
                # Usar endpoint autenticado que valida perfil "colaborador"
                # Conforme especificação: passar objeto message completo e update_id
                response = await self.chatbot_client.process_message_authenticated(
                    user_id=telegram_user_id,
                    message=message,
                    token=access_token,
                    session_id=f"telegram_{chat_id}",
                    conversation_id=None,  # Opcional: buscar conversation_id se houver
                    telegram_message=telegram_message,
                    update_id=update_id
                )
            else:
                # Usar endpoint não autenticado (legado)
                credentials = None
                if is_authenticated:
                    credentials = {
                        "is_authenticated": True,
                        "token": access_token,
                        "keycloak_user_id": userinfo.get("sub"),
                        "preferred_username": userinfo.get("preferred_username"),
                        "email": userinfo.get("email")
                    }
                
                response = await self.chatbot_client.process_message(
                    user_id=telegram_user_id,
                    message=message,
                    session_id=f"telegram_{chat_id}",
                    metadata=metadata,
                    credentials=credentials
                )
            
            if response and response.get("success"):
                # Extrair texto da resposta
                text = response.get("response", "")
                if not text:
                    # Tentar extrair de response_data se response for um dict aninhado
                    response_data = response.get("response", {})
                    if isinstance(response_data, dict):
                        text = response_data.get("response", "")
                    else:
                        text = str(response_data) if response_data else ""
                
                if not text:
                    text = "Não consegui gerar uma resposta."
                
                # Verificar se tem botões usando flag explícita
                result = {"text": text}
                
                # Adicionar parse_mode se fornecido
                if response.get("parse_mode"):
                    result["parse_mode"] = response["parse_mode"]
                
                # Adicionar delete_message e message_id se fornecidos (para deletar mensagem do bot)
                if response.get("delete_message"):
                    result["delete_message"] = response["delete_message"]
                if response.get("message_id"):
                    result["message_id"] = response["message_id"]
                
                # Adicionar delete_user_message se fornecido
                if response.get("delete_user_message"):
                    result["delete_user_message"] = response["delete_user_message"]
                
                if response.get("has_keyboard") and response.get("reply_markup"):
                    result["reply_markup"] = response["reply_markup"]
                    
                    # Log para depuração
                    keyboard_type = response.get("keyboard_type", "inline")
                    buttons_count = len(response["reply_markup"].get("inline_keyboard", []))
                    logger.info(
                        "Adicionando teclado à resposta",
                        chat_id=chat_id,
                        keyboard_type=keyboard_type,
                        buttons_count=buttons_count
                    )
                elif response.get("telegram_keyboard"):
                    # Compatibilidade com alias telegram_keyboard
                    result["reply_markup"] = response["telegram_keyboard"]
                    logger.info("Adicionando teclado (via telegram_keyboard)", chat_id=chat_id)
                
                # Verificar se deve editar mensagem existente
                edit_message = response.get("edit_message", False)
                message_id_to_edit = response.get("message_id")
                
                if edit_message and message_id_to_edit:
                    result["edit_message"] = True
                    result["message_id"] = message_id_to_edit
                    logger.info(
                        "Resposta requer edição de mensagem",
                        chat_id=chat_id,
                        message_id=message_id_to_edit
                    )
                else:
                    result["edit_message"] = False
                
                return result
            else:
                error = response.get("error", "Erro desconhecido") if response else "Erro ao processar mensagem"
                status_code = response.get("status_code") if response else None
                
                logger.warning(f"Erro no chatbot: {error}", status_code=status_code, user_id=user_id)
                
                # IMPORTANTE: Verificar se o chatbot retornou delete_message mesmo com erro
                # Se sim, retornar delete_message para que a mensagem seja deletada
                delete_message = response.get("delete_message", False) if response else False
                message_id_to_delete = response.get("message_id") if response else None
                
                if delete_message and message_id_to_delete:
                    # Retornar delete_message mesmo em caso de erro
                    return {
                        "delete_message": True,
                        "message_id": message_id_to_delete,
                        "text": "",  # Texto vazio pois vamos deletar
                        "edit_message": False
                    }
                
                # Tratamento específico para erros de autenticação/autorização
                error_text = ""
                if status_code == 401:
                    # Gerar link de login quando token expirar
                    try:
                        auth_url, state = keycloak_auth_service.generate_authorization_url(
                            telegram_user_id=user_id,
                            telegram_chat_id=str(chat_id)
                        )
                        error_text = (
                            "❌ Erro de autenticação: Token inválido ou expirado. Não foi possível salvar o pedido.\n\n"
                            "Por favor, <a href=\"{}\">clique aqui para fazer login novamente</a>.\n\n"
                            "Após fazer login, você poderá continuar editando seu pedido."
                        ).format(auth_url)
                    except Exception as e:
                        logger.error(f"Erro ao gerar link de login: {e}", exc_info=True)
                        error_text = "🔐 Seu token de autenticação expirou. Por favor, faça login novamente."
                elif status_code == 403:
                    error_text = "🔒 Acesso negado. Você precisa ter o perfil 'colaborador' para usar este recurso. Entre em contato com o administrador."
                elif "connection" in str(error).lower() or "failed" in str(error).lower() or "unreachable" in str(error).lower():
                    error_text = "Desculpe, o serviço de chatbot não está disponível no momento. Por favor, tente novamente em alguns instantes."
                else:
                    error_text = f"Desculpe, ocorreu um erro: {error}"
                
                # IMPORTANTE: Verificar se há message_id na resposta do chatbot para editar a mensagem do pedido
                # Se o chatbot retornou message_id mesmo com erro, significa que há uma mensagem do pedido para editar
                message_id_to_edit = response.get("message_id") if response else None
                if message_id_to_edit:
                    # Editar a mensagem do pedido com o erro
                    # IMPORTANTE: Remover reply_markup (botões) ao editar com erro de autenticação
                    logger.info(
                        "Retornando erro 401 para editar mensagem do pedido (mensagem de texto)",
                        message_id_to_edit=message_id_to_edit,
                        chat_id=chat_id
                    )
                    return {
                        "text": error_text, 
                        "edit_message": True, 
                        "message_id": message_id_to_edit,
                        "parse_mode": "HTML",
                        "reply_markup": None  # Remover botões ao mostrar erro
                    }
                else:
                    # Se não houver message_id, criar nova mensagem
                    logger.warning("Erro 401 mas sem message_id na resposta - criando nova mensagem", chat_id=chat_id)
                    return {"text": error_text, "edit_message": False, "parse_mode": "HTML"}
                
        except Exception as e:
            logger.error(f"Erro ao processar mensagem com chatbot: {e}", exc_info=True)
            return {"text": "Desculpe, ocorreu um erro ao processar sua mensagem."}
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem para o Telegram
        
        Args:
            chat_id: ID do chat
            text: Texto da mensagem
            parse_mode: Modo de parsing (HTML, Markdown, etc.)
            reply_to_message_id: ID da mensagem para responder
            reply_markup: Teclado inline ou de resposta (opcional)
            
        Returns:
            Resposta da API do Telegram
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            
            if parse_mode:
                payload["parse_mode"] = parse_mode
            
            if reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao enviar mensagem: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}", exc_info=True)
            raise
    
    async def edit_message_text(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Edita texto de uma mensagem existente no Telegram
        
        Args:
            chat_id: ID do chat
            message_id: ID da mensagem a ser editada
            text: Novo texto da mensagem
            parse_mode: Modo de parsing (HTML, Markdown, etc.)
            reply_markup: Teclado inline ou de resposta (opcional)
            
        Returns:
            Resposta da API do Telegram
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/editMessageText"
            
            payload = {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text
            }
            
            if parse_mode:
                payload["parse_mode"] = parse_mode
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            logger.info(
                "Mensagem editada com sucesso",
                chat_id=chat_id,
                message_id=message_id
            )
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            # Erro 400 pode ter diferentes causas
            if e.response.status_code == 400:
                error_detail = "Mensagem muito antiga ou não pode ser editada"
                error_type = "unknown"
                try:
                    error_json = e.response.json()
                    error_description = error_json.get("description", "")
                    error_detail = error_description
                    
                    # Identificar tipo de erro
                    if "message is not modified" in error_description.lower():
                        # Mensagem já tem o mesmo conteúdo - não precisa fazer nada
                        error_type = "not_modified"
                    elif "message can't be edited" in error_description.lower() or "too old" in error_description.lower():
                        # Mensagem muito antiga (>48h) - precisa deletar e enviar nova
                        error_type = "too_old"
                    else:
                        # Outro tipo de erro 400
                        error_type = "other"
                except:
                    pass
                
                logger.warning(
                    "Não foi possível editar mensagem",
                    chat_id=chat_id,
                    message_id=message_id,
                    error=error_detail,
                    error_type=error_type
                )
                # Lançar exceção específica com tipo de erro para que o código chamador possa tratar
                raise ValueError(f"Mensagem não pode ser editada: {error_type}:{error_detail}") from e
            else:
                logger.error(f"Erro HTTP ao editar mensagem: {e}")
                raise
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao editar mensagem: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao editar mensagem: {e}", exc_info=True)
            raise
    
    async def send_chat_action(self, chat_id: int, action: str = "typing"):
        """
        Envia ação de chat (typing, upload_photo, etc.)
        
        Args:
            chat_id: ID do chat
            action: Ação a enviar (typing, upload_photo, etc.)
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/sendChatAction"
            
            payload = {
                "chat_id": chat_id,
                "action": action
            }
            
            await client.post(url, json=payload)
            
        except Exception as e:
            logger.debug(f"Erro ao enviar chat action (não crítico): {e}")
    
    async def answer_callback_query(
        self,
        query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ):
        """
        Responde a uma callback query
        
        Args:
            query_id: ID da query
            text: Texto da resposta
            show_alert: Se deve mostrar alerta
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/answerCallbackQuery"
            
            payload = {
                "callback_query_id": query_id
            }
            
            if text:
                payload["text"] = text
            
            if show_alert:
                payload["show_alert"] = True
            
            await client.post(url, json=payload)
            
        except Exception as e:
            logger.debug(f"Erro ao responder callback query (não crítico): {e}")
    
    async def delete_message(
        self,
        chat_id: int,
        message_id: int
    ) -> Dict[str, Any]:
        """
        Deleta uma mensagem do Telegram
        
        Args:
            chat_id: ID do chat
            message_id: ID da mensagem a ser deletada
            
        Returns:
            Resposta da API do Telegram
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/deleteMessage"
            
            payload = {
                "chat_id": chat_id,
                "message_id": message_id
            }
            
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            logger.info(
                "Mensagem deletada com sucesso",
                chat_id=chat_id,
                message_id=message_id
            )
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.warning(f"Erro HTTP ao deletar mensagem: {e}")
            raise
        except Exception as e:
            logger.warning(f"Erro ao deletar mensagem: {e}", exc_info=True)
            raise
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o webhook configurado
        
        Returns:
            Informações do webhook
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/getWebhookInfo"
            
            response = await client.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao obter informações do webhook: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao obter informações do webhook: {e}", exc_info=True)
            raise
    
    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: int = 100,
        timeout: int = 10,
        allowed_updates: Optional[list] = None
    ) -> list:
        """
        Busca atualizações do Telegram (polling)
        
        Args:
            offset: ID da última atualização recebida + 1
            limit: Número máximo de atualizações (1-100)
            timeout: Timeout em segundos para long polling (0-60)
            allowed_updates: Lista de tipos de atualização permitidos
            
        Returns:
            Lista de atualizações
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/getUpdates"
            
            params = {
                "timeout": timeout,
                "limit": limit
            }
            
            if offset is not None:
                params["offset"] = offset
            
            if allowed_updates:
                params["allowed_updates"] = allowed_updates
            
            response = await client.get(url, params=params, timeout=timeout + 5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("ok"):
                return data.get("result", [])
            else:
                logger.error(f"Erro ao buscar atualizações: {data.get('description', 'Erro desconhecido')}")
                return []
            
        except httpx.TimeoutException:
            # Timeout é esperado em long polling quando não há atualizações
            return []
        except httpx.HTTPError as e:
            # Erro 409 Conflict significa que há webhook configurado
            if hasattr(e, 'response') and e.response and e.response.status_code == 409:
                # Contador e timestamp para evitar loop infinito (atributo de classe)
                if not hasattr(self, '_webhook_409_count'):
                    self._webhook_409_count = 0
                if not hasattr(self, '_last_webhook_removal_time'):
                    self._last_webhook_removal_time = 0
                
                import time
                current_time = time.time()
                time_since_last_removal = current_time - self._last_webhook_removal_time
                
                # Se removeu recentemente (menos de 20 segundos), pode ser propagação - aguardar mais
                if time_since_last_removal < 20 and self._webhook_409_count > 0:
                    # Log apenas na primeira vez após remoção recente
                    if self._webhook_409_count == 1:
                        logger.debug("Erro 409 após remoção recente - aguardando propagação do Telegram (20s)...")
                    await asyncio.sleep(20)  # Aguardar propagação completa
                    return []
                
                self._webhook_409_count += 1
                
                # Se já tentou muitas vezes, apenas logar uma vez e aguardar mais tempo
                if self._webhook_409_count > 3:
                    if self._webhook_409_count == 4:
                        logger.warning("⚠️ Erro 409 persistente. Aguardando 60 segundos antes de tentar novamente...")
                        logger.warning("Se o problema persistir, verifique se há outro serviço configurando webhook.")
                    await asyncio.sleep(60)  # Aguardar 60 segundos antes de tentar novamente
                    return []
                
                # Log apenas nas primeiras tentativas
                if self._webhook_409_count <= 2:
                    logger.warning(f"Erro 409: Webhook detectado. Removendo... (tentativa {self._webhook_409_count}/3)")
                
                try:
                    # Tentar remover webhook automaticamente
                    delete_result = await self.delete_webhook(drop_pending_updates=True)
                    
                    # Verificar se foi realmente removido
                    await asyncio.sleep(3)  # Aguardar um pouco antes de verificar
                    webhook_info = await self.get_webhook_info()
                    webhook_url = None
                    if webhook_info and webhook_info.get("ok") and webhook_info.get("result"):
                        webhook_url = webhook_info.get("result", {}).get("url", "")
                        if webhook_url:
                            webhook_url = webhook_url.strip()
                    
                    if webhook_url:
                        # Webhook ainda configurado - pode estar sendo reconfigurado
                        if self._webhook_409_count <= 2:
                            logger.warning(f"⚠️ Webhook ainda configurado após remoção (URL: {webhook_url})")
                        await asyncio.sleep(15)
                    else:
                        # Webhook removido com sucesso
                        if self._webhook_409_count <= 2:
                            logger.info("✅ Webhook removido. Aguardando propagação (20s)...")
                        self._webhook_409_count = 0  # Resetar contador
                        self._last_webhook_removal_time = time.time()  # Registrar tempo da remoção
                        await asyncio.sleep(20)  # Aguardar propagação completa antes de tentar getUpdates
                        
                except Exception as delete_error:
                    if self._webhook_409_count <= 2:
                        logger.error(f"Erro ao remover webhook: {delete_error}", exc_info=True)
                    await asyncio.sleep(15)
            else:
                # Resetar contador se não for erro 409
                if hasattr(self, '_webhook_409_count'):
                    self._webhook_409_count = 0
                logger.error(f"Erro HTTP ao buscar atualizações: {e}")
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar atualizações: {e}", exc_info=True)
            return []
    
    async def delete_webhook(self, drop_pending_updates: bool = False) -> Dict[str, Any]:
        """
        Remove webhook configurado
        
        Args:
            drop_pending_updates: Se deve descartar atualizações pendentes
            
        Returns:
            Resposta da API do Telegram
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/deleteWebhook"
            
            payload = {}
            if drop_pending_updates:
                payload["drop_pending_updates"] = True
            
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao remover webhook: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao remover webhook: {e}", exc_info=True)
            raise
