"""
Grava a lista do dia como está na boleta e consulta o período do cliente.

O preço gravado é o da tela. Não passa pelo cálculo antigo de palito.
"""

import re
import unicodedata
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from db_session import get_db_session

router = APIRouter(prefix="/cadastro/boletas", tags=["boletas"])

CENTAVO = Decimal("0.01")


class ItemIn(BaseModel):
    produto: str = ""
    qtd: float = 0
    qtd_entregue: Optional[float] = None
    valor: float = 0
    desconto: float = 0
    desconto_percentual: float = 0
    qtd_reagendada: float = 0
    data_reagendada: str = ""
    reagenda_conduta: Optional[str] = None
    observacao: str = ""
    origem_id: Optional[str] = None


class PedidoIn(BaseModel):
    id: Optional[str] = None
    cliente_id: Optional[int] = None
    cliente: str = ""
    data: str = ""
    endereco: str = ""
    desconto: float = 0
    tabela: str = ""
    tipo: str = "venda"
    concluir: bool = False
    desconcluir: bool = False
    pago: bool = False
    observacao: str = ""
    itens: List[ItemIn] = Field(default_factory=list)


class LoteIn(BaseModel):
    pedidos: List[PedidoIn] = Field(default_factory=list)


def _fold(value: str) -> str:
    sem = unicodedata.normalize("NFKD", value or "")
    sem = "".join(ch for ch in sem if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", sem.casefold()).strip()


def _formato(value: str) -> str:
    texto = re.sub(r"\s+", " ", (value or "").strip())
    chave = _fold(texto)
    if chave in ("", "un", "und", "unidade"):
        return "unidade"
    if chave == "maco":
        return "maço"
    if chave in ("kg", "quilo", "quilos"):
        return "kg"
    if chave in ("peso fixo", "fixo"):
        return "peso fixo"
    return texto[:60]


def _rotulo(nome: str) -> tuple[str, str]:
    texto = re.sub(r"\s+", " ", (nome or "").strip())
    marcado = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", texto)
    if marcado and marcado.group(1).strip():
        return marcado.group(1).strip(), _formato(marcado.group(2))
    return texto, ""


def _centavos(value: float) -> Decimal:
    return Decimal(str(value)).quantize(CENTAVO)


def _data(texto: str, hoje: date) -> Optional[date]:
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", (texto or "").strip())
    if not match:
        return None
    dia, mes = int(match.group(1)), int(match.group(2))
    if not (1 <= dia <= 31 and 1 <= mes <= 12):
        return None
    if match.group(3):
        ano = int(match.group(3))
        if ano < 100:
            ano += 2000
    else:
        ano = hoje.year
    try:
        candidata = date(ano, mes, dia)
    except ValueError:
        return None
    if not match.group(3) and (hoje - candidata).days > 180:
        try:
            return date(hoje.year + 1, mes, dia)
        except ValueError:
            return None
    return candidata


def _dia(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _dia_do_pedido(db: Session, order_id) -> Optional[str]:
    if not order_id:
        return None
    row = db.execute(
        text('SELECT delivery_on FROM commerce."order" WHERE id = :id'),
        {"id": str(order_id)},
    ).first()
    if not row or not row[0]:
        return None
    return _dia(row[0])


def _datas_em_obs_reagendado(obs: Optional[str]) -> list:
    """Extrai datas de textos como 'Reagendado de 27/10/2026 e 30/10/2026'."""
    if not obs:
        return []
    match = re.search(r"reagendado\s+de\s+(.+?)(?:\s*[·\-–]\s*|\s*$)", obs, flags=re.IGNORECASE)
    if not match:
        return []
    achados = re.findall(r"\d{1,2}/\d{1,2}(?:/\d{2,4})?", match.group(1))
    return achados


def _obs_reagendado_de(datas: list, obs_atual: Optional[str] = None) -> Optional[str]:
    """Monta 'Reagendado de 27/10/2026 e 30/10/2026', preservando marca de Pago."""
    hoje = date.today()
    candidatas = []
    for d in datas:
        if d is None or d == "":
            continue
        if isinstance(d, date):
            candidatas.append(_dia(d))
        else:
            texto = str(d).strip()
            if texto:
                candidatas.append(texto)
    candidatas.extend(_datas_em_obs_reagendado(obs_atual))
    ordenadas = []
    vistos = set()
    for texto in candidatas:
        chave = _fold(texto)
        if not chave or chave in vistos:
            continue
        vistos.add(chave)
        ordenadas.append(( _data(texto, hoje) or date.max, texto if "/" in texto else texto ))
    # Normaliza para DD/MM/AAAA quando der para parsear
    finais = []
    vistos2 = set()
    for parsed, bruto in sorted(ordenadas, key=lambda x: x[0]):
        rotulo = _dia(parsed) if parsed != date.max else bruto
        if rotulo in vistos2:
            continue
        vistos2.add(rotulo)
        finais.append(rotulo)
    if not finais:
        return obs_atual
    texto = f"Reagendado de {finais[0]}" if len(finais) == 1 else "Reagendado de " + " e ".join(finais)
    if _obs_ja_pago(obs_atual):
        livre = re.sub(
            r"\s*[·\-–]?\s*\bj[áa]?\s*pag[oa]s?\b",
            "",
            re.sub(r"reagendado\s+de\s+[^·\-–]+", "", obs_atual or "", flags=re.IGNORECASE),
            flags=re.IGNORECASE,
        )
        livre = re.sub(r"\s+", " ", livre).strip(" ·-–")
        if livre:
            return f"{livre} · {texto} · Pago"
        return f"{texto} · Pago"
    # Mantém resto da obs que não seja o bloco reagendado/pago
    livre = re.sub(r"reagendado\s+de\s+[^·\-–]+", "", obs_atual or "", flags=re.IGNORECASE)
    livre = re.sub(r"\s*[·\-–]?\s*\bj[áa]?\s*pag[oa]s?\b", "", livre, flags=re.IGNORECASE)
    livre = re.sub(r"\s+", " ", livre).strip(" ·-–")
    if livre:
        return f"{livre} · {texto}"
    return texto


def _ensure(db: Session) -> None:
    db.execute(text('ALTER TABLE commerce."order" ADD COLUMN IF NOT EXISTS delivery_on DATE'))
    db.execute(text('ALTER TABLE commerce."order" ADD COLUMN IF NOT EXISTS discount_percent NUMERIC(5,2) NOT NULL DEFAULT 0'))
    db.execute(text('ALTER TABLE commerce."order" ADD COLUMN IF NOT EXISTS address_text TEXT'))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(10,2) NOT NULL DEFAULT 0"))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS discount_percent NUMERIC(5,2) NOT NULL DEFAULT 0"))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS label VARCHAR(200)"))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS qty_delivered NUMERIC(10,2)"))
    db.execute(text("UPDATE commerce.order_item SET qty_delivered = qty WHERE qty_delivered IS NULL"))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS reschedule_qty NUMERIC(10,2) NOT NULL DEFAULT 0"))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS reschedule_on DATE"))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS delivery_note TEXT"))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS carried_from_order_id UUID"))
    db.execute(text("""ALTER TABLE commerce."order" ADD COLUMN IF NOT EXISTS purpose VARCHAR(20) NOT NULL DEFAULT 'venda'"""))
    db.execute(text('ALTER TABLE commerce."order" ADD COLUMN IF NOT EXISTS finalized_at TIMESTAMP'))
    db.execute(text('ALTER TABLE commerce."order" ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP'))
    db.execute(text("ALTER TABLE commerce.customer ADD COLUMN IF NOT EXISTS kind VARCHAR(20) DEFAULT 'pessoa'"))
    db.execute(text("ALTER TABLE commerce.customer ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE"))
    db.commit()


def _cliente_eventual(db: Session, nome: str, lista_id: int) -> dict:
    """Nome só na boleta: não entra no cadastro (kind eventual, active false)."""
    limpo = re.sub(r"\s+", " ", (nome or "").strip())[:200]
    if not limpo:
        raise HTTPException(status_code=400, detail="Falta o nome do cliente eventual.")
    achado = db.execute(
        text(
            """
            SELECT id, name, default_price_list_id
            FROM commerce.customer
            WHERE kind = 'eventual'
              AND lower(trim(name)) = lower(trim(:nome))
            ORDER BY id
            LIMIT 1
            """
        ),
        {"nome": limpo},
    ).mappings().first()
    if achado:
        if achado["default_price_list_id"] != lista_id:
            db.execute(
                text(
                    """
                    UPDATE commerce.customer
                    SET default_price_list_id = :lista, active = FALSE, kind = 'eventual'
                    WHERE id = :id
                    """
                ),
                {"lista": lista_id, "id": achado["id"]},
            )
        return {
            "id": achado["id"],
            "name": achado["name"],
            "default_price_list_id": lista_id,
            "kind": "eventual",
        }
    criado = db.execute(
        text(
            """
            INSERT INTO commerce.customer (
                name, phone_e164, kind, price_profile, default_price_list_id, notes, active, created_at
            ) VALUES (
                :name, NULL, 'eventual', 'VAREJO', :lista,
                'Cliente eventual — só na boleta, sem cadastro', FALSE, now()
            )
            RETURNING id, name, default_price_list_id
            """
        ),
        {"name": limpo, "lista": lista_id},
    ).mappings().first()
    return {**dict(criado), "kind": "eventual"}


def _produto(nome: str, produtos: list) -> Optional[dict]:
    base, formato = _rotulo(nome)
    chave = _fold(base)
    exatos = [item for item in produtos if _fold(item["name"]) == chave]
    if formato:
        return next((item for item in exatos if _formato(item["unit"]) == formato), None)
    if len(exatos) == 1:
        return exatos[0]
    for preferido in ("unidade", "maço"):
        achado = next((item for item in exatos if _formato(item["unit"]) == preferido), None)
        if achado:
            return achado
    return exatos[0] if exatos else None


def _obs_ja_pago(observacao: Optional[str]) -> bool:
    """'Pago' / 'já pagas' no reagendamento: só entrega, sem nova cobrança."""
    return bool(re.search(r"\b(?:ja\s+)?pag[oa]s?\b", _fold(observacao or "")))


def _quantidades(item: ItemIn) -> tuple[Decimal, Decimal, Decimal]:
    """Pedido, entrega e valor cobrado.

    Em geral cobra o entregue. Se o reagendamento está 'já pago' na origem, soma a qtd
    reagendada nesta nota; o outro dia só entrega (destino com origem_id + já pago = R$ 0).
    """
    pedida = Decimal(str(item.qtd))
    entregue = Decimal(str(item.qtd if item.qtd_entregue is None else item.qtd_entregue))
    if entregue < 0:
        entregue = Decimal("0")
    cobrada = entregue
    if _obs_ja_pago(item.observacao):
        if item.origem_id:
            # Destino do reagendamento já pago: entrega sem nova fatura.
            cobrada = Decimal("0")
        else:
            falta = pedida - entregue
            if falta < 0:
                falta = Decimal("0")
            reagendada = Decimal(str(item.qtd_reagendada or 0))
            if reagendada < 0:
                reagendada = Decimal("0")
            if reagendada > falta:
                reagendada = falta
            cobrada = entregue + reagendada
    valor = _centavos(item.valor)
    bruto = cobrada * valor
    fixo = cobrada * _centavos(item.desconto)
    percentual = bruto * (Decimal(str(item.desconto_percentual)) / Decimal("100"))
    total = bruto - fixo - percentual
    if total < 0:
        total = Decimal("0")
    return pedida, entregue, total.quantize(CENTAVO)


def _reagendamento(item: ItemIn, pedida: Decimal, entregue: Decimal, hoje: date, entrega: Optional[date], quem: str, faltas: List[str]):
    """Quantidade, dia e observação. A quantidade não passa da falta."""
    falta = pedida - entregue
    if falta < 0:
        falta = Decimal("0")
    quantidade = Decimal(str(item.qtd_reagendada or 0))
    if quantidade < 0:
        quantidade = Decimal("0")
    if quantidade > falta:
        quantidade = falta
    dia = _data(item.data_reagendada, hoje) if quantidade > 0 else None
    if quantidade > 0 and not dia:
        faltas.append(f"{quem}: falta o dia do reagendamento de {item.produto}.")
    elif quantidade > 0 and entrega and dia == entrega:
        faltas.append(f"{quem}: o reagendamento de {item.produto} precisa ser outro dia.")
    obs = re.sub(r"\s+", " ", (item.observacao or "").strip())[:300] or None
    if entregue >= pedida:
        obs = None
    origem = None
    if item.origem_id:
        try:
            origem = str(uuid.UUID(str(item.origem_id)))
        except ValueError:
            origem = None
    return quantidade, dia, obs, origem


def _recalcular_nota(db: Session, order_id) -> None:
    pedido = str(order_id)
    row = db.execute(
        text('SELECT discount_percent FROM commerce."order" WHERE id = :id'),
        {"id": pedido},
    ).mappings().first()
    if not row:
        return
    soma = db.execute(
        text("SELECT COALESCE(SUM(subtotal), 0) AS subtotal, COUNT(*) AS n FROM commerce.order_item WHERE order_id = :id"),
        {"id": pedido},
    ).mappings().first()
    if not soma or int(soma["n"] or 0) == 0:
        db.execute(text("UPDATE chatbot.conversation SET current_order_id = NULL WHERE current_order_id = :id"), {"id": pedido})
        db.execute(text("DELETE FROM commerce.delivery_stop WHERE order_id = :id"), {"id": pedido})
        db.execute(text("DELETE FROM commerce.payment WHERE order_id = :id"), {"id": pedido})
        db.execute(text('DELETE FROM commerce."order" WHERE id = :id'), {"id": pedido})
        return
    subtotal = Decimal(str(soma["subtotal"] or 0)).quantize(CENTAVO)
    desconto = Decimal(str(row["discount_percent"] or 0))
    total = (subtotal * (Decimal("1") - desconto / Decimal("100"))).quantize(CENTAVO)
    if total < 0:
        total = Decimal("0")
    db.execute(
        text('UPDATE commerce."order" SET subtotal = :subtotal, total = :total WHERE id = :id'),
        {"id": pedido, "subtotal": subtotal, "total": total},
    )


def _nota_no_dia(db: Session, customer_id: int, dia: date, lista_id, endereco, desconto, agora: datetime, preferidos: list):
    for candidato in preferidos:
        vivo = db.execute(
            text('SELECT id FROM commerce."order" WHERE id = :id AND status <> \'CANCELED\''),
            {"id": str(candidato)},
        ).first()
        if vivo:
            return vivo[0]
    achada = db.execute(
        text(
            """
            SELECT id FROM commerce."order"
            WHERE customer_id = :customer_id AND delivery_on = :dia AND status <> 'CANCELED'
              AND COALESCE(purpose, 'venda') = 'venda'
            ORDER BY created_at
            LIMIT 1
            """
        ),
        {"customer_id": customer_id, "dia": dia},
    ).first()
    if achada:
        return achada[0]
    novo = uuid.uuid4()
    db.execute(
        text(
            """
            INSERT INTO commerce."order" (
                id, customer_id, status, channel, price_list_id, delivery_fee,
                subtotal, total, created_at, confirmed_at, delivery_on, discount_percent, address_text
            ) VALUES (
                :id, :customer_id, 'CONFIRMED', 'MANUAL', :price_list_id, 0,
                0, 0, :agora, :agora, :dia, :discount_percent, :address_text
            )
            """
        ),
        {
            "id": novo,
            "customer_id": customer_id,
            "price_list_id": lista_id,
            "agora": agora,
            "dia": dia,
            "discount_percent": desconto,
            "address_text": endereco,
        },
    )
    return novo


def _subtotal_linha(qty: Decimal, unit_price: Decimal, discount_amount: Decimal, discount_percent: Decimal) -> Decimal:
    bruto = qty * unit_price
    percentual = bruto * (Decimal(str(discount_percent)) / Decimal("100"))
    total = bruto - discount_amount - percentual
    if total < 0:
        total = Decimal("0")
    return total.quantize(CENTAVO)


def _fundir_linhas_pedido(db: Session, itens: list) -> list:
    """Uma linha por produto na mesma nota. Várias origens → obs 'Reagendado de A e B'."""
    por_chave: dict = {}
    ordem: list = []
    for tupla in itens:
        item, produto, pedida, entregue, total, reagendar, dia_reag, obs, origem = tupla
        chave = _chave_produto(item.produto) or _chave_produto(produto.get("name") or "") or str(produto["id"])
        if chave not in por_chave:
            por_chave[chave] = [
                item,
                produto,
                Decimal(str(pedida)),
                Decimal(str(entregue)),
                Decimal(str(total)),
                Decimal(str(reagendar or 0)),
                dia_reag,
                obs,
                origem,
                [_dia_do_pedido(db, origem)] if origem else list(_datas_em_obs_reagendado(obs)),
            ]
            ordem.append(chave)
            continue
        acc = por_chave[chave]
        acc[2] += Decimal(str(pedida))
        acc[3] += Decimal(str(entregue))
        acc[4] += Decimal(str(total))
        reag = Decimal(str(reagendar or 0))
        if reag > 0:
            acc[5] += reag
            if dia_reag:
                acc[6] = dia_reag
        dia_origem = _dia_do_pedido(db, origem) if origem else None
        if dia_origem:
            acc[9].append(dia_origem)
        acc[9].extend(_datas_em_obs_reagendado(obs))
        if obs and _obs_ja_pago(obs):
            acc[7] = _obs_reagendado_de(acc[9], obs)
        else:
            acc[7] = _obs_reagendado_de(acc[9], acc[7] or obs)
        if acc[8] and origem and str(acc[8]) != str(origem):
            acc[8] = None  # várias origens: só a obs lista os dias
        elif not acc[8] and origem:
            acc[8] = origem
    saida = []
    for chave in ordem:
        acc = por_chave[chave]
        if len({d for d in acc[9] if d}) > 1:
            acc[7] = _obs_reagendado_de(acc[9], acc[7])
            acc[8] = None
        elif len({d for d in acc[9] if d}) == 1 and not (acc[7] or "").strip():
            acc[7] = _obs_reagendado_de(acc[9], acc[7])
        saida.append(tuple(acc[:9]))
    return saida


def _fundir_duplicatas_cliente_dia(db: Session, customer_id: int, dia: date) -> None:
    """Garante uma linha por produto na(s) nota(s) do cliente naquele dia."""
    rows = db.execute(
        text(
            """
            SELECT DISTINCT i.product_id, COALESCE(i.label, p.name, '') AS label
            FROM commerce.order_item i
            JOIN commerce."order" o ON o.id = i.order_id
            LEFT JOIN commerce.product p ON p.id = i.product_id
            WHERE o.customer_id = :customer_id
              AND o.delivery_on = :dia
              AND o.status <> 'CANCELED'
              AND COALESCE(o.purpose, 'venda') = 'venda'
            """
        ),
        {"customer_id": customer_id, "dia": dia},
    ).mappings().all()
    for row in rows:
        _item_produto_no_dia(db, customer_id, dia, row["product_id"], row["label"] or "")


def _chave_produto(nome: str) -> str:
    """Nome canônico sem formato (unidade/maço) — alinha Mostarda e Mostarda (unidade)."""
    base, _ = _rotulo(nome or "")
    return _fold(base)


def _linhas_produto_no_dia(db: Session, customer_id: int, dia: date, product_id, label: str) -> list:
    """Todas as linhas do mesmo produto no dia (id e/ou nome canônico)."""
    vistos = set()
    achadas = []
    select_cols = """
                SELECT i.id, i.order_id, i.qty, i.qty_delivered, i.unit_price, i.discount_amount,
                       i.discount_percent, i.delivery_note, i.carried_from_order_id,
                       origem.delivery_on AS origem_dia
    """
    joins = """
                FROM commerce.order_item i
                JOIN commerce."order" o ON o.id = i.order_id
                LEFT JOIN commerce."order" origem ON origem.id = i.carried_from_order_id
    """
    if product_id is not None:
        for row in db.execute(
            text(
                select_cols
                + joins
                + """
                WHERE o.customer_id = :customer_id
                  AND o.delivery_on = :dia
                  AND o.status <> 'CANCELED'
                  AND COALESCE(o.purpose, 'venda') = 'venda'
                  AND i.product_id = :product_id
                ORDER BY o.created_at, i.created_at
                """
            ),
            {"customer_id": customer_id, "dia": dia, "product_id": product_id},
        ).mappings():
            if row["id"] in vistos:
                continue
            vistos.add(row["id"])
            achadas.append(row)
    chave = _chave_produto(label or "")
    if chave:
        for row in db.execute(
            text(
                select_cols
                + """,
                       COALESCE(i.label, p.name, '') AS nome
                """
                + joins
                + """
                LEFT JOIN commerce.product p ON p.id = i.product_id
                WHERE o.customer_id = :customer_id
                  AND o.delivery_on = :dia
                  AND o.status <> 'CANCELED'
                  AND COALESCE(o.purpose, 'venda') = 'venda'
                ORDER BY o.created_at, i.created_at
                """
            ),
            {"customer_id": customer_id, "dia": dia},
        ).mappings():
            if row["id"] in vistos:
                continue
            if _chave_produto(row["nome"] or "") != chave:
                continue
            vistos.add(row["id"])
            achadas.append(row)
    return achadas


def _item_produto_no_dia(db: Session, customer_id: int, dia: date, product_id, label: str):
    """Uma linha do produto no dia; se houver duplicata, funde numa só (somar nunca deixa 2)."""
    linhas = _linhas_produto_no_dia(db, customer_id, dia, product_id, label)
    if not linhas:
        return None
    if len(linhas) == 1:
        return linhas[0]
    base = linhas[0]
    qty = Decimal(str(base["qty"] or 0))
    ent = base["qty_delivered"]
    if ent is None:
        ent = base["qty"]
    ent = Decimal(str(ent or 0))
    datas_origem = []
    if base.get("origem_dia"):
        datas_origem.append(_dia(base["origem_dia"]))
    datas_origem.extend(_datas_em_obs_reagendado(base.get("delivery_note")))
    note_base = base["delivery_note"]
    for extra in linhas[1:]:
        qty += Decimal(str(extra["qty"] or 0))
        e = extra["qty_delivered"]
        if e is None:
            e = extra["qty"]
        ent += Decimal(str(e or 0))
        if extra.get("origem_dia"):
            datas_origem.append(_dia(extra["origem_dia"]))
        datas_origem.extend(_datas_em_obs_reagendado(extra.get("delivery_note")))
        if extra.get("delivery_note") and _obs_ja_pago(extra["delivery_note"]):
            note_base = extra["delivery_note"]
        db.execute(text("DELETE FROM commerce.order_item WHERE id = :id"), {"id": extra["id"]})
        if str(extra["order_id"]) != str(base["order_id"]):
            _recalcular_nota(db, extra["order_id"])
    unit = Decimal(str(base["unit_price"]))
    disc_a = Decimal(str(base["discount_amount"] or 0))
    disc_p = Decimal(str(base["discount_percent"] or 0))
    note = _obs_reagendado_de(datas_origem, note_base) if datas_origem else note_base
    cobrada = Decimal("0") if _obs_ja_pago(note) else ent
    subtotal = _subtotal_linha(cobrada, unit, disc_a, disc_p)
    db.execute(
        text(
            """
            UPDATE commerce.order_item SET
                qty = :qty,
                qty_delivered = :qty_delivered,
                subtotal = :subtotal,
                delivery_note = :delivery_note,
                carried_from_order_id = NULL
            WHERE id = :id
            """
        ),
        {
            "id": base["id"],
            "qty": qty,
            "qty_delivered": ent,
            "subtotal": subtotal,
            "delivery_note": note,
        },
    )
    _recalcular_nota(db, base["order_id"])
    return _linhas_produto_no_dia(db, customer_id, dia, product_id, label)[0]


def _retirar_qtd_produto_no_dia(
    db: Session, customer_id: int, dia: date, product_id, label: str, qty
) -> None:
    """Desfaz qtde previamente reagendada (somar em linha existente ou insert puro)."""
    existente = _item_produto_no_dia(db, customer_id, dia, product_id, label or "")
    if not existente:
        return
    qtd = Decimal(str(qty or 0))
    if qtd <= 0:
        return
    nova_qty = Decimal(str(existente["qty"])) - qtd
    base_ent = existente["qty_delivered"]
    if base_ent is None:
        base_ent = existente["qty"]
    nova_ent = Decimal(str(base_ent)) - qtd
    if nova_ent < 0:
        nova_ent = Decimal("0")
    nota = existente["order_id"]
    if nova_qty <= 0:
        db.execute(text("DELETE FROM commerce.order_item WHERE id = :id"), {"id": existente["id"]})
        _recalcular_nota(db, nota)
        return
    unit = Decimal(str(existente["unit_price"]))
    disc_a = Decimal(str(existente["discount_amount"] or 0))
    disc_p = Decimal(str(existente["discount_percent"] or 0))
    note = existente["delivery_note"]
    cobrada = Decimal("0") if _obs_ja_pago(note) else nova_ent
    subtotal = _subtotal_linha(cobrada, unit, disc_a, disc_p)
    db.execute(
        text(
            """
            UPDATE commerce.order_item SET
                qty = :qty,
                qty_delivered = :qty_delivered,
                subtotal = :subtotal
            WHERE id = :id
            """
        ),
        {"id": existente["id"], "qty": nova_qty, "qty_delivered": nova_ent, "subtotal": subtotal},
    )
    _recalcular_nota(db, nota)


def _aplicar_reagendamentos(
    db: Session,
    origem_id,
    customer_id: int,
    lista_id,
    endereco,
    desconto,
    agora: datetime,
    itens: list,
    anteriores: Optional[list] = None,
) -> int:
    """Tira o que esta origem tinha levado e grava o reagendamento atual (somar = UPDATE, sem duplicar)."""
    notas_tocadas: set = set()
    for ant in anteriores or []:
        dia_ant = ant.get("dia")
        if not dia_ant or not ant.get("qty"):
            continue
        _retirar_qtd_produto_no_dia(
            db, customer_id, dia_ant, ant.get("product_id"), ant.get("label") or "", ant["qty"]
        )
    # Marca antiga carried_from: limpa o vínculo (não apaga linha nativa que o bug antigo etiquetou).
    # Insert puro desta origem já foi zerado/apagado no retirar acima quando batia a qtde.
    marcadas = db.execute(
        text(
            """
            SELECT i.id, i.order_id, o.delivery_on
            FROM commerce.order_item i
            JOIN commerce."order" o ON o.id = i.order_id
            WHERE i.carried_from_order_id = :origem
            """
        ),
        {"origem": str(origem_id)},
    ).mappings().all()
    preferidos_por_dia: dict = {}
    for row in marcadas:
        preferidos_por_dia.setdefault(row["delivery_on"], []).append(row["order_id"])
        db.execute(
            text("UPDATE commerce.order_item SET carried_from_order_id = NULL WHERE id = :id"),
            {"id": row["id"]},
        )
        notas_tocadas.add(str(row["order_id"]))

    por_dia: dict = {}
    for item in itens:
        por_dia.setdefault(item["dia"], []).append(item)
    gravados = 0
    for dia, linhas in por_dia.items():
        preferidos = list(preferidos_por_dia.get(dia) or [])
        notas_recalc: set = set()
        for linha in linhas:
            conduta = (linha.get("conduta") or "").strip().lower()
            if conduta not in ("somar", "substituir"):
                conduta = "somar"
            existente = _item_produto_no_dia(
                db, customer_id, dia, linha["product_id"], linha.get("label") or ""
            )
            if existente:
                nota = existente["order_id"]
                if str(nota) == str(origem_id):
                    continue
                qtd_movida = Decimal(str(linha["qty"]))
                dia_desta = _dia_do_pedido(db, origem_id)
                if conduta == "substituir":
                    nova_qty = qtd_movida
                    nova_ent = qtd_movida
                    unit = Decimal(str(linha["unit_price"]))
                    disc_a = Decimal(str(linha["discount_amount"] or 0))
                    disc_p = Decimal(str(linha["discount_percent"] or 0))
                    note = _obs_reagendado_de([dia_desta], linha.get("observacao"))
                    # Substituir: a linha passa a representar só o reagendado desta origem.
                    carried = origem_id
                else:
                    # somar: nunca cria segunda linha; não marca carried na nativa (senão o próximo salvar apaga).
                    nova_qty = Decimal(str(existente["qty"])) + qtd_movida
                    base_ent = existente["qty_delivered"]
                    if base_ent is None:
                        base_ent = existente["qty"]
                    nova_ent = Decimal(str(base_ent)) + qtd_movida
                    unit = Decimal(str(existente["unit_price"]))
                    disc_a = Decimal(str(existente["discount_amount"] or 0))
                    disc_p = Decimal(str(existente["discount_percent"] or 0))
                    datas = []
                    if existente.get("origem_dia"):
                        datas.append(_dia(existente["origem_dia"]))
                    elif existente.get("carried_from_order_id"):
                        datas.append(_dia_do_pedido(db, existente["carried_from_order_id"]))
                    datas.append(dia_desta)
                    note_base = existente["delivery_note"]
                    if linha.get("observacao") and _obs_ja_pago(linha["observacao"]):
                        note_base = linha["observacao"]
                    note = _obs_reagendado_de(datas, note_base)
                    # Várias origens na obs: não prende a linha a um único carried.
                    carried = None
                if _obs_ja_pago(note):
                    cobrada = Decimal("0")
                else:
                    cobrada = nova_ent
                subtotal = _subtotal_linha(cobrada, unit, disc_a, disc_p)
                db.execute(
                    text(
                        """
                        UPDATE commerce.order_item SET
                            qty = :qty,
                            qty_delivered = :qty_delivered,
                            unit_price = :unit_price,
                            subtotal = :subtotal,
                            discount_amount = :discount_amount,
                            discount_percent = :discount_percent,
                            delivery_note = :delivery_note,
                            carried_from_order_id = :origem
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": existente["id"],
                        "qty": nova_qty,
                        "qty_delivered": nova_ent,
                        "unit_price": unit,
                        "subtotal": subtotal,
                        "discount_amount": disc_a,
                        "discount_percent": disc_p,
                        "delivery_note": note,
                        "origem": str(carried) if carried else None,
                    },
                )
            else:
                nota = _nota_no_dia(db, customer_id, dia, lista_id, endereco, desconto, agora, preferidos)
                if str(nota) == str(origem_id):
                    continue
                db.execute(
                    text(
                        """
                        INSERT INTO commerce.order_item (
                            order_id, product_id, qty, qty_delivered, unit_price, subtotal, created_at,
                            discount_amount, discount_percent, label, delivery_note, carried_from_order_id
                        ) VALUES (
                            :order_id, :product_id, :qty, :qty, :unit_price, :subtotal, :agora,
                            :discount_amount, :discount_percent, :label, :delivery_note, :origem
                        )
                        """
                    ),
                    {
                        "order_id": nota,
                        "product_id": linha["product_id"],
                        "qty": linha["qty"],
                        "unit_price": linha["unit_price"],
                        "subtotal": linha["subtotal"],
                        "agora": agora,
                        "discount_amount": linha["discount_amount"],
                        "discount_percent": linha["discount_percent"],
                        "label": linha["label"],
                        "delivery_note": _obs_reagendado_de(
                            [_dia_do_pedido(db, origem_id)], linha.get("observacao")
                        ),
                        "origem": str(origem_id),
                    },
                )
            gravados += 1
            notas_recalc.add(str(nota))
        for nota_id in notas_recalc:
            _recalcular_nota(db, nota_id)
    for nota_id in notas_tocadas:
        _recalcular_nota(db, nota_id)
    return gravados


@router.post("")
def salvar_boletas(body: LoteIn, db: Session = Depends(get_db_session)):
    """Grava as notas da tela e devolve a quantidade salva."""
    if not body.pedidos:
        raise HTTPException(status_code=400, detail="Não há pedido na tela para salvar.")
    _ensure(db)
    hoje = date.today()
    produtos = [
        dict(row)
        for row in db.execute(text("SELECT id, name, unit FROM commerce.product WHERE COALESCE(active, TRUE)")).mappings()
    ]
    listas = {
        _fold(row["name"]): row["id"]
        for row in db.execute(text("SELECT id, name FROM commerce.price_list")).mappings()
    }
    faltas: List[str] = []
    prontos = []
    mantidos: dict = {}
    destravados: dict = {}
    for pedido in body.pedidos:
        compra = pedido.tipo == "compra"
        nome_tela = re.sub(r"\s+", " ", (pedido.cliente or "").strip())
        cliente = None
        if pedido.cliente_id:
            cliente = db.execute(
                text(
                    """
                    SELECT id, name, default_price_list_id, COALESCE(kind, 'pessoa') AS kind
                    FROM commerce.customer WHERE id = :id
                    """
                ),
                {"id": pedido.cliente_id},
            ).mappings().first()
        quem = (cliente["name"] if cliente else nome_tela).strip() or "Uma nota"
        lista_id_previa = listas.get(_fold(pedido.tabela))
        if not cliente and not compra:
            if not nome_tela:
                faltas.append(f"{quem}: falta o nome na nota.")
                continue
            if not lista_id_previa:
                faltas.append(f"{quem}: escolha a tabela (Varejo, Restaurantes, Revenda ou Amigos).")
                continue
            # Cliente eventual: nome + tabela na boleta, sem cadastro.
            cliente = _cliente_eventual(db, nome_tela, lista_id_previa)
        if not cliente:
            faltas.append(f"{quem}: falta escolher o {'fornecedor' if compra else 'cliente'} do cadastro.")
            continue
        existente = None
        if pedido.id:
            try:
                pedido_uuid = uuid.UUID(str(pedido.id))
            except ValueError:
                faltas.append(f"{quem}: este pedido não pode ser atualizado.")
                continue
            existente = db.execute(
                text(
                    """
                    SELECT id, price_list_id, finalized_at
                    FROM commerce."order"
                    WHERE id = :id AND status <> 'CANCELED'
                    """
                ),
                {"id": str(pedido_uuid)},
            ).mappings().first()
            if not existente:
                faltas.append(f"{quem}: não achei este pedido para atualizar.")
                continue
            if existente["finalized_at"]:
                if pedido.desconcluir:
                    destravados[id(pedido)] = str(existente["id"])
                else:
                    mantidos[id(pedido)] = str(existente["id"])
                    # Nota concluída ainda aceita marcar/desmarcar pago.
                    db.execute(
                        text(
                            """
                            UPDATE commerce."order"
                            SET paid_at = CASE
                                WHEN :pago THEN COALESCE(paid_at, :agora)
                                ELSE NULL
                            END
                            WHERE id = :id
                            """
                        ),
                        {"pago": bool(pedido.pago), "agora": datetime.now(), "id": str(existente["id"])},
                    )
                continue
        entrega = _data(pedido.data, hoje)
        if not entrega:
            faltas.append(f"{quem}: falta a data de entrega.")
        lista_id = (
            listas.get(_fold(pedido.tabela))
            or (existente["price_list_id"] if existente else None)
            or cliente["default_price_list_id"]
        )
        if not lista_id and compra:
            lista_id = next(iter(listas.values()), None)
        if not lista_id:
            faltas.append(f"{quem}: falta a tabela de preço.")
        # Eventual: garante o nome da tela e a tabela escolhida.
        if not compra and str(cliente.get("kind") or "") == "eventual" and lista_id and nome_tela:
            cliente = _cliente_eventual(db, nome_tela, lista_id)
            quem = cliente["name"]
        antes = len(faltas)
        itens = []
        for item in pedido.itens:
            if item.qtd <= 0 or not item.produto.strip():
                continue
            if item.valor <= 0 and not compra and not _obs_ja_pago(item.observacao):
                faltas.append(f"{quem}: falta o preço de {item.produto}.")
                continue
            produto = _produto(item.produto, produtos)
            if not produto:
                faltas.append(f"{quem}: não achei {item.produto} no cadastro.")
                continue
            pedida, entregue, total = _quantidades(item)
            reagendar, dia_reag, obs, origem = _reagendamento(item, pedida, entregue, hoje, entrega, quem, faltas)
            itens.append((item, produto, pedida, entregue, total, reagendar, dia_reag, obs, origem))
        if not itens and len(faltas) == antes:
            faltas.append(f"{quem}: não tem item com quantidade.")
        if entrega and lista_id and itens and cliente:
            prontos.append((pedido, cliente, entrega, lista_id, itens))
    if faltas:
        db.rollback()
        raise HTTPException(status_code=400, detail=" ".join(faltas))
    gravados: dict = {}
    filas = []
    agora = datetime.now()
    dias_a_fundir: set = set()
    for pedido, cliente, entrega, lista_id, itens in prontos:
        itens = _fundir_linhas_pedido(db, itens)
        subtotal = sum((linha[4] for linha in itens), Decimal("0"))
        desconto = Decimal(str(pedido.desconto))
        total = (subtotal * (Decimal("1") - desconto / Decimal("100"))).quantize(CENTAVO)
        dias_a_fundir.add((cliente["id"], entrega))
        if total < 0:
            total = Decimal("0")
        dados = {
            "customer_id": cliente["id"],
            "price_list_id": lista_id,
            "subtotal": subtotal.quantize(CENTAVO),
            "total": total,
            "delivery_on": entrega,
            "discount_percent": _centavos(pedido.desconto),
            "address_text": pedido.endereco.strip() or None,
            "purpose": "compra" if pedido.tipo == "compra" else "venda",
            "paid_at": agora if pedido.pago else None,
            "notes": re.sub(r"\s+", " ", (pedido.observacao or "").strip())[:300] or None,
        }
        anteriores_mov = []
        if pedido.id:
            pedido_id = uuid.UUID(str(pedido.id))
            # Antes de reescrever a origem: o que já tinha sido levado (para desfazer somar sem apagar a nativa).
            for row in db.execute(
                text(
                    """
                    SELECT product_id, COALESCE(label, '') AS label, reschedule_qty, reschedule_on
                    FROM commerce.order_item
                    WHERE order_id = :id
                      AND COALESCE(reschedule_qty, 0) > 0
                      AND reschedule_on IS NOT NULL
                    """
                ),
                {"id": str(pedido_id)},
            ).mappings():
                anteriores_mov.append(
                    {
                        "product_id": row["product_id"],
                        "label": row["label"] or "",
                        "qty": row["reschedule_qty"],
                        "dia": row["reschedule_on"],
                    }
                )
            db.execute(
                text(
                    """
                    UPDATE commerce."order"
                    SET customer_id = :customer_id,
                        price_list_id = :price_list_id,
                        subtotal = :subtotal,
                        total = :total,
                        delivery_on = :delivery_on,
                        discount_percent = :discount_percent,
                        address_text = :address_text,
                        purpose = :purpose,
                        notes = :notes,
                        paid_at = CASE
                            WHEN :pago THEN COALESCE(paid_at, :paid_at)
                            ELSE NULL
                        END
                    WHERE id = :id
                    """
                ),
                {**dados, "id": str(pedido_id), "pago": bool(pedido.pago)},
            )
            db.execute(text("DELETE FROM commerce.order_item WHERE order_id = :id"), {"id": str(pedido_id)})
        else:
            pedido_id = uuid.uuid4()
            db.execute(
                text(
                    """
                    INSERT INTO commerce."order" (
                        id, customer_id, status, channel, price_list_id, delivery_fee,
                        subtotal, total, created_at, confirmed_at, delivery_on, discount_percent, address_text, purpose, paid_at, notes
                    ) VALUES (
                        :id, :customer_id, 'CONFIRMED', 'MANUAL', :price_list_id, 0,
                        :subtotal, :total, :agora, :agora, :delivery_on, :discount_percent, :address_text, :purpose, :paid_at, :notes
                    )
                    """
                ),
                {**dados, "id": pedido_id, "agora": agora},
            )
        movidos = []
        for item, produto, pedida, entregue, linha_total, reagendar, dia_reag, obs, origem in itens:
            db.execute(
                text(
                    """
                    INSERT INTO commerce.order_item (
                        order_id, product_id, qty, qty_delivered, unit_price, subtotal, created_at,
                        discount_amount, discount_percent, label,
                        reschedule_qty, reschedule_on, delivery_note, carried_from_order_id
                    ) VALUES (
                        :order_id, :product_id, :qty, :qty_delivered, :unit_price, :subtotal, :agora,
                        :discount_amount, :discount_percent, :label,
                        :reschedule_qty, :reschedule_on, :delivery_note, :carried_from_order_id
                    )
                    """
                ),
                {
                    "order_id": pedido_id,
                    "product_id": produto["id"],
                    "qty": pedida,
                    "qty_delivered": entregue,
                    "unit_price": _centavos(item.valor),
                    "subtotal": linha_total,
                    "agora": agora,
                    "discount_amount": _centavos(item.desconto),
                    "discount_percent": _centavos(item.desconto_percentual),
                    "label": item.produto.strip()[:200],
                    "reschedule_qty": reagendar,
                    "reschedule_on": dia_reag,
                    "delivery_note": obs,
                    "carried_from_order_id": origem,
                },
            )
            if reagendar > 0 and dia_reag:
                # Já pago na nota de origem: vai só para entrega, sem nova fatura.
                pago_origem = _obs_ja_pago(obs)
                valor_destino = 0.0 if pago_origem else item.valor
                desconto_destino = 0.0 if pago_origem else item.desconto
                pct_destino = 0.0 if pago_origem else item.desconto_percentual
                obs_destino = "Já pago" if pago_origem else obs
                destino = ItemIn(
                    produto=item.produto,
                    qtd=float(reagendar),
                    qtd_entregue=float(reagendar),
                    valor=valor_destino,
                    desconto=desconto_destino,
                    desconto_percentual=pct_destino,
                )
                _, _, linha_destino = _quantidades(destino)
                conduta = (item.reagenda_conduta or "").strip().lower()
                if conduta not in ("somar", "substituir"):
                    conduta = None
                movidos.append(
                    {
                        "dia": dia_reag,
                        "product_id": produto["id"],
                        "qty": reagendar,
                        "unit_price": _centavos(valor_destino),
                        "subtotal": linha_destino,
                        "discount_amount": _centavos(desconto_destino),
                        "discount_percent": _centavos(pct_destino),
                        "label": item.produto.strip()[:200],
                        "observacao": obs_destino,
                        "conduta": conduta,
                    }
                )
                dias_a_fundir.add((cliente["id"], dia_reag))
        if pedido.concluir:
            db.execute(
                text('UPDATE commerce."order" SET finalized_at = COALESCE(finalized_at, :agora) WHERE id = :id'),
                {"id": str(pedido_id), "agora": agora},
            )
        gravados[id(pedido)] = str(pedido_id)
        filas.append(
            (
                pedido_id,
                cliente["id"],
                lista_id,
                dados["address_text"],
                dados["discount_percent"],
                movidos,
                anteriores_mov,
            )
        )
    reagendados = 0
    for origem_id, customer_id, lista_origem, endereco, desconto_origem, movidos, anteriores_mov in filas:
        reagendados += _aplicar_reagendamentos(
            db,
            origem_id,
            customer_id,
            lista_origem,
            endereco,
            desconto_origem,
            agora,
            movidos,
            anteriores_mov,
        )
        for mov in movidos:
            dias_a_fundir.add((customer_id, mov["dia"]))
    # Última passada: se ainda houver duas Mostardas no mesmo dia, vira uma.
    for customer_id, dia in dias_a_fundir:
        if customer_id and dia:
            _fundir_duplicatas_cliente_dia(db, customer_id, dia)
    for pedido_id in destravados.values():
        db.execute(
            text('UPDATE commerce."order" SET finalized_at = NULL WHERE id = :id'),
            {"id": pedido_id},
        )
    db.commit()
    ids = []
    for pedido in body.pedidos:
        chave = id(pedido)
        if chave in gravados:
            ids.append(gravados[chave])
        elif chave in destravados:
            ids.append(destravados[chave])
        elif chave in mantidos:
            ids.append(mantidos[chave])
    return {"salvos": len(gravados), "ids": ids, "reagendados": reagendados}


@router.delete("/{pedido_id}")
def excluir_boleta(pedido_id: str, db: Session = Depends(get_db_session)):
    """Apaga a nota do banco. Pedido concluído não sai."""
    _ensure(db)
    try:
        pedido_uuid = str(uuid.UUID(pedido_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Este pedido não pode ser excluído.") from None
    row = db.execute(
        text('SELECT id, finalized_at FROM commerce."order" WHERE id = :id AND status <> \'CANCELED\''),
        {"id": pedido_uuid},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Não achei este pedido.")
    if row["finalized_at"]:
        raise HTTPException(status_code=409, detail="Este pedido já foi concluído. Não dá para excluir.")
    db.execute(text("UPDATE chatbot.conversation SET current_order_id = NULL WHERE current_order_id = :id"), {"id": pedido_uuid})
    db.execute(text("DELETE FROM commerce.delivery_stop WHERE order_id = :id"), {"id": pedido_uuid})
    db.execute(text("DELETE FROM commerce.payment WHERE order_id = :id"), {"id": pedido_uuid})
    db.execute(
        text("UPDATE commerce.order_item SET carried_from_order_id = NULL WHERE carried_from_order_id = :id"),
        {"id": pedido_uuid},
    )
    db.execute(text("DELETE FROM commerce.order_item WHERE order_id = :id"), {"id": pedido_uuid})
    db.execute(text('DELETE FROM commerce."order" WHERE id = :id'), {"id": pedido_uuid})
    db.commit()
    return {"excluido": pedido_uuid}


@router.get("")
def consultar_boletas(
    de: date = Query(...),
    ate: date = Query(...),
    cliente_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session),
):
    """Pedidos do período, agrupados por cliente, para o acerto."""
    if ate < de:
        raise HTTPException(status_code=400, detail="A data final é anterior à inicial.")
    _ensure(db)
    rows = db.execute(
        text(
            """
            SELECT o.id, o.customer_id, c.name AS cliente, COALESCE(o.delivery_on, o.created_at::date) AS dia,
                   o.discount_percent, o.address_text, o.subtotal, o.total, pl.name AS tabela,
                   COALESCE(o.purpose, 'venda') AS purpose, o.notes AS observacao,
                   (o.finalized_at IS NOT NULL) AS concluido,
                   (o.paid_at IS NOT NULL) AS pago,
                   COALESCE(i.label, p.name) AS produto, i.qty, COALESCE(i.qty_delivered, i.qty) AS entregue,
                   i.unit_price, i.discount_amount, i.discount_percent AS item_discount_percent, i.subtotal AS linha,
                   i.reschedule_qty, i.reschedule_on, i.delivery_note, i.carried_from_order_id,
                   origem.delivery_on AS origem_dia
            FROM commerce."order" o
            JOIN commerce.customer c ON c.id = o.customer_id
            JOIN commerce.order_item i ON i.order_id = o.id
            LEFT JOIN commerce.product p ON p.id = i.product_id
            LEFT JOIN commerce.price_list pl ON pl.id = o.price_list_id
            LEFT JOIN commerce."order" origem ON origem.id = i.carried_from_order_id
            WHERE o.status <> 'CANCELED'
              AND COALESCE(o.delivery_on, o.created_at::date) BETWEEN :de AND :ate
              AND (:cliente_id IS NULL OR o.customer_id = :cliente_id)
            ORDER BY c.name, dia, o.created_at, i.id
            """
        ),
        {"de": de, "ate": ate, "cliente_id": cliente_id},
    ).mappings()
    grupos: dict = {}
    ordem = []
    for row in rows:
        chave = row["customer_id"]
        if chave not in grupos:
            grupos[chave] = {"id": chave, "nome": row["cliente"], "pedidos": {}, "ordem": []}
            ordem.append(chave)
        grupo = grupos[chave]
        pedido_id = str(row["id"])
        if pedido_id not in grupo["pedidos"]:
            grupo["pedidos"][pedido_id] = {
                "id": pedido_id,
                "data": _dia(row["dia"]),
                "endereco": row["address_text"] or "",
                "desconto": float(row["discount_percent"] or 0),
                "tabela": row["tabela"] or "",
                "tipo": "compra" if row["purpose"] == "compra" else "venda",
                "concluido": bool(row["concluido"]),
                "pago": bool(row["pago"]),
                "observacao": row["observacao"] or "",
                "subtotal": float(row["subtotal"] or 0),
                "total": float(row["total"] or 0),
                "itens": [],
            }
            grupo["ordem"].append(pedido_id)
        grupo["pedidos"][pedido_id]["itens"].append(
            {
                "produto": row["produto"] or "",
                "qtd": float(row["qty"] or 0),
                "qtd_entregue": float(row["entregue"] if row["entregue"] is not None else row["qty"] or 0),
                "valor": float(row["unit_price"] or 0),
                "desconto": float(row["discount_amount"] or 0),
                "desconto_percentual": float(row["item_discount_percent"] or 0),
                "total": float(row["linha"] or 0),
                "qtd_reagendada": float(row["reschedule_qty"] or 0),
                "data_reagendada": _dia(row["reschedule_on"]) if row["reschedule_on"] else "",
                "observacao": row["delivery_note"] or "",
                "origem_id": str(row["carried_from_order_id"]) if row["carried_from_order_id"] else "",
                "origem_data": _dia(row["origem_dia"]) if row["origem_dia"] else "",
            }
        )
    clientes = []
    total = Decimal("0")
    for chave in ordem:
        grupo = grupos[chave]
        pedidos = [grupo["pedidos"][item] for item in grupo["ordem"]]
        soma = sum((Decimal(str(item["total"])) for item in pedidos), Decimal("0")).quantize(CENTAVO)
        total += soma
        clientes.append({"id": grupo["id"], "nome": grupo["nome"], "total": float(soma), "pedidos": pedidos})
    return {"de": de.isoformat(), "ate": ate.isoformat(), "total": float(total.quantize(CENTAVO)), "clientes": clientes}
