"""
Lê uma frase do cadastro e devolve ações para a tela.

A tela aplica as ações na hora. Quem grava é a confirmação do operador.
Usa o mesmo AI Service do Telegram.
"""

import json
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import structlog

from services.ai_integration import ai_integration
from services.conversation_order_intake import canonical_product_name

logger = structlog.get_logger(__name__)

LISTAS = ("Varejo", "Restaurantes", "Revenda", "Amigos")
_LISTA_ALIAS = {
    "varejo": "Varejo",
    "restaurante": "Restaurantes",
    "restaurantes": "Restaurantes",
    "revenda": "Revenda",
    "amigo": "Amigos",
    "amigos": "Amigos",
}


def extract_json_object(reply: str) -> Dict[str, Any]:
    text = (reply or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("A IA não devolveu o comando do cadastro")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("A IA não devolveu o comando do cadastro")
    return parsed


def _text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _money(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip().replace("R$", "").replace(" ", "")
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        try:
            number = float(text)
        except ValueError:
            return None
    if number < 0:
        return None
    return round(number, 2)


def _reais(value: float) -> str:
    texto = f"{value:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _fold(value: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", value)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", sem_acento.casefold()).strip()


_PRECO_LINHA = re.compile(
    r"(?:R\$\s*(\d{1,6}(?:\.\d{3})*(?:,\d{1,2})?|\d{1,6}(?:\.\d{2})?)|(\d{1,6},\d{2}))\s*$",
    re.IGNORECASE,
)
_EMOJI = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF]")


def _listas_na_mensagem(message: str) -> List[str]:
    folded = _fold(message)
    achadas: List[str] = []
    vistas = set()
    for alias, nome in _LISTA_ALIAS.items():
        if alias not in folded or nome.casefold() in vistas:
            continue
        vistas.add(nome.casefold())
        achadas.append(nome)
    return achadas


def _formato_canonico(value: str) -> str:
    texto = re.sub(r"\s+", " ", (value or "").strip())
    chave = _fold(texto)
    if chave in ("", "un", "und", "unid", "unidade"):
        return "unidade"
    if chave == "maco":
        return "maço"
    if chave in ("kg", "quilo", "quilos"):
        return "kg"
    if chave in ("peso fixo", "fixo"):
        return "peso fixo"
    return texto


def _partir_produto(texto: str) -> Tuple[str, str]:
    limpo = re.sub(r"\s+", " ", (texto or "").strip())
    parenteses = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", limpo)
    if parenteses and parenteses.group(1).strip():
        return parenteses.group(1).strip(), _formato_canonico(parenteses.group(2))
    pacote = re.match(r"^(.*?)\s+(c/\s*\d+\s*unidades?)\s*$", limpo, flags=re.IGNORECASE)
    if pacote and pacote.group(1).strip():
        return pacote.group(1).strip(), re.sub(r"\s+", " ", pacote.group(2).strip())
    solto = re.match(r"^(.*?)\s+(unidade|maço|maco|kg|peso fixo)\s*$", limpo, flags=re.IGNORECASE)
    if solto and solto.group(1).strip():
        return solto.group(1).strip(), _formato_canonico(solto.group(2))
    return limpo, ""


def _casar_produto(nome: str, produtos: List[str]) -> List[str]:
    catalogo = []
    for produto in produtos:
        nome_item, formato = _partir_produto(produto)
        catalogo.append(
            {
                "bruto": produto,
                "nome": nome_item,
                "formato": _formato_canonico(formato or "unidade"),
            }
        )
    qualquer = re.match(r"^(.*?)\s*\(\s*qualquer\s+([^)]+?)\s*\)\s*$", re.sub(r"\s+", " ", nome.strip()), flags=re.IGNORECASE)
    if qualquer:
        termo = _fold(qualquer.group(2))
        if not termo:
            return []
        formato_linha = "palito" if re.search(r"\bpalito\b", _fold(qualquer.group(1))) else ""
        rotulos: List[str] = []
        vistos_familia = set()
        for item in catalogo:
            if not re.search(rf"\b{re.escape(termo)}\b", _fold(item["nome"])):
                continue
            formato_alvo = _formato_canonico(formato_linha or item["formato"])
            rotulo = f"{item['nome']} ({formato_alvo})"
            chave_rotulo = _fold(rotulo)
            if chave_rotulo in vistos_familia:
                continue
            vistos_familia.add(chave_rotulo)
            rotulos.append(rotulo)
        return rotulos
    linha = _fold(nome)
    if re.search(r"\b30\b", linha) and "ovo" in linha:
        return [item["bruto"] for item in catalogo if _fold(item["nome"]) == "cartela 30 ovos"][:1]
    if "ovo" in linha and ("duzia" in linha or re.search(r"\b12\b", linha)):
        return [item["bruto"] for item in catalogo if _fold(item["nome"]) == "ovos"][:1]
    nome_linha, formato_linha = _partir_produto(nome)
    key = _fold(nome_linha)
    if not key:
        return []
    candidatos = [item for item in catalogo if _fold(item["nome"]) == key]
    if not candidatos:
        contidos = [item for item in catalogo if _fold(item["nome"]) and _fold(item["nome"]) in key]
        if contidos:
            maior = max(len(_fold(item["nome"])) for item in contidos)
            candidatos = [item for item in contidos if len(_fold(item["nome"])) == maior]
    if not candidatos:
        prefixo = [item for item in catalogo if _fold(item["nome"]).startswith(key)]
        if len(prefixo) == 1:
            candidatos = prefixo
        elif key == "brocolis" and prefixo and all(_fold(item["nome"]).startswith("brocolis") for item in prefixo):
            candidatos = prefixo
    if formato_linha:
        alvo = _formato_canonico(formato_linha)
        return [
            item["bruto"]
            for item in candidatos
            if item["formato"] == alvo or _fold(item["formato"]) == _fold(formato_linha)
        ]
    unidade = [item for item in candidatos if item["formato"] == "unidade"]
    if unidade:
        return [item["bruto"] for item in unidade]
    if len(candidatos) == 1:
        return [candidatos[0]["bruto"]]
    return []


def precos_da_mensagem(message: str, produtos: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Lê uma tabela colada (uma linha por produto) sem depender da IA."""
    listas = _listas_na_mensagem(message)
    if not listas:
        return [], []
    faltando: List[str] = []
    por_chave: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for bruta in re.split(r"[\r\n]+", message or ""):
        linha = _EMOJI.sub("", bruta).strip()
        if not linha:
            continue
        achado = _PRECO_LINHA.search(linha)
        if not achado:
            continue
        valor = _money(achado.group(1) or achado.group(2))
        if valor is None:
            continue
        nome = re.sub(r"\s+", " ", linha[: achado.start()].strip(" -–—:|")).strip()
        if not nome:
            continue
        casados = _casar_produto(nome, produtos)
        if not casados:
            faltando.append(nome)
            continue
        for lista in listas:
            for produto in casados:
                por_chave[(produto.casefold(), lista.casefold())] = {
                    "tipo": "preco",
                    "produto": produto,
                    "lista": lista,
                    "valor": valor,
                }
    return list(por_chave.values()), faltando


def _lista(value: Any) -> Optional[str]:
    text = _text(value)
    if not text:
        return None
    return _LISTA_ALIAS.get(text.casefold())


def _produto(value: Any, produtos: List[str]) -> Optional[str]:
    text = _text(value)
    if not text:
        return None
    canonical, known = canonical_product_name(text)
    by_key = {name.casefold(): name for name in produtos}
    if canonical.casefold() in by_key:
        return by_key[canonical.casefold()]
    if text.casefold() in by_key:
        return by_key[text.casefold()]
    if known:
        return canonical
    return None


def normalize_actions(raw: Any, produtos: List[str]) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    actions: List[Dict[str, Any]] = []
    for item in raw[:80]:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("tipo") or "").strip().casefold()
        if kind == "cliente":
            nome = _text(item.get("nome"))
            if not nome:
                continue
            action: Dict[str, Any] = {"tipo": "cliente", "nome": nome}
            for key in ("celular1", "celular2", "endereco", "localizacao", "observacao"):
                value = _text(item.get(key))
                if value:
                    action[key] = value
            lista = _lista(item.get("preco_base"))
            if lista:
                action["preco_base"] = lista
            actions.append(action)
        elif kind == "preco":
            produto = _produto(item.get("produto"), produtos)
            lista = _lista(item.get("lista"))
            valor = _money(item.get("valor"))
            if produto and lista and valor is not None:
                actions.append({"tipo": "preco", "produto": produto, "lista": lista, "valor": valor})
        elif kind == "desconto":
            cliente = _text(item.get("cliente"))
            produto = _produto(item.get("produto"), produtos)
            desconto = _money(item.get("desconto"))
            if cliente and produto and desconto is not None:
                actions.append({"tipo": "desconto", "cliente": cliente, "produto": produto, "desconto": desconto})
    return actions


def describe_actions(actions: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    labels = {
        "celular1": "celular 1",
        "celular2": "celular 2",
        "endereco": "endereço",
        "localizacao": "localização",
        "observacao": "observação de entrega",
        "preco_base": "preço base",
    }
    for action in actions:
        if action["tipo"] == "cliente":
            changes = [f"{label} para {action[key]}" for key, label in labels.items() if action.get(key)]
            if changes:
                lines.append(f"Atualizei {action['nome']}: " + ", ".join(changes))
            else:
                lines.append(f"Abri o cliente {action['nome']}")
        elif action["tipo"] == "desconto":
            lines.append(f"Desconto de {action['cliente']} em {action['produto']}: {_reais(action['desconto'])}")
    precos = [action for action in actions if action["tipo"] == "preco"]
    if len(precos) == 1:
        action = precos[0]
        lines.append(f"{action['produto']} no preço {action['lista']} ficou {_reais(action['valor'])}")
    elif precos:
        por_lista: Dict[str, List[str]] = {}
        for action in precos:
            por_lista.setdefault(action["lista"], []).append(f"{action['produto']} {_reais(action['valor'])}")
        for lista, itens in por_lista.items():
            lines.append(f"Preço {lista}: " + ", ".join(itens))
    if not lines:
        return ""
    return ". ".join(lines) + ". Confirme para salvar."


def build_prompt(message: str, clientes: List[Dict[str, Any]], produtos: List[str]) -> str:
    pessoas = ", ".join(_text(item.get("nome")) or "" for item in clientes if _text(item.get("nome"))) or "nenhum"
    catalogo = ", ".join(produtos) or "nenhum"
    return (
        "Você atualiza clientes e preços do Sítio Multitrem a partir de uma frase. "
        "Não explique fora do JSON. Responda somente um objeto JSON.\n"
        '{"reply":"Atualizei o celular da Waldeth.","acoes":[]}\n'
        "reply descreve só o que a frase pediu, em uma frase.\n"
        "Cliente, só com os campos que a frase mudou, e o nome para achar a pessoa: "
        '{"tipo":"cliente","nome":"Waldeth","celular1":"62 981414141","celular2":"","endereco":"","localizacao":"","observacao":"","preco_base":"Varejo"}\n'
        "Omita campo vazio.\n"
        "Preço de um produto: "
        '{"tipo":"preco","produto":"Couve","lista":"Varejo","valor":4}\n'
        "lista é só Varejo, Restaurantes, Revenda ou Amigos.\n"
        "Desconto em reais de um cliente num produto: "
        '{"tipo":"desconto","cliente":"Waldeth","produto":"Couve","desconto":0.5}\n'
        "Não invente telefone, endereço, localização nem preço que a frase não trouxe. "
        "Não diga que gravou. A tela mostra e a pessoa confirma depois.\n"
        f"Clientes: {pessoas}.\n"
        f"Produtos: {catalogo}.\n"
        f"Frase: {message}"
    )


async def interpret_cadastro(
    message: str,
    clientes: List[Dict[str, Any]],
    produtos: List[str],
) -> Dict[str, Any]:
    reply = await ai_integration.chat_simple(build_prompt(message, clientes, produtos), intent="CADASTRO")
    if not reply:
        raise RuntimeError(ai_integration.last_error or "O AI Service não respondeu")
    try:
        parsed = extract_json_object(reply)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.info("cadastro sem json", reply=reply[:500])
        raise ValueError("A IA não devolveu o comando do cadastro") from exc
    actions = normalize_actions(parsed.get("acoes"), produtos)
    lidas, faltando = precos_da_mensagem(message, produtos)
    if lidas:
        chaves = {(item["produto"].casefold(), item["lista"].casefold()) for item in lidas}
        demais = [
            item
            for item in actions
            if item["tipo"] != "preco" or (item["produto"].casefold(), item["lista"].casefold()) not in chaves
        ]
        actions = [item for item in demais if item["tipo"] != "preco"] + lidas
        extras = [item for item in demais if item["tipo"] == "preco"]
        actions.extend(extras)
    described = describe_actions(actions)
    if faltando and lidas:
        described = described.replace("Confirme para salvar.", f"Não achei {', '.join(faltando)}. Confirme para salvar.")
    text = described or _text(parsed.get("reply")) or "Não identifiquei o que mudar."
    return {"reply": text, "acoes": actions}
