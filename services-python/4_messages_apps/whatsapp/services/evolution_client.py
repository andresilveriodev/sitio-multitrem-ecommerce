"""
Cliente HTTP mínimo para enviar mensagens via Evolution API.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

import httpx
import structlog

from config import settings

logger = structlog.get_logger(__name__)


def normalize_number(value: str) -> str:
    """Retorna só dígitos (Evolution aceita 55DDDNUMERO)."""
    return re.sub(r"\D", "", value or "")


class EvolutionClient:
    """Encaminha texto para Evolution sendText."""

    def __init__(self) -> None:
        self.base_url = (settings.EVOLUTION_API_URL or "").rstrip("/")
        self.api_key = (settings.EVOLUTION_API_KEY or "").strip()
        self.instance = (settings.EVOLUTION_INSTANCE_NAME or "").strip()
        self.timeout = settings.EVOLUTION_SEND_TIMEOUT
        self.client: Optional[httpx.AsyncClient] = None

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.instance)

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

    async def send_text(self, number: str, text: str) -> Dict[str, Any]:
        if not self.configured:
            return {
                "success": False,
                "error": "Evolution API não configurada (URL/KEY/INSTANCE)",
            }
        digits = normalize_number(number)
        message = (text or "").strip()
        if not digits or len(digits) < 10:
            return {"success": False, "error": "Número inválido", "number": number}
        if not message:
            return {"success": False, "error": "Texto vazio", "number": digits}

        url = f"{self.base_url}/message/sendText/{self.instance}"
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"number": digits, "text": message}

        try:
            client = await self._get_client()
            logger.info(
                "Enviando WhatsApp via Evolution",
                number=digits[-4:].rjust(len(digits), "*") if len(digits) > 4 else "****",
                chars=len(message),
            )
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json() if response.content else {}
            return {"success": True, "number": digits, "result": data}
        except httpx.HTTPError as e:
            logger.error("Falha Evolution sendText", error=str(e), number=digits)
            return {"success": False, "number": digits, "error": str(e)}
        except Exception as e:
            logger.error(
                "Erro inesperado Evolution sendText",
                error=str(e),
                number=digits,
                exc_info=True,
            )
            return {"success": False, "number": digits, "error": str(e)}
