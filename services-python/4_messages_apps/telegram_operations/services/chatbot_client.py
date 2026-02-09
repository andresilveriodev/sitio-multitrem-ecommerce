"""
Cliente para comunicação com o Chatbot Service
"""

import httpx
import structlog
from typing import Optional, Dict, Any
from config import settings

logger = structlog.get_logger(__name__)


class ChatbotClient:
    """Cliente para chamar o Chatbot Service"""
    
    def __init__(self):
        self.base_url = settings.CHATBOT_SERVICE_URL
        self.timeout = settings.CHATBOT_SERVICE_TIMEOUT
        self.client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtém ou cria cliente HTTP"""
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=self.timeout,
                    write=10.0,
                    pool=10.0
                )
            )
        return self.client
    
    async def close(self):
        """Fecha cliente HTTP"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Processa mensagem através do Chatbot Service
        
        Args:
            user_id: ID do usuário
            message: Texto da mensagem
            session_id: ID da sessão (opcional)
            metadata: Metadados adicionais (opcional)
            credentials: Credenciais do usuário autenticado (opcional)
            
        Returns:
            Resposta do chatbot service
        """
        try:
            client = await self._get_client()
            url = f"{self.base_url}/chatbot/process-message"
            
            payload = {
                "user_id": user_id,
                "message": message,
                "content_type": "text/plain"
            }
            
            if session_id:
                payload["session_id"] = session_id
            
            if metadata:
                # Adicionar metadata ao contexto se necessário
                payload["context"] = metadata
            
            # Preparar headers com token JWT se disponível
            headers = {}
            if credentials and credentials.get("is_authenticated"):
                # Se tiver token JWT, adicionar ao header Authorization
                token = credentials.get("token")
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                # Também enviar informações do usuário no payload
                payload["authenticated_user"] = {
                    "user_id": credentials.get("user_id"),
                    "email": credentials.get("email"),
                    "keycloak_id": credentials.get("keycloak_id"),
                    "permissions": credentials.get("permissions", []),
                    "profiles": credentials.get("profiles", [])
                }
            
            logger.info(
                "Enviando mensagem para chatbot",
                user_id=user_id,
                message_preview=message[:50],
                is_authenticated=credentials is not None and credentials.get("is_authenticated", False) if credentials else False
            )
            
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(
                "Resposta recebida do chatbot",
                user_id=user_id,
                success=result.get("success")
            )
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao chamar chatbot: {e}")
            return {
                "success": False,
                "error": f"Erro de comunicação com chatbot: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Erro ao processar mensagem no chatbot: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Erro ao processar mensagem: {str(e)}"
            }
