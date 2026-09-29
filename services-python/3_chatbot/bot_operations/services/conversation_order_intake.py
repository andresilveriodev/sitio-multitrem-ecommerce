"""
Converte uma conversa colada (WhatsApp) no pedido formal da nota.

O texto passa pelo mesmo AI Service que o Telegram usa (ai_integration).
Antes de devolver, os nomes passam pelo catálogo interno do sítio.
Não grava pedido.
"""

import json
import re
import unicodedata
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import structlog

from services.ai_integration import ai_integration

logger = structlog.get_logger(__name__)

CATALOG = [
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
]

ALIASES = {
    "salsa": "Salsinha",
    "salsinha": "Salsinha",
    "cheiro verde": "Cheiro-verde",
    "cheiro-verde": "Cheiro-verde",
    "rucula": "Rúcula",
    "rúcula": "Rúcula",
    "manjericao": "Manjericão",
    "hortela": "Hortelã",
    "brocolis ninja": "Brócolis Ninja",
    "brócolis ninja": "Brócolis Ninja",
    "brocolis piracicaba": "Brócolis Piracicaba",
    "brócolis piracicaba": "Brócolis Piracicaba",
    "almeirao": "Almeirão",
    "cartela": "Cartela 30 ovos",
    "cartela 30": "Cartela 30 ovos",
    "cartela de ovos": "Cartela 30 ovos",
}

_CATALOG_BY_KEY = {name.casefold(): name for name in CATALOG}

_WEEKDAYS = (
    ("segunda", 0),
    ("terça", 1),
    ("terca", 1),
    ("quarta", 2),
    ("quinta", 3),
    ("sexta", 4),
    ("sábado", 5),
    ("sabado", 5),
    ("domingo", 6),
)
_EXPLICIT_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")


def _format_date(value: date) -> str:
    return value.strftime("%d/%m")


def is_real_date(value: str) -> bool:
    match = _EXPLICIT_DATE.fullmatch((value or "").strip())
    if not match:
        return False
    day, month = int(match.group(1)), int(match.group(2))
    return 1 <= day <= 31 and 1 <= month <= 12


def delivery_date_from_text(text: str, today: Optional[date] = None) -> str:
    """Lê 'segunda', 'amanhã' ou '26/09' na conversa."""
    today = today or date.today()
    folded = (text or "").casefold()
    explicit = _EXPLICIT_DATE.search(text or "")
    if explicit and is_real_date(explicit.group(0)):
        return f"{int(explicit.group(1)):02d}/{int(explicit.group(2)):02d}"
    if re.search(r"\bamanh[ãa]\b", folded):
        return _format_date(today + timedelta(days=1))
    if re.search(r"\bhoje\b", folded):
        return _format_date(today)
    for word, weekday in _WEEKDAYS:
        if re.search(rf"\b{word}\b", folded):
            delta = (weekday - today.weekday()) % 7
            return _format_date(today + timedelta(days=delta))
    return ""


def canonical_product_name(name: str) -> Tuple[str, bool]:
    """Devolve (nome canônico ou original, se caiu no catálogo)."""
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    if not cleaned:
        return cleaned, False
    key = cleaned.casefold()
    if key in ALIASES:
        return ALIASES[key], True
    if key in _CATALOG_BY_KEY:
        return _CATALOG_BY_KEY[key], True
    return cleaned, False


def extract_json_array(reply: str) -> List[Dict[str, Any]]:
    text = (reply or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("A IA não devolveu uma lista de pedidos")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, list):
        raise ValueError("A IA não devolveu uma lista de pedidos")
    return parsed


def _number(value: Any, default: float = 0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return default


def _optional_number(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    return _number(value)


def _fold(value: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", value or "")
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", sem_acento.casefold()).strip()


def _nome_base(produto: str) -> str:
    sem = re.sub(r"\s*\([^)]*\)\s*", " ", produto or "")
    sem = re.sub(r"\bpalitos?\b", " ", sem, flags=re.IGNORECASE)
    sem = re.sub(r"\bde\b", " ", sem, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", sem).strip()


def _aplicar_palito(items: List[Dict[str, Any]], conversation: str) -> None:
    """'04 palitos de alface crespa' é Alface Crespa no formato palito, não unidade."""
    linhas = []
    todas = []
    for linha in (conversation or "").splitlines():
        dobrada = _fold(linha)
        if not dobrada:
            continue
        todas.append(dobrada)
        if re.search(r"\bpalitos?\b", dobrada):
            linhas.append((dobrada, [int(n) for n in re.findall(r"\b(\d+)\b", dobrada)]))
    if not linhas:
        return
    for item in items:
        bruto = str(item.get("produto") or "")
        base_texto = _nome_base(bruto)
        canonico, conhecido = canonical_product_name(base_texto)
        base = _fold(canonico if conhecido else base_texto)
        if not base:
            continue
        nome_diz_palito = bool(re.search(r"\bpalitos?\b", _fold(bruto)))
        casa = [(texto, qtds) for texto, qtds in linhas if base in texto]
        if not nome_diz_palito and not casa:
            continue
        if not nome_diz_palito:
            outras = [texto for texto in todas if base in texto and not re.search(r"\bpalitos?\b", texto)]
            if outras:
                qtds = [qtd for _, numeros in casa for qtd in numeros]
                if qtds and item.get("qtd") not in qtds:
                    continue
        item["produto"] = f"{canonico if conhecido else base_texto} (palito)"
        item["tipo"] = "palito"
        if conhecido:
            item["conhecido"] = True


def normalize_orders(raw_orders: List[Dict[str, Any]], conversation: str = "") -> List[Dict[str, Any]]:
    orders = []
    for raw in raw_orders:
        if not isinstance(raw, dict):
            continue
        items = []
        for item in raw.get("itens") or []:
            if not isinstance(item, dict):
                continue
            produto, conhecido = canonical_product_name(str(item.get("produto") or ""))
            if not produto:
                continue
            qtd = _number(item.get("qtd"), 0)
            if qtd <= 0:
                continue
            valor = _number(item.get("valor"), 0)
            if valor < 0:
                valor = 0
            normalized = {
                "produto": produto,
                "qtd": qtd,
                "valor": valor,
                "conhecido": conhecido,
                "preco_tabela": False,
            }
            desconto = _optional_number(item.get("desconto"))
            percentual = _optional_number(item.get("descontoPercentual"))
            if desconto:
                normalized["desconto"] = desconto
            if percentual:
                normalized["descontoPercentual"] = percentual
            tipo = item.get("tipo")
            if isinstance(tipo, str) and tipo.strip():
                normalized["tipo"] = tipo.strip()
            items.append(normalized)
        _aplicar_palito(items, conversation)
        data = str(raw.get("data") or "").strip()
        if not is_real_date(data):
            data = delivery_date_from_text(conversation)
        orders.append(
            {
                "cliente": str(raw.get("cliente") or "").strip(),
                "data": data,
                "endereco": str(raw.get("endereco") or "").strip(),
                "desconto": _number(raw.get("desconto"), 0),
                "itens": items,
            }
        )
    return [order for order in orders if order["cliente"] or order["itens"]]


def build_prompt(conversation: str, today: Optional[date] = None) -> str:
    catalog = ", ".join(CATALOG)
    today = today or date.today()
    hoje = f"{_format_date(today)}/{today.year}"
    return (
        "Você converte uma conversa de pedido de hortaliças do Sítio Multitrem "
        "no JSON interno da nota. Não converse e não explique. "
        "Responda somente um array JSON.\n"
        "Cada pedido: "
        '{"cliente":"","data":"28/09","endereco":"","desconto":0,'
        '"itens":[{"produto":"Couve","qtd":1}]}\n'
        f"Hoje é {hoje}. data é o dia da entrega no formato DD/MM. "
        "segunda, terça, quarta, quinta, sexta, sábado e domingo são o próximo dia com esse nome, inclusive hoje. "
        "amanhã é o dia seguinte. Se a conversa não tiver data, data fica \"\". "
        "Nunca escreva o texto DD/MM.\n"
        "cliente é o nome da pessoa ou do estabelecimento, só se aparecer na conversa. "
        "Se não aparecer, cliente fica \"\". Não invente nome.\n"
        "endereco só se aparecer. desconto do pedido é percentual. "
        "No item, desconto é reais por unidade e descontoPercentual é % da linha. "
        "Omita desconto quando não houver. "
        "valor é o preço unitário só se a conversa informar um número em reais. "
        "Se não informar, omita valor.\n"
        f"Produtos do catálogo, use exatamente estes nomes quando couber: {catalog}.\n"
        "Salsa é Salsinha. Cheiro verde é Cheiro-verde. "
        "'roxa' depois de alface é Alface Roxa. 'crespa' depois de alface é Alface Crespa.\n"
        "palito e palitos são o formato, não outro produto. "
        '"04 palitos de alface crespa" é produto "Alface Crespa (palito)", qtd 4 e tipo "palito". '
        "Não troque palito por unidade. Se a conversa não disser palito, não escreva palito.\n"
        "Se não couber no catálogo, mantenha o nome que a pessoa usou, como rabanete ou repolho.\n"
        "Uma, um e 1 são quantidade 1. Vários clientes viram vários objetos.\n"
        "Ignore cumprimento.\n\n"
        "Conversa:\n"
        f"{conversation.strip()}"
    )


async def convert_conversation(conversation: str) -> List[Dict[str, Any]]:
    if ai_integration.client is None:
        await ai_integration.connect()
    prompt = build_prompt(conversation)
    reply = await ai_integration.chat_simple(
        prompt,
        intent="criar_pedido",
        intent_reason="conversa colada na tela de operacao",
        user_id="commerce-frontend",
    )
    if not reply:
        raise RuntimeError(ai_integration.last_error or "O AI Service não respondeu")
    logger.info("Resposta da IA para conversa colada", reply_preview=reply[:300])
    return normalize_orders(extract_json_array(reply), conversation)
