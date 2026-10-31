"""
Histórico do painel de pedidos.

Cada fala do operador e cada resposta do sistema fica gravada.
Limpar a conversa só tira o texto da tela; o registro continua para consulta.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db_session import get_db_session

router = APIRouter(prefix="/cadastro/conversas", tags=["conversas"])

LIMITE_TEXTO = 50000


class MensagemIn(BaseModel):
    painel: str = "venda"
    papel: str
    texto: str = Field(min_length=1)


class MensagemOut(BaseModel):
    id: int
    papel: str
    texto: str
    criada_em: str


class ConversaOut(BaseModel):
    id: int
    painel: str
    iniciada_em: str
    encerrada_em: Optional[str] = None
    mensagens: List[MensagemOut] = Field(default_factory=list)


def _painel(valor: str) -> str:
    if valor == "compra":
        return "compra"
    if valor == "venda":
        return "venda"
    raise HTTPException(status_code=400, detail="Painel inválido.")


def _papel(valor: str) -> str:
    if valor in ("voce", "bot"):
        return valor
    raise HTTPException(status_code=400, detail="Papel inválido.")


def _iso(valor) -> str:
    if isinstance(valor, datetime):
        return valor.isoformat()
    return "" if valor is None else str(valor)


def _ensure(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commerce.conversa_painel (
                id BIGSERIAL PRIMARY KEY,
                painel VARCHAR(20) NOT NULL,
                iniciada_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                encerrada_em TIMESTAMPTZ
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commerce.conversa_mensagem (
                id BIGSERIAL PRIMARY KEY,
                conversa_id BIGINT NOT NULL REFERENCES commerce.conversa_painel(id),
                papel VARCHAR(10) NOT NULL,
                texto TEXT NOT NULL,
                criada_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )
    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS conversa_mensagem_conversa_idx
            ON commerce.conversa_mensagem (conversa_id, id)
            """
        )
    )
    db.execute(
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS conversa_painel_uma_aberta
            ON commerce.conversa_painel (painel)
            WHERE encerrada_em IS NULL
            """
        )
    )
    db.commit()


def _aberta(db: Session, painel: str) -> Optional[int]:
    row = db.execute(
        text(
            """
            SELECT id FROM commerce.conversa_painel
            WHERE painel = :painel AND encerrada_em IS NULL
            ORDER BY id DESC
            LIMIT 1
            """
        ),
        {"painel": painel},
    ).first()
    return int(row[0]) if row else None


def _abrir(db: Session, painel: str) -> int:
    existente = _aberta(db, painel)
    if existente:
        return existente
    try:
        novo = db.execute(
            text(
                """
                INSERT INTO commerce.conversa_painel (painel)
                VALUES (:painel)
                RETURNING id
                """
            ),
            {"painel": painel},
        ).first()
        return int(novo[0])
    except IntegrityError:
        db.rollback()
        existente = _aberta(db, painel)
        if existente:
            return existente
        raise HTTPException(status_code=500, detail="Não consegui abrir a conversa.") from None


def _mensagens(db: Session, conversa_id: int) -> List[dict]:
    rows = db.execute(
        text(
            """
            SELECT id, papel, texto, criada_em
            FROM commerce.conversa_mensagem
            WHERE conversa_id = :id
            ORDER BY id ASC
            """
        ),
        {"id": conversa_id},
    ).mappings()
    return [
        {
            "id": row["id"],
            "papel": row["papel"],
            "texto": row["texto"],
            "criada_em": _iso(row["criada_em"]),
        }
        for row in rows
    ]


def _conversa(db: Session, conversa_id: int, painel: str) -> dict:
    row = db.execute(
        text(
            """
            SELECT id, painel, iniciada_em, encerrada_em
            FROM commerce.conversa_painel
            WHERE id = :id
            """
        ),
        {"id": conversa_id},
    ).mappings().first()
    if not row:
        return {"id": 0, "painel": painel, "iniciada_em": "", "encerrada_em": None, "mensagens": []}
    return {
        "id": row["id"],
        "painel": row["painel"],
        "iniciada_em": _iso(row["iniciada_em"]),
        "encerrada_em": _iso(row["encerrada_em"]) if row["encerrada_em"] else None,
        "mensagens": _mensagens(db, conversa_id),
    }


@router.get("/atual", response_model=ConversaOut)
def conversa_atual(painel: str = Query("venda"), db: Session = Depends(get_db_session)):
    """Conversa que está na tela. Não apaga nada se ainda não houver fala."""
    qual = _painel(painel)
    _ensure(db)
    aberta = _aberta(db, qual)
    if not aberta:
        return {"id": 0, "painel": qual, "iniciada_em": "", "encerrada_em": None, "mensagens": []}
    return _conversa(db, aberta, qual)


@router.get("", response_model=List[ConversaOut])
def listar_conversas(painel: str = Query("venda"), db: Session = Depends(get_db_session)):
    """Conversas gravadas, da mais recente para a mais antiga, inclusive as já tiradas da tela."""
    qual = _painel(painel)
    _ensure(db)
    rows = db.execute(
        text(
            """
            SELECT c.id AS conversa_id, c.painel, c.iniciada_em, c.encerrada_em,
                   m.id AS mensagem_id, m.papel, m.texto, m.criada_em
            FROM (
                SELECT id, painel, iniciada_em, encerrada_em
                FROM commerce.conversa_painel
                WHERE painel = :painel
                  AND EXISTS (
                      SELECT 1 FROM commerce.conversa_mensagem mensagem
                      WHERE mensagem.conversa_id = conversa_painel.id
                  )
                ORDER BY id DESC
                LIMIT 40
            ) c
            JOIN commerce.conversa_mensagem m ON m.conversa_id = c.id
            ORDER BY c.id DESC, m.id ASC
            """
        ),
        {"painel": qual},
    ).mappings()
    grupos: List[dict] = []
    indice: dict = {}
    for row in rows:
        chave = row["conversa_id"]
        if chave not in indice:
            indice[chave] = {
                "id": chave,
                "painel": row["painel"],
                "iniciada_em": _iso(row["iniciada_em"]),
                "encerrada_em": _iso(row["encerrada_em"]) if row["encerrada_em"] else None,
                "mensagens": [],
            }
            grupos.append(indice[chave])
        indice[chave]["mensagens"].append(
            {
                "id": row["mensagem_id"],
                "papel": row["papel"],
                "texto": row["texto"],
                "criada_em": _iso(row["criada_em"]),
            }
        )
    return grupos


@router.post("/mensagens", response_model=MensagemOut)
def gravar_mensagem(dados: MensagemIn, db: Session = Depends(get_db_session)):
    """Grava uma fala. A conversa aberta é reaproveitada; se não houver, abre outra."""
    qual = _painel(dados.painel)
    papel = _papel(dados.papel)
    texto = dados.texto.strip()
    if not texto:
        raise HTTPException(status_code=400, detail="A mensagem está vazia.")
    if len(texto) > LIMITE_TEXTO:
        raise HTTPException(status_code=400, detail="A mensagem passou do tamanho que o histórico guarda.")
    _ensure(db)
    conversa_id = _abrir(db, qual)
    row = db.execute(
        text(
            """
            INSERT INTO commerce.conversa_mensagem (conversa_id, papel, texto)
            VALUES (:conversa_id, :papel, :texto)
            RETURNING id, papel, texto, criada_em
            """
        ),
        {"conversa_id": conversa_id, "papel": papel, "texto": texto},
    ).mappings().first()
    db.commit()
    return {
        "id": row["id"],
        "papel": row["papel"],
        "texto": row["texto"],
        "criada_em": _iso(row["criada_em"]),
    }


@router.post("/limpar", response_model=ConversaOut)
def limpar_tela(painel: str = Query("venda"), db: Session = Depends(get_db_session)):
    """Encerra a conversa da tela. As mensagens permanecem para o histórico."""
    qual = _painel(painel)
    _ensure(db)
    aberta = _aberta(db, qual)
    if aberta:
        tem = db.execute(
            text("SELECT 1 FROM commerce.conversa_mensagem WHERE conversa_id = :id LIMIT 1"),
            {"id": aberta},
        ).first()
        if tem:
            db.execute(
                text("UPDATE commerce.conversa_painel SET encerrada_em = NOW() WHERE id = :id AND encerrada_em IS NULL"),
                {"id": aberta},
            )
    db.commit()
    return {"id": 0, "painel": qual, "iniciada_em": "", "encerrada_em": None, "mensagens": []}
