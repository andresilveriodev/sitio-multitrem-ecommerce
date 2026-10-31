"""
Cliente HTTP mínimo para encaminhar mensagens ao Chatbot Service (canal WhatsApp).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
import structlog

from config import settings

logger = structlog.get_logger(__name__)


class ChatbotClient:
    """Encaminha payload WhatsApp ao endpoint dedicado; sem lógica de negócio."""

    def __init__(self) -> None:
        self.base_url = settings.CHATBOT_SERVICE_URL.rstrip("/")
        self.timeout = settings.CHATBOT_SERVICE_TIMEOUT
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=self.timeout,
                    write=10.0,
                    pool=10.0,
                )
            )
        return self.client

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None

    async def process_message(
        self,
        user_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """POST /chatbot/whatsapp — contrato próprio do canal."""
        url = f"{self.base_url}/chatbot/whatsapp"
        meta = metadata or {}
        payload: Dict[str, Any] = {
            "channel": "whatsapp",
            "user_id": user_id,
            "message": message,
            "message_id": meta.get("message_id"),
            "instance": meta.get("instance"),
            "remote_jid": meta.get("remote_jid"),
            "push_name": meta.get("push_name"),
            "raw_event_type": meta.get("raw_event_type"),
        }

        try:
            client = await self._get_client()
            logger.info(
                "Encaminhando ao chatbot (whatsapp)",
                user_id=user_id,
                message_preview=message[:50],
                url=url,
            )
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(
                "Chatbot respondeu (whatsapp)",
                user_id=user_id,
                success=result.get("success"),
            )
            return result
        except httpx.HTTPError as e:
            logger.error("Falha ao chamar chatbot", error=str(e), user_id=user_id)
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(
                "Erro inesperado no forward chatbot",
                error=str(e),
                user_id=user_id,
                exc_info=True,
            )
            return {"success": False, "error": str(e)}
