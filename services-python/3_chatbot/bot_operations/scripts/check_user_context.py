#!/usr/bin/env python3
"""
Verifica mensagens salvas no histórico de um usuário.
Prioridade: PostgreSQL (permanente), depois Redis (cache).
Horário exibido em GMT-3 (Brasília/São Paulo).
Uso: python scripts/check_user_context.py [user_id]
Exemplo: python scripts/check_user_context.py 178999227
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from zoneinfo import ZoneInfo
    TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")  # GMT-3
except ImportError:
    TZ_BRASILIA = timezone(timedelta(hours=-3))  # GMT-3 (Python 3.8)

from services.context_service import context_service
from models.conversation_context import MessageType


def _format_ts_brasilia(ts) -> str:
    """Formata timestamp em horário de Brasília (GMT-3)."""
    if ts is None:
        return ""
    if hasattr(ts, "astimezone"):
        dt = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(TZ_BRASILIA)
        return dt.strftime("%Y-%m-%d %H:%M:%S (GMT-3)")
    return str(ts)


async def main():
    user_id = (sys.argv[1] or "178999227").strip()
    print(f"Consultando histórico do usuário: {user_id}")
    print("Horário exibido: GMT-3 (Brasília/São Paulo)")
    print("Conectando ao Redis...")
    await context_service.connect()
    # Conectar DB se disponível (para mostrar mensagens permanentes)
    try:
        from services.database_service import database_service
        await database_service.connect()
        print("PostgreSQL conectado (histórico permanente).")
    except Exception as e:
        print(f"PostgreSQL não disponível: {e}. Usando apenas Redis.")
    try:
        ctx = await context_service.get_conversation_context(user_id)
        history = ctx.message_history or []
        print(f"\nTotal de mensagens no histórico: {len(history)}")
        if not history:
            print("Nenhuma mensagem salva para este usuário.")
            return
        print("\n--- Últimas mensagens (mais recentes por último) ---\n")
        for i, m in enumerate(history[-30:], 1):  # últimas 30
            role = "Usuário" if m.message_type == MessageType.USER else "Bot"
            ts_str = _format_ts_brasilia(m.timestamp)
            content = (m.content or "")[:500]
            if len((m.content or "")) > 500:
                content += "..."
            print(f"{i}. [{role}] {ts_str}")
            print(f"   {content}")
            print()
    finally:
        await context_service.disconnect()
        try:
            from services.database_service import database_service
            await database_service.disconnect()
        except Exception:
            pass
    print("Fim.")


if __name__ == "__main__":
    asyncio.run(main())
