"""
Cadastro de colaboradores da empresa.
Uma pessoa pode ter várias funções (dono, colheiteiro, entregador, granjeiro…).
"""

from __future__ import annotations

import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db_session import get_db_session
from models.commerce import Collaborator

router = APIRouter(prefix="/cadastro/colaboradores", tags=["colaboradores"])

# Funções conhecidas do sítio (várias por pessoa)
FUNCOES = (
    "dono",
    "funcionario",
    "entregador",
    "colheiteiro",
    "granjeiro",
    "separador_pedidos",
    "fornecedor",
)

# Compat: aliases → canônico
ALIASES = {
    "dona": "dono",
    "proprietario": "dono",
    "proprietaria": "dono",
    "funcionaria": "funcionario",
    "entregadora": "entregador",
    "motoqueiro": "entregador",
    "motoqueira": "entregador",
    "colheita": "colheiteiro",
    "colheiteira": "colheiteiro",
    "granjeira": "granjeiro",
    "separador": "separador_pedidos",
    "separadorpedidos": "separador_pedidos",
    "separadordepedidos": "separador_pedidos",
    "fornecedora": "fornecedor",
}


class ColaboradorIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    phone_e164: str = Field(..., min_length=8, max_length=20)
    roles: List[str] = Field(default_factory=list)
    # compat com clientes antigos
    role: Optional[str] = None
    endereco: Optional[str] = None
    localizacao: Optional[str] = None
    active: bool = True
    notes: Optional[str] = None


class ColaboradorOut(BaseModel):
    id: int
    name: str
    phone_e164: str
    roles: List[str]
    role: str  # primeira função (compat)
    endereco: Optional[str] = None
    localizacao: Optional[str] = None
    active: bool
    notes: Optional[str] = None


def _ensure(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commerce.collaborator (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                phone_e164 VARCHAR(20) NOT NULL UNIQUE,
                role VARCHAR(200) NOT NULL DEFAULT 'funcionario',
                address VARCHAR(300),
                location_url VARCHAR(500),
                active BOOLEAN NOT NULL DEFAULT TRUE,
                notes TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )
    db.execute(
        text(
            "ALTER TABLE commerce.collaborator ADD COLUMN IF NOT EXISTS address VARCHAR(300)"
        )
    )
    db.execute(
        text(
            "ALTER TABLE commerce.collaborator ADD COLUMN IF NOT EXISTS location_url VARCHAR(500)"
        )
    )
    db.execute(
        text(
            "ALTER TABLE commerce.collaborator ALTER COLUMN role TYPE VARCHAR(200)"
        )
    )
    db.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_collaborator_role ON commerce.collaborator (role)"
        )
    )
    db.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_collaborator_phone ON commerce.collaborator (phone_e164)"
        )
    )
    db.commit()


def _phone(value: Optional[str]) -> Optional[str]:
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return None
    if digits.startswith("55") and len(digits) >= 12:
        return f"+{digits}"[:20]
    if len(digits) >= 10:
        return f"+55{digits}"[:20]
    return None


def _canon(value: str) -> Optional[str]:
    chave = re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())
    if not chave:
        return None
    if chave in ALIASES:
        return ALIASES[chave]
    if chave in FUNCOES:
        return chave
    return None


def _roles_from_storage(raw: Optional[str]) -> List[str]:
    partes = [p.strip() for p in (raw or "").split(",") if p.strip()]
    vistos: List[str] = []
    for parte in partes:
        canon = _canon(parte) or (parte if parte in FUNCOES else None)
        if canon and canon not in vistos:
            vistos.append(canon)
    return vistos


def _normalize_roles(body: ColaboradorIn) -> List[str]:
    bruto = list(body.roles or [])
    if body.role:
        bruto.append(body.role)
    if not bruto:
        raise HTTPException(
            status_code=422,
            detail=f"Informe ao menos uma função. Use: {', '.join(FUNCOES)}",
        )
    vistos: List[str] = []
    invalidos: List[str] = []
    for item in bruto:
        for pedaco in str(item).split(","):
            canon = _canon(pedaco)
            if not canon:
                if pedaco.strip():
                    invalidos.append(pedaco.strip())
                continue
            if canon not in vistos:
                vistos.append(canon)
    if invalidos:
        raise HTTPException(
            status_code=422,
            detail=f"Função inválida: {', '.join(invalidos)}. Use: {', '.join(FUNCOES)}",
        )
    if not vistos:
        raise HTTPException(
            status_code=422,
            detail=f"Informe ao menos uma função. Use: {', '.join(FUNCOES)}",
        )
    return vistos


def _store_roles(roles: List[str]) -> str:
    return ",".join(roles)[:200]


def _texto(value: Optional[str], limite: int) -> Optional[str]:
    texto = " ".join((value or "").split())
    return texto[:limite] if texto else None


def _out(row: Collaborator) -> dict:
    roles = _roles_from_storage(row.role)
    return {
        "id": row.id,
        "name": row.name,
        "phone_e164": row.phone_e164,
        "roles": roles,
        "role": roles[0] if roles else "funcionario",
        "endereco": row.address,
        "localizacao": row.location_url,
        "active": bool(row.active),
        "notes": row.notes,
    }


def _tem_funcao(row: Collaborator, funcao: str) -> bool:
    return funcao in _roles_from_storage(row.role)


@router.get("/funcoes")
def listar_funcoes():
    """Catálogo de funções + quem está em cada uma (para tarefas / WhatsApp)."""
    return {"funcoes": list(FUNCOES)}


@router.get("/por-funcao")
def por_funcao(
    ativos: bool = Query(default=True),
    db: Session = Depends(get_db_session),
):
    """
    Agrupa colaboradores por função.
    Útil na hora da tarefa: ver o nome de quem está na função para enviar WhatsApp.
    """
    _ensure(db)
    query = db.query(Collaborator)
    if ativos:
        query = query.filter(Collaborator.active.is_(True))
    rows = query.order_by(Collaborator.name.asc()).all()
    grupos: dict[str, list[dict]] = {f: [] for f in FUNCOES}
    for row in rows:
        pessoa = {
            "id": row.id,
            "name": row.name,
            "phone_e164": row.phone_e164,
            "roles": _roles_from_storage(row.role),
        }
        for funcao in _roles_from_storage(row.role):
            if funcao in grupos:
                grupos[funcao].append(pessoa)
    return {
        "funcoes": [
            {
                "role": funcao,
                "pessoas": grupos[funcao],
            }
            for funcao in FUNCOES
        ]
    }


@router.get("", response_model=List[ColaboradorOut])
def listar(
    q: str = "",
    role: str = "",
    ativos: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db_session),
):
    _ensure(db)
    query = db.query(Collaborator)
    if ativos is True:
        query = query.filter(Collaborator.active.is_(True))
    elif ativos is False:
        query = query.filter(Collaborator.active.is_(False))
    papel = _canon(role) if role else None
    if role and not papel:
        raise HTTPException(status_code=422, detail="Função inválida")
    termo = " ".join((q or "").split())
    if termo:
        like = f"%{termo}%"
        query = query.filter(
            or_(
                Collaborator.name.ilike(like),
                Collaborator.phone_e164.ilike(like),
                Collaborator.address.ilike(like),
            )
        )
    rows = query.order_by(Collaborator.active.desc(), Collaborator.name.asc()).all()
    if papel:
        rows = [row for row in rows if _tem_funcao(row, papel)]
    return [_out(row) for row in rows]


@router.post("", response_model=ColaboradorOut, status_code=201)
def criar(body: ColaboradorIn, db: Session = Depends(get_db_session)):
    _ensure(db)
    nome = " ".join((body.name or "").split())
    telefone = _phone(body.phone_e164)
    if not nome:
        raise HTTPException(status_code=422, detail="Nome é obrigatório")
    if not telefone:
        raise HTTPException(status_code=422, detail="WhatsApp inválido")
    roles = _normalize_roles(body)
    row = Collaborator(
        name=nome[:200],
        phone_e164=telefone,
        role=_store_roles(roles),
        address=_texto(body.endereco, 300),
        location_url=_texto(body.localizacao, 500),
        active=bool(body.active),
        notes=_texto(body.notes, 2000),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe colaborador com este WhatsApp")
    db.refresh(row)
    return _out(row)


@router.put("/{colaborador_id}", response_model=ColaboradorOut)
def atualizar(
    colaborador_id: int,
    body: ColaboradorIn,
    db: Session = Depends(get_db_session),
):
    _ensure(db)
    row = db.query(Collaborator).filter(Collaborator.id == colaborador_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    nome = " ".join((body.name or "").split())
    telefone = _phone(body.phone_e164)
    if not nome:
        raise HTTPException(status_code=422, detail="Nome é obrigatório")
    if not telefone:
        raise HTTPException(status_code=422, detail="WhatsApp inválido")
    roles = _normalize_roles(body)
    row.name = nome[:200]
    row.phone_e164 = telefone
    row.role = _store_roles(roles)
    row.address = _texto(body.endereco, 300)
    row.location_url = _texto(body.localizacao, 500)
    row.active = bool(body.active)
    row.notes = _texto(body.notes, 2000)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe colaborador com este WhatsApp")
    db.refresh(row)
    return _out(row)


@router.post("/{colaborador_id}/inativar")
def inativar(colaborador_id: int, db: Session = Depends(get_db_session)):
    """Marca o colaborador como inativo (mantém o cadastro)."""
    _ensure(db)
    row = db.query(Collaborator).filter(Collaborator.id == colaborador_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    row.active = False
    db.commit()
    return {"ok": True, "id": colaborador_id, "active": False}


@router.delete("/{colaborador_id}")
def excluir(colaborador_id: int, db: Session = Depends(get_db_session)):
    """Remove o colaborador do cadastro."""
    _ensure(db)
    row = db.query(Collaborator).filter(Collaborator.id == colaborador_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    db.delete(row)
    db.commit()
    return {"ok": True, "id": colaborador_id, "deleted": True}
