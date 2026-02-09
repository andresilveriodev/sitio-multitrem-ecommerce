"""
Serviço para interagir com a API do Telegram
"""

import httpx
import structlog
from typing import Optional, Dict, Any
from config import settings
from services.chatbot_client import ChatbotClient
from services.auth_service import telegram_auth_service

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
            
            # Extrair informações da mensagem
            chat_id = message.get("chat", {}).get("id")
            user_id = str(message.get("from", {}).get("id", ""))
            username = message.get("from", {}).get("username", "")
            text = message.get("text", "")
            message_id = message.get("message_id")
            
            if not text:
                # Pode ser foto, documento, etc. Por enquanto, ignoramos
                logger.info("Mensagem sem texto recebida", chat_id=chat_id, message_type=message.get("content_type"))
                return
            
            logger.info(
                "Mensagem recebida do Telegram",
                chat_id=chat_id,
                user_id=user_id,
                username=username,
                text_preview=text[:50]
            )
            
            # Enviar indicador de digitação
            await self.send_chat_action(chat_id=chat_id, action="typing")
            
            # Processar mensagem com o chatbot
            response_text = await self._process_message_with_chatbot(
                user_id=user_id,
                username=username,
                message=text,
                chat_id=chat_id
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
            logger.error(f"Erro ao processar atualização do Telegram: {e}", exc_info=True)
            # Tentar enviar mensagem de erro ao usuário
            try:
                chat_id = update_data.get("message", {}).get("chat", {}).get("id")
                if chat_id:
                    await self.send_message(
                        chat_id=chat_id,
                        text="❌ Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
                    )
            except:
                pass
    
    async def _process_callback_query(self, callback_query: Dict[str, Any]):
        """Processa callback query (botões inline)"""
        try:
            query_id = callback_query.get("id")
            chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
            data = callback_query.get("data")
            user_id = str(callback_query.get("from", {}).get("id", ""))
            
            logger.info("Callback query recebido", query_id=query_id, data=data)
            
            # Responder ao callback (obrigatório)
            await self.answer_callback_query(query_id=query_id, text="Processando...")
            
            # Processar com chatbot se houver dados
            if data:
                response_text = await self._process_message_with_chatbot(
                    user_id=user_id,
                    username=callback_query.get("from", {}).get("username", ""),
                    message=data,
                    chat_id=chat_id
                )
                
                if response_text:
                    await self.send_message(chat_id=chat_id, text=response_text)
                    
        except Exception as e:
            logger.error(f"Erro ao processar callback query: {e}", exc_info=True)
    
    async def _process_message_with_chatbot(
        self,
        user_id: str,
        username: str,
        message: str,
        chat_id: int
    ) -> Optional[str]:
        """
        Processa mensagem com o chatbot service
        
        Args:
            user_id: ID do usuário do Telegram
            username: Nome de usuário do Telegram
            message: Texto da mensagem
            chat_id: ID do chat do Telegram
            
        Returns:
            Texto da resposta do chatbot
        """
        try:
            # Verificar se usuário existe no e-commerce e obter credenciais
            credentials = await telegram_auth_service.get_user_credentials(
                telegram_user_id=user_id,
                username=username
            )
            
            # Criar user_id único combinando telegram_id e chat_id
            telegram_user_id = f"telegram_{user_id}_{chat_id}"
            
            # Preparar metadata com informações de autenticação
            metadata = {
                "telegram_user_id": user_id,
                "telegram_username": username,
                "telegram_chat_id": chat_id,
                "platform": "telegram",
                "is_authenticated": credentials is not None if credentials else False
            }
            
            # Adicionar informações do usuário autenticado se disponível
            if credentials:
                metadata.update({
                    "user_id": credentials.get("user_id"),
                    "email": credentials.get("email"),
                    "keycloak_id": credentials.get("keycloak_id"),
                    "permissions": credentials.get("permissions", []),
                    "profiles": credentials.get("profiles", [])
                })
            
            # Chamar chatbot service
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
                logger.warning(f"Erro no chatbot: {error}")
                
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
