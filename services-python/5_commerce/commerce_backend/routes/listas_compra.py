"""
Lista de compras tirada da colheita.

Guarda o que foi marcado para comprar e o texto da mensagem.
A consulta devolve a lista mais recente do mesmo período.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db_session import get_db_session

router = APIRouter(prefix="/cadastro/listas-compra", tags=["listas-compra"])


class ItemIn(BaseModel):
    produto: str = ""
    qtd: float = 0


class ListaIn(BaseModel):
    periodo: str = ""
    texto: str = ""
    itens: List[ItemIn] = Field(default_factory=list)


class ItemOut(BaseModel):
    produto: str
    qtd: float


class ListaOut(BaseModel):
    id: int
    periodo: str
    texto: str
    criada_em: str
    itens: List[ItemOut]


def _iso(valor) -> str:
    if isinstance(valor, datetime):
        return valor.isoformat()
    return "" if valor is None else str(valor)


def _ensure(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commerce.lista_compra (
                id BIGSERIAL PRIMARY KEY,
                periodo TEXT NOT NULL,
                texto TEXT NOT NULL,
                criada_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commerce.lista_compra_item (
                id BIGSERIAL PRIMARY KEY,
                lista_id BIGINT NOT NULL REFERENCES commerce.lista_compra(id) ON DELETE CASCADE,
                produto TEXT NOT NULL,
                qtd NUMERIC(12, 3) NOT NULL
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS lista_compra_periodo_idx
            ON commerce.lista_compra (periodo, id)
            """
        )
    )
    db.commit()


def _itens(db: Session, lista_id: int) -> List[dict]:
    rows = db.execute(
        text(
            """
            SELECT produto, qtd
            FROM commerce.lista_compra_item
            WHERE lista_id = :id
            ORDER BY id
            """
        ),
        {"id": lista_id},
    ).mappings()
    return [{"produto": row["produto"], "qtd": float(row["qtd"])} for row in rows]


def _saida(row, itens: List[dict]) -> dict:
    return {
        "id": row["id"],
        "periodo": row["periodo"],
        "texto": row["texto"],
        "criada_em": _iso(row["criada_em"]),
        "itens": itens,
    }


@router.get("", response_model=ListaOut)
def atual(periodo: str = Query(""), db: Session = Depends(get_db_session)):
    """A lista salva mais recente deste período da colheita."""
    qual = periodo.strip()
    if not qual:
        raise HTTPException(status_code=404, detail="Não há lista de compras salva.")
    _ensure(db)
    row = db.execute(
        text(
            """
            SELECT id, periodo, texto, criada_em
            FROM commerce.lista_compra
            WHERE periodo = :periodo
            ORDER BY id DESC
            LIMIT 1
            """
        ),
        {"periodo": qual},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Não há lista de compras salva.")
    return _saida(row, _itens(db, row["id"]))


@router.post("", response_model=ListaOut)
def gravar(dados: ListaIn, db: Session = Depends(get_db_session)):
    """Grava a lista de compras e o texto da mensagem."""
    periodo = dados.periodo.strip()
    texto = dados.texto.strip()
    itens = [item for item in dados.itens if item.produto.strip() and item.qtd > 0]
    if not periodo:
        raise HTTPException(status_code=400, detail="A lista de compras precisa do período.")
    if not itens or not texto:
        raise HTTPException(status_code=400, detail="Informe ao menos um produto para comprar.")
    _ensure(db)
    row = db.execute(
        text(
            """
            INSERT INTO commerce.lista_compra (periodo, texto)
            VALUES (:periodo, :texto)
            RETURNING id, periodo, texto, criada_em
            """
        ),
        {"periodo": periodo, "texto": texto},
    ).mappings().first()
    for item in itens:
        db.execute(
            text(
                """
                INSERT INTO commerce.lista_compra_item (lista_id, produto, qtd)
                VALUES (:lista_id, :produto, :qtd)
                """
            ),
            {"lista_id": row["id"], "produto": item.produto.strip(), "qtd": item.qtd},
        )
    db.commit()
    return _saida(row, [{"produto": item.produto.strip(), "qtd": item.qtd} for item in itens])
