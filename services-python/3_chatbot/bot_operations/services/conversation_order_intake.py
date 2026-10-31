"""
Converte uma conversa colada (WhatsApp) no pedido formal da nota.

O texto passa pelo mesmo AI Service que o Telegram usa (ai_integration).
Antes de devolver, os nomes passam pelo catálogo interno do sítio.
Não grava pedido.
"""

import contextvars
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import structlog

from services.ai_integration import ai_integration

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class OpcoesContexto:
    cliente_fixo: str = ""
    observacao_com: bool = False


_opcoes: contextvars.ContextVar[OpcoesContexto] = contextvars.ContextVar(
    "opcoes_contexto",
    default=OpcoesContexto(),
)

_COM_A = re.compile(r"^(?P<prod>.+?)\s+(?P<obs>com\s+as?\s+.+)$", re.IGNORECASE)
_VARIEDADE_ALFACE = {"americana", "crespa", "roxa", "frizze"}

# Nomes-base alinhados ao cadastro de preços (formato fica em tipo: palito/maço/kg).
CATALOG = [
    "Alface Americana",
    "Alface Crespa",
    "Alface Frizze",
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
    "Dúzia de ovos",
    "Cartela 30 ovos",
    "Jiló",
    "Limão",
    "Pão de queijo",
    "Pimenta cheiro",
    "Rabanete",
    "Repolho",
    "Galo",
    "Galo Vivo",
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
    "alface roxo": "Alface Roxa",
    "alface roxa": "Alface Roxa",
    "alface frise": "Alface Frizze",
    "alface frisee": "Alface Frizze",
    "alface frizze": "Alface Frizze",
    "pao de queijo": "Pão de queijo",
    "jilo": "Jiló",
    "limao": "Limão",
    "pimenta de cheiro": "Pimenta cheiro",
    "cartela": "Cartela 30 ovos",
    "cartelas": "Cartela 30 ovos",
    "cartela 30": "Cartela 30 ovos",
    "cartela 30 ovos": "Cartela 30 ovos",
    "cartelas 30 ovos": "Cartela 30 ovos",
    "cartela de ovos": "Cartela 30 ovos",
    "cartelas de ovos": "Cartela 30 ovos",
    "cartela de 30 ovos": "Cartela 30 ovos",
    "cartelas de 30 ovos": "Cartela 30 ovos",
}

# Cliente fala "roxo"/"americano"; catálogo usa "roxa"/"americana".
_GENERO_TOKEN = {
    "roxo": "roxa",
    "americano": "americana",
    "crespo": "crespa",
    "frise": "frizze",
    "frisee": "frizze",
}

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


def _data_citada(data: str, conversation: str) -> bool:
    """A data da nota foi escrita na conversa, e não inventada."""
    match = _EXPLICIT_DATE.fullmatch((data or "").strip())
    if not match:
        return False
    dia, mes = int(match.group(1)), int(match.group(2))
    formas = {f"{dia:02d}/{mes:02d}", f"{dia}/{mes}", f"{dia:02d}/{mes}", f"{dia}/{mes:02d}"}
    texto = conversation or ""
    return any(re.search(rf"(?<!\d){re.escape(forma)}(?!\d)", texto) for forma in formas)


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


def _singular(key: str) -> str:
    if len(key) > 3 and key.endswith("s"):
        return key[:-1]
    return key


def _norm_token(token: str) -> str:
    """Singular + gênero: 'roxo' casa com 'roxa' do catálogo."""
    base = _singular(token) if len(token) > 3 else token
    return _GENERO_TOKEN.get(base, base)


def _singularizar_palavras(key: str) -> str:
    partes = [_singular(palavra) if len(palavra) > 3 else palavra for palavra in key.split()]
    return " ".join(partes)


def _genero_palavras(key: str) -> str:
    return " ".join(_norm_token(p) for p in (key or "").split())


def canonical_product_name(name: str) -> Tuple[str, bool]:
    """Devolve (nome canônico ou original, se caiu no catálogo)."""
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    if not cleaned:
        return cleaned, False
    key = _fold(cleaned)
    vistos = []
    for candidato in (key, _singular(key), _singularizar_palavras(key), _genero_palavras(key), _genero_palavras(_singularizar_palavras(key))):
        if candidato in vistos:
            continue
        vistos.append(candidato)
        if candidato in _ALIASES_BY_KEY:
            return _ALIASES_BY_KEY[candidato], True
        if candidato in _CATALOG_BY_KEY:
            return _CATALOG_BY_KEY[candidato], True
    return cleaned, False


def _chave_catalogo(nome: str) -> str:
    base = _nome_base(nome)
    canonico, conhecido = canonical_product_name(base)
    if not conhecido:
        return ""
    return _fold(canonico)


def extract_json_array(reply: str) -> List[Dict[str, Any]]:
    text = (reply or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1)
    obj_start = text.find("{")
    arr_start = text.find("[")
    if obj_start != -1 and (arr_start == -1 or obj_start < arr_start):
        obj_end = text.rfind("}")
        if obj_end > obj_start:
            parsed = json.loads(text[obj_start : obj_end + 1])
            if isinstance(parsed, dict):
                pedidos = parsed.get("pedidos")
                if isinstance(pedidos, list):
                    return [item for item in pedidos if isinstance(item, dict)]
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


# Chave sem acento: "jilo" casa com "Jiló", "pao de queijo" com "Pão de queijo".
_CATALOG_BY_KEY = {_fold(name): name for name in CATALOG}
_ALIASES_BY_KEY = {_fold(chave): alvo for chave, alvo in ALIASES.items()}


def _nome_base(produto: str) -> str:
    sem = re.sub(r"\s*\([^)]*\)\s*", " ", produto or "")
    sem = re.sub(r"\bpalitos?\b", " ", sem, flags=re.IGNORECASE)
    sem = re.sub(r"\bde\b", " ", sem, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", sem).strip()


def _linha_cabecalho_cliente(linha: str, cliente: str) -> bool:
    """True se a linha é só o nome do cliente (título do bloco), não um item."""
    alvo = _fold(cliente)
    if not alvo:
        return False
    limpa = _fold(re.sub(r"[#*_`>-]+", " ", linha or ""))
    if not limpa:
        return False
    if limpa == alvo:
        return True
    # "**Emerson**" ou "Emerson:" sem quantidade/produto longo
    if limpa.startswith(alvo) and len(limpa) <= len(alvo) + 4:
        return True
    return False


def _trecho_do_cliente(conversation: str, cliente: str, clientes: List[str]) -> str:
    """Só o bloco daquele cliente no texto colado, para não misturar palito de outro."""
    if not (conversation or "").strip() or not (cliente or "").strip():
        return conversation or ""
    linhas = (conversation or "").splitlines()
    inicio = next((i for i, linha in enumerate(linhas) if _linha_cabecalho_cliente(linha, cliente)), None)
    if inicio is None:
        return conversation or ""
    outros = [_fold(nome) for nome in clientes if _fold(nome) and _fold(nome) != _fold(cliente)]
    fim = len(linhas)
    for i in range(inicio + 1, len(linhas)):
        limpa = _fold(re.sub(r"[#*_`>-]+", " ", linhas[i] or ""))
        if limpa and any(limpa == outro or (limpa.startswith(outro) and len(limpa) <= len(outro) + 4) for outro in outros):
            fim = i
            break
    return "\n".join(linhas[inicio:fim])


def _aplicar_palito(items: List[Dict[str, Any]], conversation: str, cliente: str = "", clientes: Optional[List[str]] = None) -> None:
    """'um palito de alface crespa' é palito. 'uma acelga' na mesma linha não herda palito."""
    trecho = _trecho_do_cliente(conversation, cliente, clientes or [])
    if not re.search(r"\bpalitos?\b", _fold(trecho or "")):
        return
    for item in items:
        if _fold(str(item.get("tipo") or "")) == "palito":
            continue
        bruto = str(item.get("produto") or "")
        if re.search(r"\bpalitos?\b", _fold(bruto)):
            base_texto = _nome_base(bruto)
            canonico, conhecido = canonical_product_name(base_texto)
            item["produto"] = f"{canonico if conhecido else _titulo_produto(base_texto)} (palito)"
            item["tipo"] = "palito"
            if conhecido:
                item["conhecido"] = True
            continue
        qtd = float(item.get("qtd") or 0)
        for quantidade, nome, unidade, _obs in _mencoes_de_quantidade(trecho):
            if float(quantidade) != qtd:
                continue
            falado = f"{unidade} {nome}".strip()
            if not re.search(r"\bpalitos?\b", _fold(falado)):
                continue
            perto = _produto_proximo(falado)
            if perto and _tokens_produto(perto[0]) == _tokens_produto(bruto):
                item["produto"] = f"{perto[0]} (palito)"
                item["tipo"] = "palito"
                item["conhecido"] = True
                break
            if _item_ja_cobre(falado, [item]) or _item_ja_cobre(bruto, [{"produto": falado}]):
                base_texto = _nome_base(bruto)
                canonico, conhecido = canonical_product_name(base_texto)
                item["produto"] = f"{canonico if conhecido else _titulo_produto(base_texto)} (palito)"
                item["tipo"] = "palito"
                if conhecido:
                    item["conhecido"] = True
                break


_STOP_PRODUTO = {"de", "do", "da", "dos", "das", "com", "para", "pro", "pra", "um", "uma"}
_FORMATO_DISTINTO = {"cartela", "palito", "bandeja", "caixa", "pacote", "saco", "lata", "duzia", "maco"}
_UNIDADE_NOME = {
    "kg": "kg",
    "g": "g",
    "quilo": "kg",
    "quilos": "kg",
    "kilo": "kg",
    "kilos": "kg",
    "duzia": "dúzia",
    "duzias": "dúzia",
    "maco": "maço",
    "macos": "maço",
    "marcio": "maço",
    "massa": "maço",
    "massas": "maço",
    "bandeja": "bandeja",
    "bandejas": "bandeja",
    "caixa": "caixa",
    "caixas": "caixa",
    "pacote": "pacote",
    "pacotes": "pacote",
    "pct": "pacote",
    "lata": "lata",
    "latas": "lata",
    "saco": "saco",
    "sacos": "saco",
    "un": "unidade",
    "und": "unidade",
    "unid": "unidade",
    "unidade": "unidade",
    "unidades": "unidade",
}
_FORMATO_TOKEN = {
    "un": "unidade",
    "und": "unidade",
    "unid": "unidade",
    "unidade": "unidade",
    "duzia": "dúzia",
    "maco": "maço",
    "marcio": "maço",
    "massa": "maço",
    "palito": "palito",
}
_UNIDADE_RE = re.compile(
    r"^(?P<un>kg|g|quilos?|kilos?|unidades?|unid|und|un|d[uú]zias?|ma[cç]os?|m[aá]rcio|massas?|bandejas?|caixas?|pacotes?|pct|latas?|sacos?)\b(?:\s+de)?\s+(?P<prod>.+)$",
    re.IGNORECASE,
)
_QTD_EXTENSO = {
    "um": 1,
    "uma": 1,
    "dois": 2,
    "duas": 2,
    "tres": 3,
    "quatro": 4,
    "cinco": 5,
    "seis": 6,
    "sete": 7,
    "oito": 8,
    "nove": 9,
    "dez": 10,
    "onze": 11,
    "doze": 12,
    "treze": 13,
    "quatorze": 14,
    "catorze": 14,
    "quinze": 15,
    "dezesseis": 16,
    "dezessete": 17,
    "dezoito": 18,
    "dezenove": 19,
    "vinte": 20,
}
_QTD_PALAVRA_RE = (
    "dezesseis|dezessete|dezoito|dezenove|quatorze|catorze|quinze|doze|duas|dois|"
    "treze|quatro|cinco|oito|nove|sete|seis|tres|tr[eê]s|onze|vinte|uma|um|dez"
)
# Aceita 0,5 / 0.5 — senão "0,5kg" vira só o "5".
_QTD_NUMERO = r"\d{1,4}(?:[.,]\d{1,3})?"
_QTD_TOKEN = rf"(?:{_QTD_PALAVRA_RE}|{_QTD_NUMERO})"
_UNIDADE_COLADA = (
    r"kg|g|quilos?|kilos?|unidades?|unid|und|un|d[uú]zias?|ma[cç]os?|m[aá]rcio|massas?|"
    r"bandejas?|caixas?|pacotes?|pct|latas?|sacos?|cartelas?|palitos?"
)
# '1kg' / '2kg' / '0,5kg' colado — sem espaço a quantidade não era reconhecida e virava "nome".
_QTD_UNIDADE_COLADA = re.compile(
    rf"(?P<qtd>{_QTD_TOKEN})(?P<un>{_UNIDADE_COLADA})\b",
    re.IGNORECASE,
)
_MENCAO_QTD = re.compile(
    rf"(?:(?<![A-Za-zÀ-ÿ])(?P<palavra>{_QTD_PALAVRA_RE})(?![A-Za-zÀ-ÿ])|(?<![\d/])(?P<numero>{_QTD_NUMERO})(?![\d/]))\s+(?P<resto>.+)",
    re.IGNORECASE,
)


def _separar_qtd_unidade(texto: str) -> str:
    """'1kg de jiló' → '1 kg de jiló' para achar quantidade e item."""
    return _QTD_UNIDADE_COLADA.sub(lambda m: f"{m.group('qtd')} {m.group('un')}", texto or "")


def _palavras_produto(nome: str) -> set:
    base = _fold(_nome_base(nome))
    return {p for p in base.split() if len(p) >= 3 and p not in _STOP_PRODUTO and not p.isdigit()}


def _tokens_produto(nome: str) -> List[str]:
    return [_norm_token(p) for p in _palavras_produto(nome)]


def _palavras_cruas(frase: str) -> List[str]:
    """Conserva palito e dúzia. _tokens_produto tira o palito do nome."""
    return [
        _norm_token(p)
        for p in _fold(frase).split()
        if len(p) >= 3 and p not in _STOP_PRODUTO and not p.isdigit()
    ]


def _produto_proximo(frase: str) -> Optional[Tuple[str, str]]:
    """'dúzias de ovos' é Dúzia de ovos. 'dois palitos de alface roxa' é Alface Roxa no palito."""
    crus = _palavras_cruas(frase)
    if not crus:
        return None
    formatos = []
    nomes = []
    for token in crus:
        forma = _FORMATO_TOKEN.get(token)
        if forma:
            formatos.append(forma)
        elif token not in nomes:
            nomes.append(token)

    def coberto(produto: str) -> bool:
        partes = _tokens_produto(produto)
        return bool(partes) and all(parte in crus for parte in partes)

    cobertos = [nome for nome in CATALOG if coberto(nome)]
    if cobertos:
        maior = max(len(_tokens_produto(nome)) for nome in cobertos)
        melhores = [nome for nome in cobertos if len(_tokens_produto(nome)) == maior]
        if len(melhores) == 1:
            return melhores[0], _tipo_que_sobra(melhores[0], formatos)
    if not nomes:
        return None
    parciais = [nome for nome in CATALOG if all(token in _tokens_produto(nome) for token in nomes)]
    if len(parciais) != 1:
        return None
    return parciais[0], _tipo_que_sobra(parciais[0], formatos)


def _tipo_que_sobra(produto: str, formatos: List[str]) -> str:
    partes = set(_tokens_produto(produto))
    for forma in formatos:
        chave = _singular(forma) if len(forma) > 3 else forma
        if chave in partes or forma in partes:
            continue
        if forma in ("unidade", "palito", "maço"):
            return forma
    return ""


def _frase_do_item(produto: str, qtd: float, tipo: str, conversation: str) -> str:
    """A linha da conversa guarda 'dúzias de ovos' quando a nota já encurtou para Ovos."""
    base = [token for token in _tokens_produto(produto) if token not in _FORMATO_TOKEN]
    melhor = f"{tipo} {produto}".strip()
    tamanho = len(_tokens_produto(melhor))
    if not base:
        return melhor
    for quantidade, nome, unidade, _obs in _mencoes_de_quantidade(conversation):
        if float(quantidade) != float(qtd):
            continue
        pedaco = f"{unidade} {nome}".strip()
        tokens = _tokens_produto(pedaco)
        if all(token in tokens for token in base) and len(tokens) >= tamanho:
            melhor = pedaco
            tamanho = len(tokens)
    return melhor


def _item_ja_cobre(produto: str, items: List[Dict[str, Any]]) -> bool:
    chave = _chave_catalogo(produto)
    if chave and any(_chave_catalogo(str(item.get("produto") or "")) == chave for item in items):
        return True
    novas = {_singular(p) if len(p) > 3 else p for p in _palavras_produto(produto)}
    if not novas:
        return True
    for item in items:
        atuais = {_singular(p) if len(p) > 3 else p for p in _palavras_produto(str(item.get("produto") or ""))}
        if not atuais:
            continue
        if novas == atuais or novas <= atuais:
            extra = atuais - novas
            if not extra or not extra <= _FORMATO_DISTINTO:
                return True
    return False


def _titulo_produto(nome: str) -> str:
    limpo = re.sub(r"\s+", " ", nome).strip(" .,;:-")
    if not limpo:
        return ""
    return limpo[0].upper() + limpo[1:]


def _numero_da_quantidade(token: str) -> Optional[float]:
    texto = (token or "").strip()
    if not texto:
        return None
    if re.fullmatch(r"\d{1,4}(?:[.,]\d{1,3})?", texto):
        valor = float(texto.replace(",", "."))
        return valor if 0 < valor <= 999 else None
    return _QTD_EXTENSO.get(_fold(texto))


# O "30" de "cartela de 30 ovos" não é quantidade de outro item.
_CARTELA_NUM_OVOS = re.compile(
    r"\b(cartelas?\s+(?:de\s+)?)(\d{1,3})(\s+ovos?)\b",
    re.IGNORECASE,
)
_FALA_PAGO = re.compile(
    r"(?:^|[\s\-–—,;.(])((?:ja\s+)?pag[oa]s?|pagou)(?=$|[\s\-–—,;.!)])",
    re.IGNORECASE,
)


def _mascarar_cartela_ovos(texto: str) -> Tuple[str, List[str]]:
    """Esconde 'cartela de 30 ovos' para o '30' não virar outro item."""
    guardados: List[str] = []

    def guardar(match: re.Match) -> str:
        guardados.append(match.group(0))
        return f"«CART{len(guardados) - 1}»"

    return _CARTELA_NUM_OVOS.sub(guardar, texto or ""), guardados


def _restaurar_cartela_ovos(texto: str, guardados: List[str]) -> str:
    saida = texto or ""
    for indice, original in enumerate(guardados):
        saida = saida.replace(f"«CART{indice}»", original)
    return saida


def _fala_pago(texto: str) -> bool:
    return bool(_FALA_PAGO.search(_fold(texto or "")))


def _sem_fala_pago(texto: str) -> str:
    limpo = _FALA_PAGO.sub(" ", texto or "")
    limpo = re.sub(r"\s*[\-–—]+\s*$", "", limpo)
    return re.sub(r"\s+", " ", limpo).strip(" .,;:-")


def _so_o_produto(nome: str) -> str:
    """'cebolinhas, 2 couve, 2 alface' é a frase inteira, não um produto."""
    mascarado, guardados = _mascarar_cartela_ovos(nome or "")
    # (?<!\d) evita partir "0,5 kg" como se a vírgula separasse itens.
    corte = re.split(
        rf"(?<!\d)\s*,\s*(?={_QTD_TOKEN}\b)|\s+e\s+(?={_QTD_TOKEN}\b)|\s+(?={_QTD_TOKEN}\s+[A-Za-zÀ-ÿ])",
        mascarado,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return _restaurar_cartela_ovos(corte, guardados).strip(" .,;:-")


def _clausulas(texto: str) -> List[str]:
    """Parte também no meio da linha: 'um palito ... um palito ...' são dois itens."""
    saida = []
    mascarado, guardados = _mascarar_cartela_ovos(texto or "")
    for bloco in re.split(r"[\n;]+", mascarado):
        for pedaco in re.split(
            rf"(?:(?<!\d),\s*|\s+e\s+)(?={_QTD_TOKEN}\b(?!/))",
            bloco,
            flags=re.IGNORECASE,
        ):
            for clausula in re.split(rf"(?<=\S)\s+(?={_QTD_TOKEN}\b(?!/))", pedaco, flags=re.IGNORECASE):
                limpa = _restaurar_cartela_ovos(clausula, guardados).strip(" .,;:-")
                if limpa:
                    saida.append(limpa)
    return saida


def _partir_com(nome: str) -> Tuple[str, str]:
    """'alface com a Polianna' vira produto alface e observação 'com a Polianna'."""
    texto = re.sub(r"\s+", " ", (nome or "").strip())
    achado = _COM_A.match(texto)
    if not achado:
        return texto, ""
    prod = achado.group("prod").strip(" .,;:-")
    obs = re.sub(r"\s+", " ", achado.group("obs")).strip(" .,;:-")
    if not prod or not obs or not _palavras_produto(prod) or len(obs.split()) < 3:
        return texto, ""
    return prod, obs


def _sem_variedade_inventada(produto: str, frase: str) -> str:
    """'Alface Americana' só fica se a frase disser americana, crespa, roxa ou frizze."""
    base = _nome_base(produto)
    palavras = base.split()
    if len(palavras) < 2 or _norm_token(_fold(palavras[0])) != "alface":
        return produto
    frase_norm = {_norm_token(p) for p in _fold(frase).split()}
    extras = [p for p in palavras if _norm_token(_fold(p)) in _VARIEDADE_ALFACE]
    if not extras or all(_norm_token(_fold(p)) in frase_norm for p in extras):
        return produto
    resto = [p for p in palavras if p not in extras]
    if not resto:
        return produto
    limpo = " ".join(resto)
    formato = re.search(r"\(([^)]+)\)\s*$", produto or "")
    if formato and _norm_token(_fold(formato.group(1))) not in _VARIEDADE_ALFACE:
        return f"{limpo} ({formato.group(1).strip()})"
    return limpo


def _mencoes_de_quantidade(texto: str) -> List[Tuple[float, str, str, str]]:
    """Cada 'dois palitos', '0,5 kg' ou '02 kg' vira quantidade, nome e unidade."""
    achados = []
    for clausula in _clausulas(_sem_fala_pago(_separar_qtd_unidade(texto))):
        achado = _MENCAO_QTD.search(clausula)
        if not achado:
            continue
        qtd = _numero_da_quantidade(achado.group("palavra") or achado.group("numero") or "")
        if not qtd:
            continue
        resto = achado.group("resto").strip()
        resto = re.split(r"\s+(?:para|pro|pra)\b", resto, maxsplit=1, flags=re.IGNORECASE)[0]
        resto = re.split(r"\s+\d{1,2}/\d{1,2}\b", resto, maxsplit=1)[0]
        resto = re.split(r"\s+(?:na|no|nas|nos|do|da|dos|das)\b", resto, maxsplit=1, flags=re.IGNORECASE)[0]
        resto = _sem_fala_pago(resto)
        # "cartelas de 30 ovos - Copinhos Bar" (eco do nome na linha seguinte)
        resto = re.split(r"\s*[\-–—]+\s+[A-Za-zÀ-ÿ].*$", resto, maxsplit=1)[0]
        resto = _so_o_produto(resto)
        if not resto:
            continue
        unidade = ""
        medida = _UNIDADE_RE.match(resto)
        if medida:
            unidade = _UNIDADE_NOME.get(_fold(medida.group("un")), "")
            resto = medida.group("prod").strip(" .,;:-")
        obs = ""
        if _opcoes.get().observacao_com:
            resto, obs = _partir_com(resto)
        if _palavras_produto(resto):
            achados.append((qtd, resto, unidade, obs))
    return achados


def _cita_cliente(texto: str, cliente: str) -> bool:
    frase = set(_fold(texto).split())
    palavras = [p for p in _fold(cliente).split() if len(p) >= 4]
    return any(p in frase for p in palavras)


def _anexar_mencao(order: Dict[str, Any], qtd: float, nome: str, unidade: str, observacao: str = "") -> None:
    perto = _produto_proximo(f"{unidade} {nome}".strip())
    if perto:
        titulo, tipo = perto
        conhecido = True
        if not tipo and unidade and unidade != "unidade":
            tipo = unidade
    else:
        titulo = _titulo_produto(nome)
        tipo = unidade if unidade and unidade != "unidade" else ""
        if not titulo:
            return
        canonico, conhecido = canonical_product_name(titulo)
        titulo = canonico if conhecido else titulo
        if tipo:
            titulo = f"{titulo} ({tipo})"
    # Já existe: a quantidade da conversa manda (ex.: IA pôs 10 no cheiro-verde
    # e a frase era "10 maço de couve quatro massas de cheiro Verde").
    for existente in order["itens"]:
        if not (
            _item_ja_cobre(titulo, [existente])
            or _item_ja_cobre(str(existente.get("produto") or ""), [{"produto": titulo}])
        ):
            continue
        existente["qtd"] = qtd
        if tipo:
            existente["tipo"] = tipo
        if conhecido:
            existente["conhecido"] = True
        if observacao and not str(existente.get("observacao") or "").strip():
            existente["observacao"] = observacao
        return
    item = {
        "produto": titulo,
        "qtd": qtd,
        "valor": 0,
        "conhecido": conhecido,
        "preco_tabela": False,
    }
    if tipo:
        item["tipo"] = tipo
    if observacao:
        item["observacao"] = observacao
    order["itens"].append(item)


def _anexar_mencoes(order: Dict[str, Any], texto: str) -> None:
    for qtd, nome, unidade, obs in _mencoes_de_quantidade(texto):
        _anexar_mencao(order, qtd, nome, unidade, obs)


def _completar_itens_omitidos(orders: List[Dict[str, Any]], conversation: str) -> None:
    """A IA às vezes descarta o que não é hortaliça. A quantidade na frase entra mesmo assim."""
    if not (conversation or "").strip() or not orders:
        return
    if len(orders) == 1:
        _anexar_mencoes(orders[0], conversation)
        return
    clientes = [str(order.get("cliente") or "") for order in orders]
    proprios = []
    for order in orders:
        trecho = _trecho_do_cliente(conversation, str(order.get("cliente") or ""), clientes)
        if trecho.strip() != conversation.strip():
            proprios.append((order, trecho))
    if len(proprios) == len(orders):
        for order, trecho in proprios:
            _anexar_mencoes(order, trecho)
        return
    atual: Optional[Dict[str, Any]] = None
    for clausula in _clausulas(conversation):
        citados = [order for order in orders if _cita_cliente(clausula, str(order.get("cliente") or ""))]
        if len(citados) == 1:
            atual = citados[0]
        if atual is None:
            continue
        _anexar_mencoes(atual, clausula)


def normalize_orders(raw_orders: List[Dict[str, Any]], conversation: str = "") -> List[Dict[str, Any]]:
    orders = []
    conversation = _conversa_limpa(conversation)
    data_conversa = delivery_date_from_text(conversation)
    clientes = [str(raw.get("cliente") or "").strip() for raw in raw_orders if isinstance(raw, dict)]
    for raw in raw_orders:
        if not isinstance(raw, dict):
            continue
        items = []
        for item in raw.get("itens") or []:
            if not isinstance(item, dict):
                continue
            bruto = _so_o_produto(_sem_fala_pago(str(item.get("produto") or "")))
            tipo_falado = item.get("tipo") if isinstance(item.get("tipo"), str) else ""
            qtd = _number(item.get("qtd"), 0)
            if qtd <= 0 or not bruto:
                continue
            obs_item = str(item.get("observacao") or "").strip()
            if _opcoes.get().observacao_com:
                bruto, obs_partida = _partir_com(bruto)
                if obs_partida and not obs_item:
                    obs_item = obs_partida
            cliente_bruto = str(raw.get("cliente") or "").strip()
            trecho = _trecho_do_cliente(conversation, cliente_bruto, clientes) if cliente_bruto else conversation
            frase = _frase_do_item(bruto, qtd, tipo_falado, trecho or conversation)
            perto = _produto_proximo(frase) or _produto_proximo(f"{tipo_falado} {bruto}".strip()) or _produto_proximo(bruto)
            if perto:
                produto, tipo_resolvido = perto
                conhecido = True
            else:
                produto, conhecido = canonical_product_name(bruto)
                tipo_resolvido = tipo_falado.strip()
            if not produto:
                continue
            ajustado = _sem_variedade_inventada(produto, trecho or conversation)
            if ajustado != produto:
                produto = ajustado
                conhecido = False
            normalized = {
                "produto": produto,
                "qtd": qtd,
                "valor": 0,
                "conhecido": conhecido,
                "preco_tabela": False,
            }
            if tipo_resolvido:
                normalized["tipo"] = tipo_resolvido
            if obs_item:
                normalized["observacao"] = obs_item[:300]
            if _fold(str(normalized.get("tipo") or "")) == "palito" and "palito" not in _fold(str(normalized.get("produto") or "")):
                nome = str(normalized["produto"])
                if nome[:1].islower():
                    nome = nome[:1].upper() + nome[1:]
                normalized["produto"] = f"{nome} (palito)"
            items.append(normalized)
        cliente = _opcoes.get().cliente_fixo.strip()
        _aplicar_palito(items, conversation, cliente, clientes)
        for item in items:
            if not str(item.get("tipo") or "").strip():
                item["tipo"] = "unidade"
        data = str(raw.get("data") or "").strip()
        if not _data_citada(data, conversation):
            data = data_conversa or (data if is_real_date(data) else "")
        orders.append(
            {
                "cliente": cliente,
                "data": data,
                "endereco": "",
                "desconto": 0,
                "pago": False,
                "itens": items,
            }
        )
    data_conversa = delivery_date_from_text(conversation)
    data_lote = next((order["data"] for order in orders if is_real_date(order["data"])), "") or data_conversa
    if data_lote:
        for order in orders:
            if not is_real_date(order["data"]):
                order["data"] = data_lote
    orders = _unir_mesmo_cliente(orders, conversation)
    _completar_itens_omitidos(orders, conversation)
    for order in orders:
        order["itens"] = _fundir_mesmo_produto(order["itens"])
        order["itens"] = _limpar_ovos_soltos_da_cartela(order["itens"], conversation)
    # Cliente já aberto na tela: "Quarta-feira" e "Deixamos" não são outros clientes.
    if not _opcoes.get().cliente_fixo.strip():
        orders = _redistribuir_blocos(orders, conversation)
    return [order for order in orders if order["cliente"] or order["itens"]]


def _mesmo_item(item: Dict[str, Any], items: List[Dict[str, Any]]) -> bool:
    produto = str(item.get("produto") or "")
    chave = _chave_catalogo(produto) or _fold(_nome_base(produto))
    formato = str(item.get("tipo") or "")
    if not chave:
        return False
    for outro in items:
        outro_nome = str(outro.get("produto") or "")
        outra = _chave_catalogo(outro_nome) or _fold(_nome_base(outro_nome))
        if outra == chave and str(outro.get("tipo") or "") == formato:
            return True
    return False


_LINHA_DATA = re.compile(r"^\d{1,2}/\d{1,2}(?:/\d{2,4})?$")
# [12/10 17:53], [22/10/2026, 07:56] ou [07:56, 22/10/2026]
_WHATS_TS = re.compile(
    r"^\[(?:"
    r"(?P<data_a>\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s*,?\s*(?P<hora_a>\d{1,2}:\d{2}(?::\d{2})?)"
    r"|"
    r"(?P<hora_b>\d{1,2}:\d{2}(?::\d{2})?)\s*,\s*(?P<data_b>\d{1,2}/\d{1,2}(?:/\d{2,4})?)"
    r")\]\s*"
)
_WHATS_LOJA = re.compile(r"^(?:s[ií]tio\s+multitrem|multitrem)\s*:\s*", re.IGNORECASE)
_WHATS_MSG = re.compile(r"^(?P<nome>.+?)\s*:\s*(?P<corpo>.*)$")
_WHATS_EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "\U0000FE0F"
    "\U0000200D"
    "]+",
)
_PREP_DATA = r"(?:(?:para|pro|pra|no|na)\b|p/)"
_MEIO_DATA = r"(?:(?:o|a)\s+)?(?:(?:dia|entrega|entregar)\s+)?(?:de\s+)?"
_DATA_CURTA = r"\d{1,2}/\d{1,2}(?:/\d{2,4})?"
_DIA_SEMANA = r"(?:segunda|ter[cç]a|quarta|quinta|sexta|s[aá]bado|domingo)(?:-feira)?"
_LINHA_SO_DATA = re.compile(
    rf"^(?:{_PREP_DATA}\s*)?{_MEIO_DATA}(?P<data>{_DATA_CURTA})(?:\s+{_DIA_SEMANA})?\s*[.!]?\s*$",
    re.IGNORECASE,
)
_DATA_NO_NOME = re.compile(
    rf"^(?P<nome>.+?)\s+{_PREP_DATA}\s*{_MEIO_DATA}(?P<data>{_DATA_CURTA})\s*[.!]?\s*$",
    re.IGNORECASE,
)
_COMECA_QTD = re.compile(rf"^(?:{_QTD_TOKEN})\b", re.IGNORECASE)
_NOTA_SOLTA = {
    "ja", "pagas", "pago", "paga", "pagos", "pagou", "entregue", "entregues",
    "obs", "observacao", "ok", "obrigado", "obrigada",
}
_PALAVRA_ITEM = {
    "kg", "quilo", "quilos", "kilo", "kilos", "cartela", "cartelas", "ovo", "ovos",
    "duzia", "maco", "palito", "palitos", "bandeja", "caixa", "pacote", "saco", "lata",
    "alface", "alfaces", "couve", "cebolinha", "coentro", "salsinha", "salsa", "agriao",
    "jilo", "limao", "rucula", "hortela", "manjericao", "brocolis", "repolho", "rabanete",
}


def _parece_linha_de_item(linha: str) -> bool:
    """Quantidade (3, 01, 1kg, dois) no começo = item, não cliente."""
    texto = _separar_qtd_unidade((linha or "").strip())
    if not texto:
        return False
    if _COMECA_QTD.match(texto):
        return True
    if _MENCAO_QTD.match(texto):
        return True
    if _UNIDADE_RE.match(texto):
        return True
    return False


def _sanear_blocos(blocos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Se '1kg de Jiló' virou bloco/cliente, devolve os itens ao pedido anterior."""
    saida: List[Dict[str, Any]] = []
    for bloco in blocos:
        nome = _nome_sem_data(str(bloco.get("cliente") or ""))
        texto = str(bloco.get("texto") or "")
        # Só funde quando o "nome" é claramente item/pago — não apaga cliente real.
        if nome and (_parece_linha_de_item(nome) or (_fala_pago(nome) and not _linha_de_cliente(_sem_fala_pago(nome)))):
            if saida:
                saida[-1]["texto"] = (str(saida[-1].get("texto") or "") + "\n" + texto).strip()
                saida[-1]["itens"] = True
            else:
                saida.append({"cliente": "", "data": bloco.get("data") or "", "texto": texto, "itens": True})
            continue
        bloco = {**bloco, "cliente": nome}
        saida.append(bloco)
    return saida


def _sem_data_inicial(linha: str) -> str:
    return re.sub(r"^\d{1,2}/\d{1,2}(?:/\d{2,4})?\s*", "", linha or "").strip()


def _data_normalizada(valor: str) -> str:
    texto = (valor or "").strip()
    if not is_real_date(texto):
        return ""
    match = _EXPLICIT_DATE.fullmatch(texto)
    if not match:
        return ""
    return f"{int(match.group(1)):02d}/{int(match.group(2)):02d}"


def _nome_whatsapp(nome: str) -> str:
    """Tira emoji e símbolos do remetente: 'Maria De Lourdes❣️' → 'Maria De Lourdes'."""
    limpo = _WHATS_EMOJI.sub(" ", nome or "")
    limpo = re.sub(r"[❣️❤♥♡·•]+", " ", limpo)
    return re.sub(r"\s+", " ", limpo).strip(" \t.-–—:")


def _conversa_limpa(conversation: str) -> str:
    """Cola do WhatsApp vira data + um nome + itens.

    Várias mensagens da mesma pessoa ([07:56, 22/10/2026] Maria: 2 Rúcula)
    viram um bloco só — um pedido, não uma nota por mensagem.
    """
    saida: List[str] = []
    ultimo_nome = ""
    ultima_data = ""
    for bruta in (conversation or "").splitlines():
        linha = bruta.strip()
        if not linha:
            saida.append("")
            continue
        ts = _WHATS_TS.match(linha)
        if ts:
            data = _data_normalizada(ts.group("data_a") or ts.group("data_b") or "")
            resto = _WHATS_LOJA.sub("", linha[ts.end() :].strip()).strip()
            msg = _WHATS_MSG.match(resto)
            if msg:
                nome = _nome_whatsapp(msg.group("nome"))
                corpo = (msg.group("corpo") or "").strip()
                if data and data != ultima_data:
                    saida.append(data)
                    ultima_data = data
                if nome and _fold(nome) != _fold(ultimo_nome):
                    saida.append(nome)
                    ultimo_nome = nome
                if corpo:
                    saida.append(_separar_qtd_unidade(corpo))
                continue
            if data and data != ultima_data:
                saida.append(data)
                ultima_data = data
            if resto:
                saida.append(_separar_qtd_unidade(resto))
            continue
        resto = _WHATS_LOJA.sub("", linha).strip()
        saida.append(_separar_qtd_unidade(resto if resto else linha))
    return "\n".join(saida)


def _nome_na_linha(linha: str) -> Optional[Tuple[str, str]]:
    """Linha só de itens devolve None. Senão (cliente, resto com quantidade)."""
    texto = _separar_qtd_unidade(linha or "").strip()
    if _parece_linha_de_item(texto):
        # '1 kg de jiló' / '3 alfaces' — item do pedido atual, não novo cliente.
        if not re.search(rf"[A-Za-zÀ-ÿ].*\s+(?:{_QTD_TOKEN})\b", texto, flags=re.IGNORECASE):
            return None
    if _COMECA_QTD.match(texto):
        return None
    achado = re.search(rf"\s+(?:{_QTD_TOKEN})\b(?!/)", texto, flags=re.IGNORECASE)
    if not achado:
        nome = texto.strip(" :.-")
        if nome and _parece_linha_de_item(nome):
            return None
        return (nome, "") if nome else None
    nome = texto[: achado.start()].strip(" :.-—")
    if not nome or _LINHA_DATA.match(nome):
        return None
    if _parece_linha_de_item(nome):
        return None
    return nome, texto[achado.start() :].strip()


def _linha_de_cliente(nome: str) -> bool:
    """Um nome em linha própria abre outro pedido, mesmo sem linha em branco. 'já pagas' não."""
    if _parece_linha_de_item(nome):
        return False
    if _fala_pago(nome):
        return False
    palavras = [
        p
        for p in _fold(nome).split()
        if len(p) >= 3 and p not in _NOTA_SOLTA and p not in _PALAVRA_ITEM and p != "novo"
    ]
    return bool(palavras)


def _blocos_da_conversa(conversation: str) -> List[Dict[str, Any]]:
    """Cada nome em linha própria é outro pedido. A linha em branco não é obrigatória."""
    data = ""
    blocos: List[Dict[str, Any]] = []
    atual: Optional[Dict[str, Any]] = None
    viu_branco = True
    for bruta in (conversation or "").splitlines():
        linha = bruta.strip()
        if not linha:
            viu_branco = True
            continue
        so_data = _LINHA_SO_DATA.match(linha)
        if so_data:
            data = _data_normalizada(so_data.group("data")) or data
            if atual is not None and data:
                atual["data"] = data
            viu_branco = True
            continue
        no_nome = _DATA_NO_NOME.match(linha)
        if no_nome:
            achada = _data_normalizada(no_nome.group("data"))
            if achada:
                data = achada
                if atual is not None:
                    atual["data"] = achada
                linha = no_nome.group("nome").strip(" :.-")
        sem_data = _sem_data_inicial(linha)
        if sem_data and sem_data != linha:
            linha = sem_data
        linha = _separar_qtd_unidade(linha)
        partido = _nome_na_linha(linha)
        if partido and partido[1]:
            atual = {"cliente": partido[0], "data": data, "texto": linha, "itens": True}
            blocos.append(atual)
            viu_branco = False
            continue
        if partido and not partido[1]:
            if atual is not None and atual.get("itens") and not _linha_de_cliente(partido[0]):
                atual["texto"] += "\n" + linha
                viu_branco = False
                continue
            if atual is None or viu_branco or atual.get("itens"):
                atual = {"cliente": partido[0], "data": data, "texto": linha, "itens": False}
                blocos.append(atual)
            else:
                atual["cliente"] = (str(atual.get("cliente") or "") + " " + partido[0]).strip()
                atual["texto"] += "\n" + linha
            viu_branco = False
            continue
        if atual is None:
            atual = {"cliente": "", "data": data, "texto": linha, "itens": True}
            blocos.append(atual)
        else:
            atual["texto"] += "\n" + linha
            atual["itens"] = True
        viu_branco = False
    return _sanear_blocos(blocos)


def _nome_sem_data(cliente: str) -> str:
    """'Ademar para' não é o nome. O 'para' era o começo da data."""
    return re.sub(r"\s+(?:para|pro|pra|dia|entrega|entregar)\s*$", "", cliente or "", flags=re.IGNORECASE).strip()


def _casa_cliente(bloco: str, cliente: str) -> bool:
    a = _fold(bloco)
    b = _fold(cliente)
    if not a or not b:
        return False
    if a == b or a.startswith(b) or b.startswith(a):
        return True
    pa = [p for p in a.split() if len(p) >= 3 and p != "novo"]
    pb = [p for p in b.split() if len(p) >= 3 and p != "novo"]
    if not pa or not pb:
        return False
    curto, longo = (pa, pb) if len(pa) <= len(pb) else (pb, pa)
    return all(any(c == d or (len(c) >= 4 and d.startswith(c)) for d in longo) for c in curto)


def _item_do_bloco(item: Dict[str, Any], texto: str) -> bool:
    """'3 dúzias de ovos' continua sendo o item Dúzia de ovos, mesmo com outro cliente na conversa."""
    produto = str(item.get("produto") or "")
    tipo_item = _fold(str(item.get("tipo") or ""))
    for qtd, nome, unidade, _obs in _mencoes_de_quantidade(texto):
        if float(item.get("qtd") or 0) != float(qtd):
            continue
        falado = f"{unidade} {nome}".strip()
        perto = _produto_proximo(falado)
        tipo_mencao = _fold((perto[1] if perto else "") or unidade or "")
        if tipo_mencao and tipo_mencao in _FORMATO_DISTINTO:
            no_produto = tipo_mencao in set(_tokens_produto(produto))
            if tipo_item and tipo_item != tipo_mencao:
                continue
            if not tipo_item and not no_produto:
                # '10 maço de couve' da Dilma não leva a couve sem maço do Ademar
                continue
        if perto and _tokens_produto(perto[0]) == _tokens_produto(produto):
            return True
        if _item_ja_cobre(falado, [item]) or _item_ja_cobre(produto, [{"produto": falado}]):
            return True
    return False


def _sem_eco(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    saida: List[Dict[str, Any]] = []
    for item in items:
        repetido = False
        for outro in saida:
            if float(item.get("qtd") or 0) != float(outro.get("qtd") or 0):
                continue
            if _item_ja_cobre(str(item.get("produto") or ""), [outro]) or _item_ja_cobre(str(outro.get("produto") or ""), [item]):
                repetido = True
                break
        if not repetido:
            saida.append(item)
    return saida


def _limpar_ovos_soltos_da_cartela(items: List[Dict[str, Any]], texto: str) -> List[Dict[str, Any]]:
    """'02 cartelas de 30 ovos' não gera item Ovos 30 além da Cartela."""
    if not _CARTELA_NUM_OVOS.search(texto or ""):
        return items
    tem_cartela = any(_chave_catalogo(str(item.get("produto") or "")) == _fold("Cartela 30 ovos") for item in items)
    if not tem_cartela:
        return items
    return [
        item
        for item in items
        if _chave_catalogo(str(item.get("produto") or "")) != _fold("Ovos")
    ]


def _redistribuir_blocos(orders: List[Dict[str, Any]], conversation: str) -> List[Dict[str, Any]]:
    """O nome da próxima pessoa não é endereço, e os itens dela não entram na nota anterior."""
    blocos = [bloco for bloco in _blocos_da_conversa(conversation) if _fold(str(bloco.get("cliente") or ""))]
    if len(blocos) == 1 and len(orders) == 1:
        bloco = blocos[0]
        order = orders[0]
        limpo = _nome_sem_data(str(order.get("cliente") or ""))
        if not _casa_cliente(str(bloco["cliente"]), limpo):
            order["cliente"] = bloco["cliente"]
            if bloco.get("data"):
                order["data"] = bloco["data"]
            _anexar_mencoes(order, str(bloco["texto"]))
            order["itens"] = _sem_eco(order["itens"])
        else:
            if limpo != str(order.get("cliente") or ""):
                order["cliente"] = limpo
            if bloco.get("data") and not is_real_date(str(order.get("data") or "")):
                order["data"] = bloco["data"]
        order["pago"] = bool(order.get("pago")) or _fala_pago(str(bloco["texto"]))
        order["itens"] = _limpar_ovos_soltos_da_cartela(order.get("itens") or [], str(bloco["texto"]))
        return orders
    if len(blocos) < 2 and not (len(blocos) == 1 and len(orders) > 1):
        return orders
    nomes = {_fold(str(bloco["cliente"])) for bloco in blocos}
    usados = set()
    itens_usados: List[Dict[str, Any]] = []
    saida: List[Dict[str, Any]] = []
    for bloco in blocos:
        origem = None
        for indice, order in enumerate(orders):
            if indice in usados:
                continue
            if _casa_cliente(str(bloco["cliente"]), str(order.get("cliente") or "")):
                origem = indice
                break
        texto_bloco = str(bloco["texto"])
        if origem is None:
            ordem = {
                "cliente": bloco["cliente"],
                "data": bloco["data"] or next((str(o.get("data") or "") for o in orders if o.get("data")), ""),
                "endereco": "",
                "desconto": 0,
                "pago": _fala_pago(texto_bloco),
                "itens": [],
            }
        else:
            usados.add(origem)
            base = orders[origem]
            ordem = {
                "cliente": _nome_sem_data(str(base.get("cliente") or "")) or bloco["cliente"],
                "data": base.get("data") or bloco["data"],
                "endereco": base.get("endereco") or "",
                "desconto": base.get("desconto") or 0,
                "pago": _fala_pago(texto_bloco),
                "itens": [],
            }
        if _fold(str(ordem.get("endereco") or "")) in nomes:
            ordem["endereco"] = ""
        for order in orders:
            for item in order.get("itens") or []:
                if any(item is marcado for marcado in itens_usados):
                    continue
                if _item_do_bloco(item, texto_bloco):
                    itens_usados.append(item)
                    ordem["itens"].append(item)
        ordem["itens"] = _sem_eco(ordem["itens"])
        _anexar_mencoes(ordem, texto_bloco)
        ordem["itens"] = _sem_eco(ordem["itens"])
        ordem["itens"] = _limpar_ovos_soltos_da_cartela(ordem["itens"], texto_bloco)
        ordem["pago"] = bool(ordem.get("pago")) or _fala_pago(texto_bloco)
        saida.append(ordem)
    return saida


def _unir_mesmo_cliente(orders: List[Dict[str, Any]], conversation: str = "") -> List[Dict[str, Any]]:
    """Um nome na conversa é uma nota. A IA às vezes abre duas para o mesmo cliente.

    Se o mesmo cliente aparece em mais de um bloco (ex.: dois Copinhos no mesmo dia),
    mantém notas separadas — uma pode estar paga e a outra não.
    """
    blocos = [b for b in _blocos_da_conversa(conversation) if _fold(str(b.get("cliente") or ""))] if conversation else []
    vezes: Dict[str, int] = {}
    for bloco in blocos:
        chave = _fold(str(bloco.get("cliente") or ""))
        vezes[chave] = vezes.get(chave, 0) + 1
    saida: List[Dict[str, Any]] = []
    for order in orders:
        nome = _fold(str(order.get("cliente") or ""))
        data = str(order.get("data") or "")
        if not nome:
            saida.append(order)
            continue
        if vezes.get(nome, 0) > 1:
            saida.append(order)
            continue
        existente = next(
            (
                outro
                for outro in saida
                if _fold(str(outro.get("cliente") or "")) == nome and str(outro.get("data") or "") == data
            ),
            None,
        )
        if existente is None:
            saida.append(order)
            continue
        for item in order.get("itens") or []:
            if _mesmo_item(item, existente["itens"]):
                continue
            existente["itens"].append(item)
        if not str(existente.get("endereco") or "").strip() and str(order.get("endereco") or "").strip():
            existente["endereco"] = order.get("endereco")
        if order.get("pago"):
            existente["pago"] = True
    return saida


def _fundir_mesmo_produto(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Salsas e Salsinha são o mesmo item. A segunda menção não entra de novo."""
    saida: List[Dict[str, Any]] = []
    for item in items:
        produto = str(item.get("produto") or "")
        chave = _chave_catalogo(produto) or _fold(_nome_base(produto))
        formato = str(item.get("tipo") or "")
        if chave:
            existente = next(
                (
                    outro
                    for outro in saida
                    if (_chave_catalogo(str(outro.get("produto") or "")) or _fold(_nome_base(str(outro.get("produto") or "")))) == chave
                    and str(outro.get("tipo") or "") == formato
                ),
                None,
            )
            if existente is not None:
                if item.get("conhecido") and not existente.get("conhecido"):
                    existente["produto"] = item.get("produto")
                    existente["conhecido"] = True
                if not existente.get("valor") and item.get("valor"):
                    existente["valor"] = item.get("valor")
                if item.get("observacao") and not str(existente.get("observacao") or "").strip():
                    existente["observacao"] = item.get("observacao")
                continue
        saida.append(item)
    return saida


def _secoes_por_data(conversation: str) -> List[Dict[str, str]]:
    """Cada data em linha própria abre um trecho. '28/10' e depois '29/10' são duas notas."""
    secoes: List[Dict[str, str]] = []
    atual: Optional[Dict[str, str]] = None
    for bruta in (conversation or "").splitlines():
        linha = bruta.strip()
        if not linha:
            continue
        so_data = _LINHA_SO_DATA.match(linha)
        if so_data:
            data = _data_normalizada(so_data.group("data"))
            if not data:
                continue
            atual = {"data": data, "texto": ""}
            secoes.append(atual)
            continue
        if atual is None:
            continue
        atual["texto"] = (atual["texto"] + "\n" + linha).strip()
    return [secao for secao in secoes if secao["texto"].strip()]


def _pedidos_por_data(conversation: str, cliente: str) -> List[Dict[str, Any]]:
    secoes = _secoes_por_data(conversation)
    if len(secoes) < 2 or not cliente.strip():
        return []
    saida: List[Dict[str, Any]] = []
    for secao in secoes:
        order: Dict[str, Any] = {
            "cliente": cliente.strip(),
            "data": secao["data"],
            "endereco": "",
            "desconto": 0,
            "pago": _fala_pago(secao["texto"]),
            "itens": [],
        }
        _anexar_mencoes(order, secao["texto"])
        _aplicar_palito(order["itens"], secao["texto"], cliente, [cliente])
        order["itens"] = _fundir_mesmo_produto(order["itens"])
        if order["itens"]:
            saida.append(order)
    return saida


PROMPT_EXTRACAO = (
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
)

# Contrato da resposta. Vai na chamada da API, fora do prompt.
# A raiz é objeto porque a saída estruturada da OpenAI não aceita array na raiz.
PEDIDO_RESPOSTA_SCHEMA = {
    "name": "pedidos_extraidos",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "pedidos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "data": {"type": "string"},
                        "itens": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "produto": {"type": "string"},
                                    "qtd": {"type": "integer"},
                                    "tipo": {"type": "string"},
                                    "observacao": {"type": "string"},
                                },
                                "required": ["produto", "qtd", "tipo", "observacao"],
                            },
                        },
                    },
                    "required": ["data", "itens"],
                },
            }
        },
        "required": ["pedidos"],
    },
}


def build_prompt(conversation: str, today: Optional[date] = None, contexto: str = "") -> str:
    _ = today
    instrucao = (contexto or "").strip() or PROMPT_EXTRACAO
    return f"{instrucao}\n\nMensagem:\n{(conversation or '').strip()}"


async def convert_conversation(
    conversation: str,
    contexto: str = "",
    cliente_fixo: str = "",
    observacao_com: bool = False,
) -> List[Dict[str, Any]]:
    if ai_integration.client is None:
        await ai_integration.connect()
    conversation = _conversa_limpa(conversation)
    token = _opcoes.set(
        OpcoesContexto(
            cliente_fixo=(cliente_fixo or "").strip(),
            observacao_com=bool(observacao_com),
        )
    )
    try:
        prompt = build_prompt(conversation, contexto=contexto)
        reply = await ai_integration.chat_simple(
            prompt,
            intent="criar_pedido",
            intent_reason="conversa colada na tela de operacao",
            user_id="commerce-frontend",
            response_schema=PEDIDO_RESPOSTA_SCHEMA,
            max_tokens=2000,
        )
        if not reply:
            raise RuntimeError(ai_integration.last_error or "O AI Service não respondeu")
        logger.info("Resposta da IA para conversa colada", reply_preview=reply[:300])
        orders = normalize_orders(extract_json_array(reply), conversation)
        fixo = (cliente_fixo or "").strip()
        if fixo:
            for order in orders:
                order["cliente"] = fixo
            orders = _unir_mesmo_cliente(orders, conversation)
            datas = {curta for curta in (_data_normalizada(secao["data"]) for secao in _secoes_por_data(conversation)) if curta}
            cobertas = {_data_normalizada(str(order.get("data") or "")) for order in orders}
            if len(datas) >= 2 and datas - cobertas:
                fatiados = _pedidos_por_data(conversation, fixo)
                if fatiados:
                    orders = fatiados
        return orders
    finally:
        _opcoes.reset(token)
