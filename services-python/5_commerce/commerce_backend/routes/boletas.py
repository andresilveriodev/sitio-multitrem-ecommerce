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


class PedidoIn(BaseModel):
    id: Optional[str] = None
    cliente_id: Optional[int] = None
    data: str = ""
    endereco: str = ""
    desconto: float = 0
    tabela: str = ""
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


def _ensure(db: Session) -> None:
    db.execute(text('ALTER TABLE commerce."order" ADD COLUMN IF NOT EXISTS delivery_on DATE'))
    db.execute(text('ALTER TABLE commerce."order" ADD COLUMN IF NOT EXISTS discount_percent NUMERIC(5,2) NOT NULL DEFAULT 0'))
    db.execute(text('ALTER TABLE commerce."order" ADD COLUMN IF NOT EXISTS address_text TEXT'))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(10,2) NOT NULL DEFAULT 0"))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS discount_percent NUMERIC(5,2) NOT NULL DEFAULT 0"))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS label VARCHAR(200)"))
    db.execute(text("ALTER TABLE commerce.order_item ADD COLUMN IF NOT EXISTS qty_delivered NUMERIC(10,2)"))
    db.execute(text("UPDATE commerce.order_item SET qty_delivered = qty WHERE qty_delivered IS NULL"))
    db.commit()


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


def _quantidades(item: ItemIn) -> tuple[Decimal, Decimal, Decimal]:
    """Pedido, entrega e valor cobrado. A cobrança usa só o que foi entregue."""
    pedida = Decimal(str(item.qtd))
    entregue = Decimal(str(item.qtd if item.qtd_entregue is None else item.qtd_entregue))
    if entregue < 0:
        entregue = Decimal("0")
    valor = _centavos(item.valor)
    bruto = entregue * valor
    fixo = entregue * _centavos(item.desconto)
    percentual = bruto * (Decimal(str(item.desconto_percentual)) / Decimal("100"))
    total = bruto - fixo - percentual
    if total < 0:
        total = Decimal("0")
    return pedida, entregue, total.quantize(CENTAVO)


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
    for pedido in body.pedidos:
        cliente = None
        if pedido.cliente_id:
            cliente = db.execute(
                text("SELECT id, name, default_price_list_id FROM commerce.customer WHERE id = :id"),
                {"id": pedido.cliente_id},
            ).mappings().first()
        quem = (cliente["name"] if cliente else "").strip() or "Uma nota"
        if not cliente:
            faltas.append(f"{quem}: falta escolher o cliente do cadastro.")
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
                    SELECT id, price_list_id
                    FROM commerce."order"
                    WHERE id = :id AND status <> 'CANCELED'
                    """
                ),
                {"id": str(pedido_uuid)},
            ).mappings().first()
            if not existente:
                faltas.append(f"{quem}: não achei este pedido para atualizar.")
                continue
        entrega = _data(pedido.data, hoje)
        if not entrega:
            faltas.append(f"{quem}: falta a data de entrega.")
        lista_id = (
            listas.get(_fold(pedido.tabela))
            or (existente["price_list_id"] if existente else None)
            or cliente["default_price_list_id"]
        )
        if not lista_id:
            faltas.append(f"{quem}: falta a tabela de preço.")
        antes = len(faltas)
        itens = []
        for item in pedido.itens:
            if item.qtd <= 0 or not item.produto.strip():
                continue
            if item.valor <= 0:
                faltas.append(f"{quem}: falta o preço de {item.produto}.")
                continue
            produto = _produto(item.produto, produtos)
            if not produto:
                faltas.append(f"{quem}: não achei {item.produto} no cadastro.")
                continue
            pedida, entregue, total = _quantidades(item)
            itens.append((item, produto, pedida, entregue, total))
        if not itens and len(faltas) == antes:
            faltas.append(f"{quem}: não tem item com quantidade.")
        if entrega and lista_id and itens and cliente:
            prontos.append((pedido, cliente, entrega, lista_id, itens))
    if faltas:
        db.rollback()
        raise HTTPException(status_code=400, detail=" ".join(faltas))
    salvos = []
    agora = datetime.now()
    for pedido, cliente, entrega, lista_id, itens in prontos:
        subtotal = sum((total for _, _, _, _, total in itens), Decimal("0"))
        desconto = Decimal(str(pedido.desconto))
        total = (subtotal * (Decimal("1") - desconto / Decimal("100"))).quantize(CENTAVO)
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
        }
        if pedido.id:
            pedido_id = uuid.UUID(str(pedido.id))
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
                        address_text = :address_text
                    WHERE id = :id
                    """
                ),
                {**dados, "id": str(pedido_id)},
            )
            db.execute(text("DELETE FROM commerce.order_item WHERE order_id = :id"), {"id": str(pedido_id)})
        else:
            pedido_id = uuid.uuid4()
            db.execute(
                text(
                    """
                    INSERT INTO commerce."order" (
                        id, customer_id, status, channel, price_list_id, delivery_fee,
                        subtotal, total, created_at, confirmed_at, delivery_on, discount_percent, address_text
                    ) VALUES (
                        :id, :customer_id, 'CONFIRMED', 'MANUAL', :price_list_id, 0,
                        :subtotal, :total, :agora, :agora, :delivery_on, :discount_percent, :address_text
                    )
                    """
                ),
                {**dados, "id": pedido_id, "agora": agora},
            )
        for item, produto, pedida, entregue, linha_total in itens:
            db.execute(
                text(
                    """
                    INSERT INTO commerce.order_item (
                        order_id, product_id, qty, qty_delivered, unit_price, subtotal, created_at,
                        discount_amount, discount_percent, label
                    ) VALUES (
                        :order_id, :product_id, :qty, :qty_delivered, :unit_price, :subtotal, :agora,
                        :discount_amount, :discount_percent, :label
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
                },
            )
        salvos.append(str(pedido_id))
    db.commit()
    return {"salvos": len(salvos), "ids": salvos}


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
                   COALESCE(i.label, p.name) AS produto, i.qty, COALESCE(i.qty_delivered, i.qty) AS entregue,
                   i.unit_price, i.discount_amount, i.discount_percent AS item_discount_percent, i.subtotal AS linha
            FROM commerce."order" o
            JOIN commerce.customer c ON c.id = o.customer_id
            JOIN commerce.order_item i ON i.order_id = o.id
            LEFT JOIN commerce.product p ON p.id = i.product_id
            LEFT JOIN commerce.price_list pl ON pl.id = o.price_list_id
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
