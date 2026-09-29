"""
Router de debug: listar mensagens salvas por usuário no PostgreSQL (conversation_messages).
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func

from models.conversation_message_model import ConversationMessage
from services.database_service import database_service

router = APIRouter(prefix="/debug/messages", tags=["debug-messages"])

# GMT-3 para exibição
TZ_BRASILIA = timezone(timedelta(hours=-3))


def _format_ts_brasilia(dt: Optional[datetime]) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ_BRASILIA).strftime("%Y-%m-%d %H:%M:%S (GMT-3)")


def _html_path() -> Path:
    return Path(__file__).resolve().parent.parent / "static" / "messages_debug.html"


@router.get("", response_class=HTMLResponse)
async def messages_debug_page():
    """Página HTML simples para exibir mensagens salvas por usuário."""
    path = _html_path()
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {path}")
    return path.read_text(encoding="utf-8")


@router.get("/api/users")
async def list_users_with_messages():
    """Lista user_ids que têm mensagens no banco, com contagem e última mensagem."""
    if not database_service.is_connected:
        raise HTTPException(status_code=503, detail="Banco de dados não conectado")
    try:
        async with database_service.get_session() as session:
            # user_id, count, max(created_at)
            q = (
                select(
                    ConversationMessage.user_id,
                    func.count(ConversationMessage.id).label("count"),
                    func.max(ConversationMessage.created_at).label("last_at"),
                )
                .group_by(ConversationMessage.user_id)
                .order_by(func.max(ConversationMessage.created_at).desc())
            )
            result = await session.execute(q)
            rows = result.all()
            return [
                {
                    "user_id": r.user_id,
                    "message_count": r.count,
                    "last_at": _format_ts_brasilia(r.last_at),
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/users/{user_id}")
async def get_messages_by_user(user_id: str, limit: int = 100):
    """Retorna as últimas mensagens do usuário (do banco)."""
    if not database_service.is_connected:
        raise HTTPException(status_code=503, detail="Banco de dados não conectado")
    try:
        async with database_service.get_session() as session:
            q = (
                select(ConversationMessage)
                .where(ConversationMessage.user_id == user_id)
                .order_by(ConversationMessage.created_at.asc())
                .limit(limit)
            )
            result = await session.execute(q)
            rows = result.scalars().all()
            return [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "content": r.content or "",
                    "message_type": r.message_type,
                    "created_at": _format_ts_brasilia(r.created_at),
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
