"""
Cadastro de preços e de clientes.

Cada produto tem quatro preços: Varejo, Restaurantes, Revenda e Amigos.
São linhas na tabela de preço, no lugar das folhas impressas.
O desconto de um cliente em um produto vira o preço específico dele.
"""

import re
import unicodedata
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db_session import get_db_session
from models.commerce import (
    Customer,
    CustomerAddress,
    CustomerContact,
    CustomerProductPrice,
    PriceList,
    PriceProfile,
    Product,
    ProductCategory,
    ProductPrice,
)

router = APIRouter(prefix="/cadastro", tags=["cadastro"])

TABELAS = ("Varejo", "Restaurantes", "Revenda", "Amigos")
PRODUTOS = (
    "Alface Americana",
    "Alface Crespa",
    "Alface Roxa",
    "Cebolinha",
    "Coentro",
    "Salsinha",
    "Cheiro-verde",
    "Couve",
    "Rúcula",
    "Espinafre",
    "Agrião",
    "Manjericão",
    "Hortelã",
    "Brócolis Ninja",
    "Brócolis Piracicaba",
    "Acelga",
    "Almeirão",
    "Mostarda",
    "Ovos",
    "Cartela 30 ovos",
    "Rabanete",
    "Repolho",
)

PROFILE_BY_LIST = {
    "Varejo": PriceProfile.VAREJO,
    "Restaurantes": PriceProfile.RESTAURANTE_LOW,
    "Revenda": PriceProfile.RESTAURANTE_HIGH,
    "Amigos": PriceProfile.VAREJO,
}


class PriceIn(BaseModel):
    price: Decimal = Field(..., ge=0)


class FormatoIn(BaseModel):
    formato: str = Field(..., min_length=1, max_length=60)


class ProdutoIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    formato: str = Field(..., min_length=1, max_length=60)


def _fold(value: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", value or "")
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", sem_acento.casefold()).strip()


def formato_canonico(value: Optional[str]) -> str:
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


PAPEIS = ("proprietario", "pedidos", "financeiro")


class PessoaIn(BaseModel):
    name: str = ""
    phone_e164: Optional[str] = None
    papeis: List[str] = []


class CustomerIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price_list_id: int
    phone_e164: Optional[str] = None
    phone2_e164: Optional[str] = None
    endereco: Optional[str] = None
    localizacao: Optional[str] = None
    observacao: Optional[str] = None
    kind: str = "pessoa"
    pessoas: List[PessoaIn] = []
    desconto_pedido: Optional[Decimal] = Field(None, ge=0, le=100)


class DiscountIn(BaseModel):
    product_id: int
    price: Decimal = Field(..., ge=0)


def _ensure_phone_optional(db: Session) -> None:
    db.execute(text("ALTER TABLE commerce.customer ALTER COLUMN phone_e164 DROP NOT NULL"))
    db.execute(text("ALTER TABLE commerce.customer ADD COLUMN IF NOT EXISTS phone2_e164 VARCHAR(20)"))
    db.execute(text("ALTER TABLE commerce.customer ADD COLUMN IF NOT EXISTS kind VARCHAR(20) DEFAULT 'pessoa'"))
    db.execute(text("ALTER TABLE commerce.customer ADD COLUMN IF NOT EXISTS order_discount_percent NUMERIC(5,2)"))
    db.execute(text("ALTER TABLE commerce.product ALTER COLUMN unit TYPE VARCHAR(60)"))
    db.execute(text("UPDATE commerce.customer SET kind = 'pessoa' WHERE kind IS NULL"))
    db.execute(text("ALTER TABLE commerce.customer ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE"))
    db.commit()


def _phone(value: Optional[str]) -> Optional[str]:
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return None
    if digits.startswith("55") and len(digits) >= 12:
        return f"+{digits}"[:20]
    if len(digits) >= 10:
        return f"+55{digits}"[:20]
    return digits[:20]


def _require_customer(body: CustomerIn) -> None:
    missing = []
    if not body.name.strip():
        missing.append("nome completo")
    if not _phone(body.phone_e164):
        missing.append("celular 1")
    if not (body.endereco or "").strip():
        missing.append("endereço")
    if not (body.localizacao or "").strip():
        missing.append("localização")
    if missing:
        raise HTTPException(status_code=422, detail="Para salvar precisa de " + ", ".join(missing))


def _default_address(customer: Customer) -> Optional[CustomerAddress]:
    rows = list(customer.addresses or [])
    for row in rows:
        if row.is_default:
            return row
    return rows[0] if rows else None


def _upsert_address(db: Session, customer: Customer, endereco: str, localizacao: str) -> None:
    address = _default_address(customer)
    if not address:
        address = CustomerAddress(
            customer_id=customer.id,
            label="Entrega",
            street=endereco[:200],
            district="—",
            city="Goiânia",
            state="GO",
            zip="74000000",
            is_default=True,
        )
        db.add(address)
    address.street = endereco[:200]
    address.location_url = localizacao[:500]
    address.is_default = True


def _ensure_catalog(db: Session) -> None:
    _ensure_phone_optional(db)
    category = db.query(ProductCategory).filter(ProductCategory.name == "Hortaliças").first()
    if not category:
        category = ProductCategory(name="Hortaliças", sort_order=0)
        db.add(category)
        db.flush()
    for name in PRODUTOS:
        exists = db.query(Product).filter(Product.name == name).first()
        if not exists:
            db.add(Product(category_id=category.id, name=name, unit="un", active=True))
    for name in TABELAS:
        exists = db.query(PriceList).filter(PriceList.name == name).first()
        if not exists:
            db.add(PriceList(name=name, active=True))
    db.commit()


def _money(value: Optional[Decimal]) -> Optional[float]:
    if value is None:
        return None
    return float(value)


@router.get("/tabelas")
def list_price_tables(db: Session = Depends(get_db_session)):
    _ensure_catalog(db)
    listas = (
        db.query(PriceList)
        .filter(PriceList.name.in_(TABELAS), PriceList.active == True)
        .all()
    )
    listas.sort(key=lambda item: TABELAS.index(item.name) if item.name in TABELAS else 99)
    produtos = db.query(Product).filter(Product.active == True).order_by(Product.name).all()
    precos = db.query(ProductPrice).all()
    by_product = {}
    for price in precos:
        by_product.setdefault(price.product_id, {})[price.price_list_id] = _money(price.price)
    return {
        "listas": [{"id": item.id, "name": item.name} for item in listas],
        "produtos": [
            {
                "id": product.id,
                "name": product.name,
                "formato": formato_canonico(product.unit),
                "precos": by_product.get(product.id, {}),
            }
            for product in produtos
        ],
    }


@router.put("/tabelas/{price_list_id}/produtos/{product_id}")
def set_table_price(
    price_list_id: int,
    product_id: int,
    body: PriceIn,
    db: Session = Depends(get_db_session),
):
    price_list = db.query(PriceList).filter(PriceList.id == price_list_id).first()
    product = db.query(Product).filter(Product.id == product_id).first()
    if not price_list or not product:
        raise HTTPException(status_code=404, detail="Tabela ou produto não encontrado")
    current = (
        db.query(ProductPrice)
        .filter(ProductPrice.price_list_id == price_list_id, ProductPrice.product_id == product_id)
        .first()
    )
    if current:
        current.price = body.price
    else:
        db.add(ProductPrice(price_list_id=price_list_id, product_id=product_id, price=body.price))
    db.commit()
    return {"product_id": product_id, "price_list_id": price_list_id, "price": _money(body.price)}


def _produto_igual(product: Product, name: str, formato: str) -> bool:
    return _fold(product.name) == _fold(name) and formato_canonico(product.unit) == formato_canonico(formato)


@router.put("/produtos/{product_id}/formato")
def set_product_format(product_id: int, body: FormatoIn, db: Session = Depends(get_db_session)):
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    formato = formato_canonico(body.formato)
    outro = (
        db.query(Product)
        .filter(Product.active == True, Product.id != product.id)
        .all()
    )
    if any(_produto_igual(item, product.name, formato) for item in outro):
        raise HTTPException(status_code=409, detail="Esse produto já está nesse formato")
    product.unit = formato
    db.commit()
    return {"id": product.id, "name": product.name, "formato": formato}


@router.post("/produtos", status_code=201)
def create_product(body: ProdutoIn, db: Session = Depends(get_db_session)):
    _ensure_catalog(db)
    nome = re.sub(r"\s+", " ", body.name).strip()
    formato = formato_canonico(body.formato)
    if not nome:
        raise HTTPException(status_code=422, detail="Informe o nome do produto")
    category = db.query(ProductCategory).filter(ProductCategory.name == "Hortaliças").first()
    if not category:
        raise HTTPException(status_code=500, detail="Categoria de produtos não encontrada")
    existente = next((item for item in db.query(Product).filter(Product.active == True).all() if _produto_igual(item, nome, formato)), None)
    if existente:
        raise HTTPException(status_code=409, detail="Esse produto já está nesse formato")
    product = Product(category_id=category.id, name=nome[:200], unit=formato, active=True)
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"id": product.id, "name": product.name, "formato": formato_canonico(product.unit), "precos": {}}


@router.delete("/clientes/{customer_id}")
def delete_customer(
    customer_id: int,
    modo: str = Query(..., pattern="^(base|inativar)$"),
    db: Session = Depends(get_db_session),
):
    _ensure_catalog(db)
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    if modo == "inativar":
        customer.active = False
        db.commit()
        return {"id": customer_id, "active": False}
    db.expunge(customer)
    try:
        order_ids = [
            row[0]
            for row in db.execute(
                text('SELECT id FROM commerce."order" WHERE customer_id = :id'),
                {"id": customer_id},
            )
        ]
        for order_id in order_ids:
            db.execute(
                text("UPDATE chatbot.conversation SET current_order_id = NULL WHERE current_order_id = :id"),
                {"id": order_id},
            )
            db.execute(text("DELETE FROM commerce.delivery_stop WHERE order_id = :id"), {"id": order_id})
            db.execute(text("DELETE FROM commerce.payment WHERE order_id = :id"), {"id": order_id})
            db.execute(text("DELETE FROM commerce.order_item WHERE order_id = :id"), {"id": order_id})
        db.execute(text('DELETE FROM commerce."order" WHERE customer_id = :id'), {"id": customer_id})
        db.execute(
            text("UPDATE chatbot.channel_account SET customer_id = NULL WHERE customer_id = :id"),
            {"id": customer_id},
        )
        db.execute(text("DELETE FROM commerce.customer_product_price WHERE customer_id = :id"), {"id": customer_id})
        db.execute(text("DELETE FROM commerce.customer_contact WHERE customer_id = :id"), {"id": customer_id})
        db.execute(text("DELETE FROM commerce.customer_address WHERE customer_id = :id"), {"id": customer_id})
        db.execute(text("DELETE FROM commerce.customer WHERE id = :id"), {"id": customer_id})
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não deu para excluir este cliente da base.") from exc
    return {"id": customer_id}


@router.delete("/produtos/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db_session)):
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    product.active = False
    db.commit()
    return {"id": product.id}


def _customer_payload(db: Session, customer: Customer) -> dict:
    price_list = None
    if customer.default_price_list_id:
        price_list = db.query(PriceList).filter(PriceList.id == customer.default_price_list_id).first()
    base_prices = {}
    if price_list:
        for row in db.query(ProductPrice).filter(ProductPrice.price_list_id == price_list.id).all():
            base_prices[row.product_id] = _money(row.price)
    descontos = []
    rows = (
        db.query(CustomerProductPrice, Product)
        .join(Product, Product.id == CustomerProductPrice.product_id)
        .filter(CustomerProductPrice.customer_id == customer.id)
        .all()
    )
    for special, product in rows:
        base = base_prices.get(product.id)
        preco = _money(special.price)
        desconto = None
        if base is not None and preco is not None:
            desconto = round(base - preco, 2)
        descontos.append(
            {
                "id": special.id,
                "product_id": product.id,
                "product_name": f"{product.name} ({formato_canonico(product.unit)})",
                "preco_base": base,
                "preco": preco,
                "desconto": desconto,
            }
        )
    address = _default_address(customer)
    return {
        "id": customer.id,
        "name": customer.name,
        "phone_e164": customer.phone_e164,
        "phone2_e164": customer.phone2_e164,
        "endereco": address.street if address else None,
        "localizacao": address.location_url if address else None,
        "observacao": customer.notes,
        "price_list_id": customer.default_price_list_id,
        "price_list_name": price_list.name if price_list else None,
        "kind": customer.kind or "pessoa",
        "pessoas": _pessoas(db, customer),
        "desconto_pedido": _money(customer.order_discount_percent),
        "descontos": descontos,
    }


def _pessoas(db: Session, customer: Customer) -> list:
    if (customer.kind or "pessoa") != "comercio":
        return []
    rows = (
        db.query(CustomerContact)
        .filter(CustomerContact.customer_id == customer.id, CustomerContact.active == True)
        .order_by(CustomerContact.id)
        .all()
    )
    pessoas = []
    for row in rows:
        papeis = [parte for parte in (row.role or "").split(",") if parte in PAPEIS]
        if not papeis:
            continue
        pessoas.append({"nome": row.name, "celular": row.phone_e164, "papeis": papeis})
    return pessoas


def _replace_pessoas(db: Session, customer: Customer, pessoas: List[PessoaIn]) -> None:
    db.query(CustomerContact).filter(CustomerContact.customer_id == customer.id).delete()
    if (customer.kind or "pessoa") != "comercio":
        return
    for person in pessoas:
        nome = person.name.strip()
        if not nome:
            continue
        papeis = [papel for papel in person.papeis if papel in PAPEIS]
        if not papeis:
            raise HTTPException(status_code=422, detail=f"Marque o papel de {nome}")
        db.add(
            CustomerContact(
                customer_id=customer.id,
                name=nome[:200],
                phone_e164=_phone(person.phone_e164),
                role=",".join(papeis),
                active=True,
            )
        )


def _write_customer(db: Session, customer: Customer, body: CustomerIn, price_list: PriceList) -> dict:
    _require_customer(body)
    customer.name = body.name.strip()
    customer.phone_e164 = _phone(body.phone_e164)
    customer.phone2_e164 = _phone(body.phone2_e164)
    customer.notes = (body.observacao or "").strip() or None
    customer.kind = "comercio" if body.kind == "comercio" else "pessoa"
    customer.order_discount_percent = body.desconto_pedido
    customer.default_price_list_id = price_list.id
    customer.price_profile = PROFILE_BY_LIST.get(price_list.name, PriceProfile.VAREJO)
    db.flush()
    _upsert_address(db, customer, body.endereco.strip(), body.localizacao.strip())
    _replace_pessoas(db, customer, body.pessoas)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Esse celular já está em outro cliente") from exc
    db.refresh(customer)
    return _customer_payload(db, customer)


@router.get("/clientes")
def list_registered_customers(db: Session = Depends(get_db_session)):
    _ensure_catalog(db)
    customers = db.query(Customer).filter(Customer.active == True).order_by(Customer.name).all()
    return [_customer_payload(db, customer) for customer in customers]


@router.post("/clientes", status_code=201)
def create_registered_customer(body: CustomerIn, db: Session = Depends(get_db_session)):
    _ensure_catalog(db)
    price_list = db.query(PriceList).filter(PriceList.id == body.price_list_id).first()
    if not price_list:
        raise HTTPException(status_code=404, detail="Preço base não encontrado")
    customer = Customer(name=body.name.strip(), price_profile=PriceProfile.VAREJO)
    db.add(customer)
    return _write_customer(db, customer, body, price_list)


@router.put("/clientes/{customer_id}")
def update_registered_customer(
    customer_id: int,
    body: CustomerIn,
    db: Session = Depends(get_db_session),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    price_list = db.query(PriceList).filter(PriceList.id == body.price_list_id).first()
    if not customer or not price_list:
        raise HTTPException(status_code=404, detail="Cliente ou preço base não encontrado")
    return _write_customer(db, customer, body, price_list)


@router.put("/clientes/{customer_id}/descontos/{product_id}")
def set_customer_discount(
    customer_id: int,
    product_id: int,
    body: DiscountIn,
    db: Session = Depends(get_db_session),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    product = db.query(Product).filter(Product.id == product_id).first()
    if not customer or not product or body.product_id != product_id:
        raise HTTPException(status_code=404, detail="Cliente ou produto não encontrado")
    current = (
        db.query(CustomerProductPrice)
        .filter(
            CustomerProductPrice.customer_id == customer_id,
            CustomerProductPrice.product_id == product_id,
        )
        .first()
    )
    if current:
        current.price = body.price
    else:
        db.add(CustomerProductPrice(customer_id=customer_id, product_id=product_id, price=body.price))
    db.commit()
    db.refresh(customer)
    return _customer_payload(db, customer)


@router.delete("/clientes/{customer_id}/descontos/{product_id}")
def delete_customer_discount(
    customer_id: int,
    product_id: int,
    db: Session = Depends(get_db_session),
):
    current = (
        db.query(CustomerProductPrice)
        .filter(
            CustomerProductPrice.customer_id == customer_id,
            CustomerProductPrice.product_id == product_id,
        )
        .first()
    )
    if current:
        db.delete(current)
        db.commit()
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return _customer_payload(db, customer)
