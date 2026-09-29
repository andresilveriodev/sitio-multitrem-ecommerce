"""
Chat do cadastro na tela de operação. Sem Keycloak nesta etapa.
"""

import sys
from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.cadastro_chat import interpret_cadastro

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/chatbot/cadastro", tags=["cadastro-chat"])


class CadastroChatIn(BaseModel):
    message: str = Field(..., min_length=1)
    tela: str = "clientes"
    clientes: List[Dict[str, Any]] = Field(default_factory=list)
    produtos: List[str] = Field(default_factory=list)
    listas: List[str] = Field(default_factory=list)


def _log(message: str) -> None:
    print(f"[cadastro-chat] {message}", file=sys.stderr, flush=True)
    logger.info(message)


@router.post("/interpret")
async def interpret(body: CadastroChatIn, request: Request):
    text = body.message.strip()
    origin = request.headers.get("origin") or "-"
    _log(f"POST /interpret origin={origin} tela={body.tela} chars={len(text)}")
    if not text:
        raise HTTPException(status_code=400, detail="Escreva o que quer alterar")
    try:
        result = await interpret_cadastro(text, body.clientes, body.produtos)
    except ValueError as exc:
        _log(f"comando ilegível: {exc}")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        _log(f"AI Service falhou: {exc}")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        _log(f"erro inesperado: {exc}")
        logger.exception("erro no chat do cadastro")
        raise HTTPException(status_code=502, detail=f"Falha ao ler o comando: {exc}") from exc
    _log(f"ok acoes={len(result['acoes'])}")
    return result
