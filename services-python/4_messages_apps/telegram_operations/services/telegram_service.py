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
            
            # ========== VERIFICAÇÃO DE AUTENTICAÇÃO - DEVE SER A PRIMEIRA COISA APÓS EXTRAIR INFORMAÇÕES ==========
            # NÃO PROCESSAR NADA ANTES DE VERIFICAR AUTENTICAÇÃO
            print("=" * 80, file=sys.stderr)
            print("INICIANDO VERIFICACAO DE AUTENTICACAO (ANTES DE QUALQUER PROCESSAMENTO)", file=sys.stderr)
            print(f"user_id={user_id}, chat_id={chat_id}, text={text[:50]}", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            
            logger.info("INICIANDO VERIFICACAO DE AUTENTICACAO", telegram_user_id=user_id, chat_id=chat_id)
            
            # FORÇAR VERIFICAÇÃO - SEMPRE VERIFICAR ANTES DE PROCESSAR
            auth_status = None
            is_authenticated = False
            try:
                print(f"Chamando get_user_auth_status para user_id={user_id}", file=sys.stderr)
                auth_status = keycloak_auth_service.get_user_auth_status(user_id)
                print(f"auth_status RAW: {auth_status}", file=sys.stderr)
                is_authenticated = auth_status and auth_status.get("is_authenticated", False)
                print(f"auth_status recebido: is_authenticated={is_authenticated}", file=sys.stderr)
                print(f"auth_status type: {type(auth_status)}, keys: {auth_status.keys() if auth_status else 'None'}", file=sys.stderr)
                
                logger.info(
                    "Status de autenticação verificado",
                    telegram_user_id=user_id,
                    is_authenticated=is_authenticated
                )
                
                # Se não autenticado, ENVIAR MENSAGEM DE AUTENTICAÇÃO E RETORNAR IMEDIATAMENTE (NÃO PROCESSAR)
                # VERIFICAÇÃO RIGOROSA: Se auth_status é None, False, ou is_authenticated é False
                if not auth_status or not is_authenticated or not auth_status.get("is_authenticated", False):
                    print("=" * 80, file=sys.stderr)
                    print(f"USUARIO NAO AUTENTICADO - user_id={user_id}", file=sys.stderr)
                    print(f"auth_status={auth_status}, is_authenticated={is_authenticated}", file=sys.stderr)
                    print("BLOQUEANDO PROCESSAMENTO - Enviando apenas mensagem de autenticacao", file=sys.stderr)
                    print("=" * 80, file=sys.stderr)
                    
                    logger.warning("USUARIO NAO AUTENTICADO - BLOQUEANDO PROCESSAMENTO", telegram_user_id=user_id, auth_status=auth_status)
                    
                    auth_url, state = keycloak_auth_service.generate_authorization_url(
                        telegram_user_id=user_id,
                        telegram_chat_id=str(chat_id)
                    )
                    
                    auth_message = (
                        "🔐 Você precisa estar autenticado para usar este bot.\n\n"
                        "Por favor, clique no link abaixo para fazer login:\n"
                        f"{auth_url}\n\n"
                        "Após fazer login, você será redirecionado de volta para o Telegram."
                    )
                    
                    print(f"Enviando APENAS mensagem de autenticacao para chat_id={chat_id}", file=sys.stderr)
                    await self.send_message(chat_id=chat_id, text=auth_message)
                    logger.info("Mensagem de autenticacao enviada - RETORNANDO SEM PROCESSAR", telegram_user_id=user_id)
                    print("=" * 80, file=sys.stderr)
                    print("RETORNANDO - NAO PROCESSAR COM CHATBOT - FIM DA FUNCAO", file=sys.stderr)
                    print("=" * 80, file=sys.stderr)
                    # CRÍTICO: Retornar aqui impede QUALQUER processamento com chatbot
                    # NÃO CONTINUAR PARA O CHATBOT DE FORMA ALGUMA
                    # NÃO CHAMAR _process_message_with_chatbot
                    # NÃO ENVIAR NENHUMA OUTRA MENSAGEM
                    # NÃO CONTINUAR O CÓDIGO ABAIXO
                    return  # FIM DA FUNÇÃO - NÃO EXECUTAR MAIS NADA
                    
            except Exception as e:
                print("=" * 80, file=sys.stderr)
                print(f"ERRO ao verificar autenticacao: {e}", file=sys.stderr)
                print("Tentando enviar mensagem de autenticacao mesmo assim...", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                
                logger.error(
                    "Erro ao verificar autenticação",
                    telegram_user_id=user_id,
                    error=str(e),
                    exc_info=True
                )
                # Em caso de erro, ainda assim pedir autenticação e RETORNAR
                try:
                    auth_url, state = keycloak_auth_service.generate_authorization_url(
                        telegram_user_id=user_id,
                        telegram_chat_id=str(chat_id)
                    )
                    auth_message = (
                        "🔐 Você precisa estar autenticado para usar este bot.\n\n"
                        "Por favor, clique no link abaixo para fazer login:\n"
                        f"{auth_url}\n\n"
                        "Após fazer login, você será redirecionado de volta para o Telegram."
                    )
                    await self.send_message(chat_id=chat_id, text=auth_message)
                    print("Mensagem de autenticacao enviada apos erro - RETORNANDO", file=sys.stderr)
                except Exception as e2:
                    logger.error("Erro ao enviar mensagem de autenticação", error=str(e2))
                return  # IMPORTANTE: Retornar aqui também
            
            # ========== SÓ CHEGA AQUI SE O USUÁRIO ESTIVER AUTENTICADO ==========
            # VERIFICAÇÃO ABSOLUTA - NUNCA PROCESSAR SEM AUTENTICAÇÃO
            # Verificar TODAS as condições possíveis antes de processar
            is_really_authenticated = (
                auth_status is not None and
                isinstance(auth_status, dict) and
                auth_status.get("is_authenticated") is True and
                is_authenticated is True
            )
            
            if not is_really_authenticated:
                print("=" * 80, file=sys.stderr)
                print("ERRO CRÍTICO: Verificação final falhou! Retornando SEM PROCESSAR", file=sys.stderr)
                print(f"is_really_authenticated={is_really_authenticated}", file=sys.stderr)
                print(f"auth_status={auth_status}", file=sys.stderr)
                print(f"is_authenticated={is_authenticated}", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                logger.error("ERRO CRÍTICO: Verificação final falhou - BLOQUEANDO PROCESSAMENTO", telegram_user_id=user_id)
                # NÃO PROCESSAR - RETORNAR IMEDIATAMENTE
                return  # FIM DA FUNÇÃO - NÃO EXECUTAR MAIS NADA
            
            print("=" * 80, file=sys.stderr)
            print(f"USUARIO AUTENTICADO - Processando com chatbot - user_id={user_id}", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            
            # Usuário autenticado - continuar processamento
            logger.info("USUARIO AUTENTICADO - Processando mensagem com chatbot", telegram_user_id=user_id)
            userinfo = auth_status.get("userinfo", {})
            logger.info(
                "Informações do usuário autenticado",
                telegram_user_id=user_id,
                preferred_username=userinfo.get("preferred_username"),
                keycloak_user_id=userinfo.get("sub")
            )
            
            # Enviar indicador de digitação
            await self.send_chat_action(chat_id=chat_id, action="typing")
            
            # Processar mensagem com o chatbot (com token de autenticação)
            access_token = keycloak_auth_service.get_access_token(user_id)
            logger.info("Enviando mensagem para chatbot com token de autenticação", telegram_user_id=user_id)
            response_text = await self._process_message_with_chatbot(
                user_id=user_id,
                username=username,
                message=text,
                chat_id=chat_id,
                access_token=access_token,
                userinfo=userinfo
            )
            
            # Enviar resposta para o Telegram
            if response_text:
                await self.send_message(chat_id=chat_id, text=response_text)
            else:
                # Se não houve resposta, verificar se foi erro de conexão
                error_msg = "Desculpe, não consegui processar sua mensagem. Tente novamente."
                if "connection" in str(response_text).lower() or "failed" in str(response_text).lower():
                    error_msg = "Desculpe, o serviço de chatbot não está disponível no momento. Por favor, tente novamente em alguns instantes."
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
            
            logger.info("Callback query recebido", query_id=query_id, data=data)
            
            # Responder ao callback (obrigatório)
            await self.answer_callback_query(query_id=query_id, text="Processando...")
            
            # VERIFICAR AUTENTICAÇÃO ANTES DE PROCESSAR
            print("=" * 80, file=sys.stderr)
            print(f"VERIFICANDO AUTENTICACAO PARA CALLBACK - user_id={user_id}", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            
            auth_status = keycloak_auth_service.get_user_auth_status(user_id)
            is_authenticated = auth_status and auth_status.get("is_authenticated", False)
            
            print(f"auth_status para callback: {auth_status}", file=sys.stderr)
            print(f"is_authenticated para callback: {is_authenticated}", file=sys.stderr)
            
            if not is_authenticated:
                print("=" * 80, file=sys.stderr)
                print(f"CALLBACK: USUARIO NAO AUTENTICADO - user_id={user_id}", file=sys.stderr)
                print("BLOQUEANDO PROCESSAMENTO DO CALLBACK", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                logger.warning("CALLBACK: Usuário não autenticado - bloqueando", telegram_user_id=user_id)
                # Enviar mensagem de autenticação
                try:
                    auth_url, state = keycloak_auth_service.generate_authorization_url(
                        telegram_user_id=user_id,
                        telegram_chat_id=str(chat_id)
                    )
                    auth_message = (
                        "🔐 Você precisa estar autenticado para usar este bot.\n\n"
                        "Por favor, clique no link abaixo para fazer login:\n"
                        f"{auth_url}\n\n"
                        "Após fazer login, você será redirecionado de volta para o Telegram."
                    )
                    await self.send_message(chat_id=chat_id, text=auth_message)
                except Exception as e2:
                    logger.error(f"Erro ao enviar mensagem de autenticação no callback: {e2}")
                return  # NÃO PROCESSAR CALLBACK SEM AUTENTICAÇÃO
            
            # Usuário autenticado - processar callback
            access_token = keycloak_auth_service.get_access_token(user_id) if is_authenticated else None
            userinfo = auth_status.get("userinfo") if is_authenticated else None
            
            # Processar com chatbot se houver dados
            if data:
                response_text = await self._process_message_with_chatbot(
                    user_id=user_id,
                    username=callback_query.get("from", {}).get("username", ""),
                    message=data,
                    chat_id=chat_id,
                    access_token=access_token,
                    userinfo=userinfo
                )
                
                if response_text:
                    await self.send_message(chat_id=chat_id, text=response_text)
                    
        except Exception as e:
            logger.error(f"Erro ao processar callback query: {e}", exc_info=True)
            # NÃO PROCESSAR EM CASO DE ERRO
            return
    
    async def _process_message_with_chatbot(
        self,
        user_id: str,
        username: str,
        message: str,
        chat_id: int,
        access_token: Optional[str] = None,
        userinfo: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Processa mensagem com o chatbot service
        
        Args:
            user_id: ID do usuário do Telegram
            username: Nome de usuário do Telegram
            message: Texto da mensagem
            chat_id: ID do chat do Telegram
            access_token: Token de acesso do Keycloak (opcional)
            userinfo: Informações do usuário do Keycloak (opcional)
            
        Returns:
            Texto da resposta do chatbot
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
                response = await self.chatbot_client.process_message_authenticated(
                    user_id=telegram_user_id,
                    message=message,
                    token=access_token,
                    session_id=f"telegram_{chat_id}",
                    conversation_id=None  # Opcional: buscar conversation_id se houver
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
                response_data = response.get("response", {})
                
                # Extrair texto da resposta
                if isinstance(response_data, dict):
                    text = response_data.get("response", "")
                else:
                    text = str(response_data)
                
                return text if text else "Não consegui gerar uma resposta."
            else:
                error = response.get("error", "Erro desconhecido") if response else "Erro ao processar mensagem"
                status_code = response.get("status_code") if response else None
                
                logger.warning(f"Erro no chatbot: {error}", status_code=status_code, user_id=user_id)
                
                # Tratamento específico para erros de autenticação/autorização
                if status_code == 401:
                    return "🔐 Seu token de autenticação expirou. Por favor, faça login novamente."
                elif status_code == 403:
                    return "🔒 Acesso negado. Você precisa ter o perfil 'colaborador' para usar este recurso. Entre em contato com o administrador."
                
                # Mensagem de erro mais amigável para erros de conexão
                if "connection" in str(error).lower() or "failed" in str(error).lower() or "unreachable" in str(error).lower():
                    return "Desculpe, o serviço de chatbot não está disponível no momento. Por favor, tente novamente em alguns instantes."
                else:
                    return f"Desculpe, ocorreu um erro: {error}"
                
        except Exception as e:
            logger.error(f"Erro ao processar mensagem com chatbot: {e}", exc_info=True)
            return None
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_to_message_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem para o Telegram
        
        Args:
            chat_id: ID do chat
            text: Texto da mensagem
            parse_mode: Modo de parsing (HTML, Markdown, etc.)
            reply_to_message_id: ID da mensagem para responder
            
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
            
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao enviar mensagem: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}", exc_info=True)
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
    
    async def set_webhook(
        self,
        url: str,
        secret_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configura webhook do Telegram
        
        Args:
            url: URL do webhook
            secret_token: Token secreto (opcional)
            
        Returns:
            Resposta da API do Telegram
        """
        try:
            client = await self._get_client()
            api_url = f"{self.base_url}/setWebhook"
            
            payload = {"url": url}
            
            if secret_token:
                payload["secret_token"] = secret_token
            
            response = await client.post(api_url, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao configurar webhook: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao configurar webhook: {e}", exc_info=True)
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
            # Erro 409 Conflict geralmente significa que há webhook configurado
            if hasattr(e, 'response') and e.response and e.response.status_code == 409:
                logger.error("Erro 409 Conflict: Webhook ainda está configurado! Tentando remover...")
                try:
                    # Tentar remover webhook múltiplas vezes com delay maior
                    for i in range(5):
                        await self.delete_webhook(drop_pending_updates=True)
                        await asyncio.sleep(2)  # Aguardar 2 segundos para propagação
                        # Verificar se foi removido
                        webhook_info = await self.get_webhook_info()
                        webhook_url = webhook_info.get("result", {}).get("url") if webhook_info else None
                        if not webhook_url:
                            logger.info(f"Webhook removido após erro 409 (tentativa {i+1}). Aguardando mais 3 segundos para propagação...")
                            await asyncio.sleep(3)  # Aguardar mais 3 segundos para garantir propagação
                            break
                        else:
                            logger.warning(f"Webhook ainda configurado após tentativa {i+1} (URL: {webhook_url}), tentando novamente...")
                    else:
                        logger.error("Não foi possível remover webhook após 5 tentativas! Polling pode não funcionar.")
                except Exception as e2:
                    logger.error(f"Erro ao remover webhook após 409: {e2}")
            else:
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
