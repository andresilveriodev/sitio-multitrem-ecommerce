"""
Contexto que cada tela manda para a IA junto com a frase.

O texto é editável. {cliente}, {data}, {tabela} e {endereco}
são preenchidos na hora, com o que estiver aberto na tela.
Pedidos e funil mandam só cliente e data: o formato da resposta
fica no schema da API, e preço, endereço e pagamento ficam no sistema.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from db_session import get_db_session

router = APIRouter(prefix="/cadastro/contexto-ia", tags=["contexto-ia"])

BASE = [
    {
        "tela": "pedidos",
        "titulo": "Pedidos",
        "cliente_da_tela": False,
        "observacao_com": True,
        "instrucao": (
            "Extraia os pedidos da mensagem do operador.\n"
            "\n"
            "Cliente: {cliente}\n"
            "Data padrão: {data}\n"
            "\n"
            "Regras:\n"
            "\n"
            "- Todos os pedidos pertencem ao cliente informado.\n"
            "- Separe pedidos por data; sem data explícita, use a data padrão.\n"
            "- Identifique produto, quantidade, tipo e observação.\n"
            '- Sem tipo informado, use "unidade".\n'
            "- Não invente variedades, produtos ou quantidades.\n"
            "- Nomes de pessoas relacionadas à entrega são observações.\n"
            "- Retorne somente os dados extraídos."
        ),
    },
    {
        "tela": "funil",
        "titulo": "Funil de vendas",
        "cliente_da_tela": True,
        "observacao_com": True,
        "instrucao": (
            "Extraia os pedidos da mensagem do operador.\n"
            "\n"
            "Cliente: {cliente}\n"
            "Data padrão: {data}\n"
            "\n"
            "Regras:\n"
            "\n"
            "- Todos os pedidos pertencem ao cliente informado.\n"
            "- Separe pedidos por data; sem data explícita, use a data padrão.\n"
            "- Identifique produto, quantidade, tipo e observação.\n"
            '- Sem tipo informado, use "unidade".\n'
            "- Não invente variedades, produtos ou quantidades.\n"
            "- Nomes de pessoas relacionadas à entrega são observações.\n"
            "- Retorne somente os dados extraídos."
        ),
    },
    {
        "tela": "clientes",
        "titulo": "Clientes",
        "cliente_da_tela": False,
        "observacao_com": False,
        "instrucao": (
            "A frase altera o cadastro de clientes. Não crie pedido.\n"
            "Cliente aberto na tela: {cliente}.\n"
            "Não invente telefone, endereço nem preço."
        ),
    },
    {
        "tela": "tabelas",
        "titulo": "Preços",
        "cliente_da_tela": False,
        "observacao_com": False,
        "instrucao": (
            "A frase altera o preço de um produto.\n"
            "As listas são Varejo, Restaurantes, Revenda e Amigos.\n"
            "Não crie pedido nem cliente."
        ),
    },
    {
        "tela": "contas",
        "titulo": "Contas",
        "cliente_da_tela": False,
        "observacao_com": False,
        "instrucao": "A frase é sobre contas a receber ou a pagar. Não crie pedido.",
    },
    {
        "tela": "colaboradores",
        "titulo": "Colaboradores",
        "cliente_da_tela": False,
        "observacao_com": False,
        "instrucao": "A frase mexe no colaborador: nome, papel, celular ou escala. Não crie pedido.",
    },
]

ORDEM = [item["tela"] for item in BASE]
TELAS = set(ORDEM)

# Textos da versão anterior. Só troca a linha que ainda está igual a este seed.
ANTIGAS = {
    "pedidos": (
        "A conversa pode ter vários clientes. Um nome em linha própria abre o pedido dele.\n"
        "\"com a Fulana\" na linha do item é observação: não é cliente e não faz parte do produto.\n"
        "A observação vai no campo observacao do item.\n"
        "Se a frase disser só alface, o produto é Alface. Não escolha a variedade.\n"
        "Cliente já aberto na tela, quando houver um só: {cliente}. Data da tela: {data}. Tabela: {tabela}."
    ),
    "funil": (
        "O operador está no pedido de {cliente}.\n"
        "Data de referência: {data}. Tabela: {tabela}. Endereço: {endereco}.\n"
        "A frase é lançamento deste cliente. Não abra outro cliente, mesmo que apareça um nome de pessoa.\n"
        "Cada data em linha própria (28/10, 29/10) é uma nota deste mesmo cliente.\n"
        "\"com a Fulana\" é a observação do item. Não entra no produto e não é cliente.\n"
        "Se a frase disser só alface, o produto é Alface. Não escolha americana, crespa, roxa nem frizze.\n"
        "A observação vai no campo observacao do item."
    ),
}


class ContextoIn(BaseModel):
    instrucao: str = ""
    cliente_da_tela: bool = False
    observacao_com: bool = False


def _ensure(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS commerce.contexto_ia (
                tela TEXT PRIMARY KEY,
                titulo TEXT NOT NULL,
                instrucao TEXT NOT NULL,
                cliente_da_tela BOOLEAN NOT NULL DEFAULT FALSE,
                observacao_com BOOLEAN NOT NULL DEFAULT FALSE,
                atualizada_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    )
    for item in BASE:
        db.execute(
            text(
                """
                INSERT INTO commerce.contexto_ia
                    (tela, titulo, instrucao, cliente_da_tela, observacao_com)
                VALUES
                    (:tela, :titulo, :instrucao, :cliente_da_tela, :observacao_com)
                ON CONFLICT (tela) DO NOTHING
                """
            ),
            item,
        )
        antiga = ANTIGAS.get(item["tela"])
        if antiga:
            db.execute(
                text(
                    """
                    UPDATE commerce.contexto_ia
                    SET instrucao = :instrucao, atualizada_em = NOW()
                    WHERE tela = :tela AND instrucao = :antiga
                    """
                ),
                {"tela": item["tela"], "instrucao": item["instrucao"], "antiga": antiga},
            )
    db.commit()


def _linhas(db: Session) -> list:
    rows = db.execute(
        text(
            """
            SELECT tela, titulo, instrucao, cliente_da_tela, observacao_com
            FROM commerce.contexto_ia
            """
        )
    ).mappings().all()
    por_tela = {row["tela"]: row for row in rows}
    saida = []
    for tela in ORDEM:
        row = por_tela.get(tela)
        if not row:
            continue
        saida.append(
            {
                "tela": row["tela"],
                "titulo": row["titulo"],
                "instrucao": row["instrucao"],
                "cliente_da_tela": bool(row["cliente_da_tela"]),
                "observacao_com": bool(row["observacao_com"]),
            }
        )
    return saida


@router.get("")
def listar_contextos(db: Session = Depends(get_db_session)):
    _ensure(db)
    return _linhas(db)


@router.put("/{tela}")
def gravar_contexto(tela: str, body: ContextoIn, db: Session = Depends(get_db_session)):
    if tela not in TELAS:
        raise HTTPException(status_code=422, detail="Tela desconhecida")
    instrucao = (body.instrucao or "").strip()
    if len(instrucao) > 8000:
        raise HTTPException(status_code=422, detail="O contexto passou de 8000 caracteres")
    _ensure(db)
    db.execute(
        text(
            """
            UPDATE commerce.contexto_ia SET
                instrucao = :instrucao,
                cliente_da_tela = :cliente_da_tela,
                observacao_com = :observacao_com,
                atualizada_em = NOW()
            WHERE tela = :tela
            """
        ),
        {
            "tela": tela,
            "instrucao": instrucao,
            "cliente_da_tela": body.cliente_da_tela,
            "observacao_com": body.observacao_com,
        },
    )
    db.commit()
    linhas = _linhas(db)
    achada = next((item for item in linhas if item["tela"] == tela), None)
    if not achada:
        raise HTTPException(status_code=404, detail="Não achei o contexto desta tela")
    return achada
