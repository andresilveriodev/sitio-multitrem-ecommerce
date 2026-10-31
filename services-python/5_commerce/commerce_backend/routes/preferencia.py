"""
Última tela do operador.

Uma linha por pessoa. Sem login nesta tela, a linha é a da operação.
Quando o login entrar, a mesma tabela guarda a tela de cada usuário.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from db_session import get_db_session

router = APIRouter(prefix="/cadastro/preferencia", tags=["preferencia"])

TELAS = {"pedidos", "clientes", "tabelas", "contas", "funil", "colaboradores", "contexto"}
OPERADOR = "operacao"


class PreferenciaIn(BaseModel):
    usuario: str = ""
    tela: str = "pedidos"
    chat_aberto: bool = True
    ferramentas_abertas: bool = False


def _usuario(valor: str) -> str:
    texto = " ".join((valor or "").split())[:80]
    return texto or OPERADOR


def _ensure(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commerce.preferencia_operador (
                usuario TEXT PRIMARY KEY,
                tela TEXT NOT NULL,
                chat_aberto BOOLEAN NOT NULL DEFAULT TRUE,
                ferramentas_abertas BOOLEAN NOT NULL DEFAULT FALSE,
                atualizada_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )
    db.commit()


def _ler(db: Session, usuario: str) -> dict:
    row = db.execute(
        text(
            """
            SELECT usuario, tela, chat_aberto, ferramentas_abertas
            FROM commerce.preferencia_operador
            WHERE usuario = :usuario
            """
        ),
        {"usuario": usuario},
    ).mappings().first()
    if not row:
        return {
            "usuario": usuario,
            "tela": "pedidos",
            "chat_aberto": True,
            "ferramentas_abertas": False,
        }
    tela = row["tela"] if row["tela"] in TELAS else "pedidos"
    return {
        "usuario": row["usuario"],
        "tela": tela,
        "chat_aberto": bool(row["chat_aberto"]),
        "ferramentas_abertas": bool(row["ferramentas_abertas"]),
    }


@router.get("")
def ler_preferencia(usuario: str = "", db: Session = Depends(get_db_session)):
    _ensure(db)
    return _ler(db, _usuario(usuario))


@router.put("")
def gravar_preferencia(body: PreferenciaIn, db: Session = Depends(get_db_session)):
    if body.tela not in TELAS:
        raise HTTPException(status_code=422, detail="Tela desconhecida")
    _ensure(db)
    usuario = _usuario(body.usuario)
    db.execute(
        text(
            """
            INSERT INTO commerce.preferencia_operador
                (usuario, tela, chat_aberto, ferramentas_abertas)
            VALUES (:usuario, :tela, :chat_aberto, :ferramentas_abertas)
            ON CONFLICT (usuario) DO UPDATE SET
                tela = EXCLUDED.tela,
                chat_aberto = EXCLUDED.chat_aberto,
                ferramentas_abertas = EXCLUDED.ferramentas_abertas,
                atualizada_em = NOW()
            """
        ),
        {
            "usuario": usuario,
            "tela": body.tela,
            "chat_aberto": body.chat_aberto,
            "ferramentas_abertas": body.ferramentas_abertas,
        },
    )
    db.commit()
    return _ler(db, usuario)
