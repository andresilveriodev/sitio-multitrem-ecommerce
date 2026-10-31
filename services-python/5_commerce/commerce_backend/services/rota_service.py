"""
Monta rota de entrega: geocoding + OSRM trip (quando disponível).
Prioriza o link de localização do cadastro do cliente.
"""

from __future__ import annotations

import re
import time
from decimal import Decimal
from typing import Any, Optional
from urllib.parse import quote_plus, unquote

import httpx
import structlog
from sqlalchemy.orm import Session

from config import settings
from models.commerce import Customer, CustomerAddress

logger = structlog.get_logger()

# Google às vezes devolve lng com "+-" no path: /maps/search/-16.66,+-49.23
_AT_RE = re.compile(r"@(-?\d{1,3}\.\d+)\s*,\s*\+?(-?\d{1,3}\.\d+)")
_BANG_RE = re.compile(r"!3d(-?\d{1,3}\.\d+)!4d(-?\d{1,3}\.\d+)", re.IGNORECASE)
_Q_RE = re.compile(
    r"[?&](?:q|query)=(-?\d{1,3}\.\d+)(?:\s*,\s*|%2C\+?|,\+?)(-?\d{1,3}\.\d+)",
    re.IGNORECASE,
)
_SEARCH_RE = re.compile(
    r"/maps/(?:search|place)/(-?\d{1,3}\.\d+)\s*,\s*\+?(-?\d{1,3}\.\d+)",
    re.IGNORECASE,
)
_PAIR_RE = re.compile(r"(-?\d{1,3}\.\d+)\s*,\s*\+?(-?\d{1,3}\.\d+)")


class Ponto:
    def __init__(
        self,
        rotulo: str,
        endereco: str,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        cliente_id: Optional[int] = None,
        order_id: Optional[str] = None,
        origem: str = "",
        aviso: str = "",
        localizacao: str = "",
    ):
        self.rotulo = rotulo
        self.endereco = endereco
        self.lat = lat
        self.lng = lng
        self.cliente_id = cliente_id
        self.order_id = order_id
        self.origem = origem
        self.aviso = aviso
        self.localizacao = localizacao


def _como_float(valor: Any) -> Optional[float]:
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _par_br(a: float, b: float) -> Optional[tuple[float, float]]:
    """Aceita lat,lng no Brasil (ou invertido)."""
    if -35 <= a <= 5 and -75 <= b <= -30:
        return a, b
    if -35 <= b <= 5 and -75 <= a <= -30:
        return b, a
    return None


def _coords_de_texto(texto: str) -> Optional[tuple[float, float]]:
    if not texto:
        return None
    raw = unquote(texto.strip())
    for regex in (_BANG_RE, _SEARCH_RE, _AT_RE, _Q_RE, _PAIR_RE):
        m = regex.search(raw)
        if not m:
            continue
        par = _par_br(float(m.group(1)), float(m.group(2)))
        if par:
            return par
    return None


def _eh_url_maps(texto: str) -> bool:
    baixo = (texto or "").lower()
    return "http" in baixo and (
        ("google." in baixo and "/maps" in baixo)
        or "maps.google." in baixo
        or "goo.gl" in baixo
        or "maps.app.goo.gl" in baixo
        or "g.co/maps" in baixo
    )


def _expandir_url(url: str) -> str:
    """Segue redirect de maps.app.goo.gl / goo.gl para a URL final com coordenadas."""
    texto = (url or "").strip()
    if not texto.startswith("http"):
        return texto
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(texto)
            final = str(resp.url)
            if _coords_de_texto(final):
                return final
            # Às vezes as coords só vêm no HTML (meta / JSON embutido).
            corpo = resp.text or ""
            coords = _BANG_RE.search(corpo) or _AT_RE.search(corpo)
            if coords:
                par = _par_br(float(coords.group(1)), float(coords.group(2)))
                if par:
                    return f"https://www.google.com/maps/@{par[0]},{par[1]},17z"
            return final
    except Exception as exc:
        logger.warning("Falha ao expandir URL do Maps", url=texto[:120], erro=str(exc))
        return texto


def coords_de_localizacao(texto: str) -> Optional[tuple[float, float]]:
    """Extrai lat/lng do link do cadastro (inclui link curto do Google Maps)."""
    coords = _coords_de_texto(texto)
    if coords:
        return coords
    if not _eh_url_maps(texto):
        return None
    final = _expandir_url(texto)
    if final != texto:
        coords = _coords_de_texto(final)
        if coords:
            return coords
    return None


def _endereco_consulta(endereco: str) -> str:
    texto = (endereco or "").strip()
    if not texto:
        return ""
    baixo = texto.lower()
    if "goiânia" in baixo or "goiania" in baixo or ", go" in baixo:
        return texto
    return f"{texto}, Goiânia, GO"


def _fold_end(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (texto or "").casefold()).strip()


def _default_address(customer: Customer) -> Optional[CustomerAddress]:
    rows = list(customer.addresses or [])
    for row in rows:
        if row.is_default:
            return row
    return rows[0] if rows else None


def _address_para_entrega(customer: Customer, endereco: str) -> Optional[CustomerAddress]:
    """Escolhe o endereço do cadastro que bate com o da boleta (cliente pode ter vários)."""
    rows = list(customer.addresses or [])
    if not rows:
        return None
    alvo = _fold_end(endereco)
    if alvo:
        for row in rows:
            rua = _fold_end(row.street or "")
            if not rua:
                continue
            if rua == alvo or alvo in rua or rua in alvo:
                return row
    return _default_address(customer)


def _carregar_do_cadastro(db: Session, cliente_id: Optional[int], endereco: str) -> Ponto:
    ponto = Ponto(rotulo="", endereco=endereco.strip(), cliente_id=cliente_id)
    if not cliente_id:
        return ponto
    customer = db.query(Customer).filter(Customer.id == cliente_id).first()
    if not customer:
        return ponto
    ponto.rotulo = customer.name
    address = _address_para_entrega(customer, endereco)
    if not address:
        return ponto
    if not ponto.endereco and address.street:
        ponto.endereco = address.street
    localizacao = (address.location_url or "").strip()
    ponto.localizacao = localizacao
    lat = _como_float(address.lat)
    lng = _como_float(address.lng)
    if lat is not None and lng is not None and _par_br(lat, lng):
        ponto.lat, ponto.lng = lat, lng
        ponto.origem = "cadastro"
        return ponto
    coords = coords_de_localizacao(localizacao)
    if coords:
        ponto.lat, ponto.lng = coords
        ponto.origem = "localizacao"
        address.lat = Decimal(str(round(coords[0], 8)))
        address.lng = Decimal(str(round(coords[1], 8)))
        db.add(address)
    return ponto


def _nominatim(query: str) -> Optional[tuple[float, float]]:
    q = _endereco_consulta(query)
    if not q:
        return None
    url = f"{settings.NOMINATIM_URL.rstrip('/')}/search"
    params = {
        "q": q,
        "format": "json",
        "limit": 1,
        "countrycodes": "br",
        "addressdetails": 0,
        "viewbox": "-49.55,-16.45,-48.95,-16.95",
        "bounded": 0,
    }
    headers = {"User-Agent": settings.ROTA_USER_AGENT}
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            rows = resp.json()
    except Exception as exc:
        logger.warning("Falha no Nominatim", query=q, erro=str(exc))
        return None
    if not rows:
        return None
    lat = _como_float(rows[0].get("lat"))
    lng = _como_float(rows[0].get("lon"))
    if lat is None or lng is None:
        return None
    return lat, lng


def _geocodificar(db: Session, ponto: Ponto) -> Ponto:
    if ponto.lat is not None and ponto.lng is not None:
        return ponto
    if ponto.localizacao:
        coords = coords_de_localizacao(ponto.localizacao)
        if coords:
            ponto.lat, ponto.lng = coords
            ponto.origem = "localizacao"
            if ponto.cliente_id:
                customer = db.query(Customer).filter(Customer.id == ponto.cliente_id).first()
                address = _default_address(customer) if customer else None
                if address:
                    address.lat = Decimal(str(round(coords[0], 8)))
                    address.lng = Decimal(str(round(coords[1], 8)))
                    if not address.location_url:
                        address.location_url = ponto.localizacao[:500]
                    db.add(address)
            return ponto
    coords = _coords_de_texto(ponto.endereco)
    if coords:
        ponto.lat, ponto.lng = coords
        ponto.origem = ponto.origem or "texto"
        return ponto
    coords = _nominatim(ponto.endereco or ponto.rotulo)
    time.sleep(1.05)
    if not coords:
        if ponto.localizacao:
            ponto.aviso = "Não li coordenadas do link; o Maps usa a localização do cadastro"
        else:
            ponto.aviso = "Não achei coordenadas deste endereço"
        return ponto
    ponto.lat, ponto.lng = coords
    ponto.origem = "nominatim"
    if ponto.cliente_id:
        customer = db.query(Customer).filter(Customer.id == ponto.cliente_id).first()
        address = _default_address(customer) if customer else None
        if address:
            address.lat = Decimal(str(round(coords[0], 8)))
            address.lng = Decimal(str(round(coords[1], 8)))
            db.add(address)
    return ponto


def osrm_disponivel() -> bool:
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{settings.OSRM_URL.rstrip('/')}/")
            return resp.status_code < 500
    except Exception:
        return False


def _osrm_trip(coords: list[tuple[float, float]]) -> Optional[dict[str, Any]]:
    if len(coords) < 2:
        return None
    path = ";".join(f"{lng},{lat}" for lat, lng in coords)
    url = (
        f"{settings.OSRM_URL.rstrip('/')}/trip/v1/driving/{path}"
        f"?source=first&roundtrip=false&overview=false&steps=false"
    )
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url)
            data = resp.json()
    except Exception as exc:
        logger.warning("Falha no OSRM trip", erro=str(exc))
        return None
    if data.get("code") != "Ok":
        logger.warning("OSRM trip sem Ok", code=data.get("code"), message=data.get("message"))
        return None
    return data


def _aplicar_localizacao(ponto: Ponto, localizacao: str) -> None:
    loc = (localizacao or "").strip()
    if not loc:
        return
    ponto.localizacao = loc
    if ponto.lat is not None and ponto.lng is not None:
        return
    coords = coords_de_localizacao(loc)
    if coords:
        ponto.lat, ponto.lng = coords
        ponto.origem = "localizacao"
        ponto.aviso = ""


def _ref_maps(p: Ponto) -> str:
    """Prioriza coordenada / link do cadastro — nunca o texto do endereço se houver localização."""
    if p.lat is not None and p.lng is not None:
        return f"{p.lat},{p.lng}"
    loc = (p.localizacao or "").strip()
    if loc:
        return loc
    return (p.endereco or p.rotulo or "").strip()


def _maps_url(partida: Ponto, paradas: list[Ponto]) -> str:
    pontos = [partida] + paradas
    # Última tentativa de ler coords do link do cadastro antes de montar o Maps.
    for p in pontos:
        if (p.lat is None or p.lng is None) and p.localizacao:
            _aplicar_localizacao(p, p.localizacao)

    refs = [_ref_maps(p) for p in pontos]
    refs = [r for r in refs if r]
    if len(refs) < 2:
        return refs[0] if len(refs) == 1 and refs[0].startswith("http") else ""

    com_coord = all(p.lat is not None and p.lng is not None for p in pontos)
    if com_coord:
        origem = f"{pontos[0].lat},{pontos[0].lng}"
        destino = f"{pontos[-1].lat},{pontos[-1].lng}"
        meios = pontos[1:-1]
        waypoints = "|".join(f"{p.lat},{p.lng}" for p in meios)
        url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={quote_plus(origem)}"
            f"&destination={quote_plus(destino)}"
            "&travelmode=driving"
        )
        if waypoints:
            url += f"&waypoints={quote_plus(waypoints)}"
        return url

    # Sem coords: usa link do cadastro (não o endereço textual, se o link existir).
    origem = _ref_maps(pontos[0])
    destino = _ref_maps(pontos[-1])
    meios = [_ref_maps(p) for p in pontos[1:-1]]
    url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={quote_plus(origem)}"
        f"&destination={quote_plus(destino)}"
        "&travelmode=driving"
    )
    if meios:
        url += f"&waypoints={quote_plus('|'.join(meios))}"
    return url


def otimizar_rota(
    db: Session,
    partida: str,
    paradas_in: list[dict[str, Any]],
) -> dict[str, Any]:
    avisos: list[str] = []
    partida_txt = (partida or "").strip() or settings.ROTA_PARTIDA_PADRAO
    origem = Ponto(rotulo="Partida", endereco=partida_txt)
    origem = _geocodificar(db, origem)
    if origem.aviso:
        avisos.append(f"Partida: {origem.aviso}")

    pontos: list[Ponto] = []
    vistos: set[str] = set()
    for item in paradas_in:
        cliente = (item.get("cliente") or "").strip()
        endereco = (item.get("endereco") or "").strip()
        cliente_id = item.get("cliente_id")
        order_id = item.get("order_id")
        localizacao_in = (item.get("localizacao") or "").strip()
        chave = f"{cliente_id or cliente}|{endereco.lower()}"
        if chave in vistos:
            continue
        vistos.add(chave)
        if not cliente_id and cliente:
            achado = (
                db.query(Customer)
                .filter(Customer.name.ilike(cliente))
                .order_by(Customer.id)
                .first()
            )
            if achado:
                cliente_id = achado.id
        ponto = _carregar_do_cadastro(db, cliente_id, endereco)
        if localizacao_in:
            _aplicar_localizacao(ponto, localizacao_in)
            if ponto.cliente_id and ponto.lat is not None:
                customer = db.query(Customer).filter(Customer.id == ponto.cliente_id).first()
                address = _default_address(customer) if customer else None
                if address:
                    address.location_url = localizacao_in[:500]
                    address.lat = Decimal(str(round(ponto.lat, 8)))
                    address.lng = Decimal(str(round(ponto.lng, 8)))
                    db.add(address)
        if not ponto.rotulo:
            ponto.rotulo = cliente or "Cliente"
        if not ponto.endereco and not ponto.localizacao:
            ponto.aviso = "Sem endereço"
            avisos.append(f"{ponto.rotulo}: sem endereço")
            pontos.append(ponto)
            continue
        ponto.order_id = str(order_id) if order_id else None
        ponto = _geocodificar(db, ponto)
        if ponto.aviso:
            avisos.append(f"{ponto.rotulo}: {ponto.aviso}")
        pontos.append(ponto)

    db.commit()

    osrm_ok = osrm_disponivel()
    modo = "tela"
    distancia_m = None
    duracao_s = None
    ordenados = list(pontos)

    localizados = [p for p in pontos if p.lat is not None and p.lng is not None]
    if origem.lat is not None and origem.lng is not None and localizados and osrm_ok:
        coords = [(origem.lat, origem.lng)] + [(p.lat, p.lng) for p in localizados]
        data = _osrm_trip(coords)
        if data:
            waypoints = data.get("waypoints") or []
            visit = sorted(
                range(1, len(waypoints)),
                key=lambda i: waypoints[i].get("waypoint_index", i),
            )
            ordenados_loc = [localizados[i - 1] for i in visit]
            sem = [p for p in pontos if p.lat is None or p.lng is None]
            ordenados = ordenados_loc + sem
            trip = (data.get("trips") or [{}])[0]
            distancia_m = trip.get("distance")
            duracao_s = trip.get("duration")
            modo = "osrm"
        else:
            avisos.append("OSRM não montou a trip; mantive a ordem da tela.")
    elif not osrm_ok:
        avisos.append(
            "OSRM offline — ordem da tela. Suba o Docker do OSRM na porta 5000 para otimizar."
        )

    return {
        "partida": {
            "rotulo": origem.rotulo,
            "endereco": origem.endereco,
            "lat": origem.lat,
            "lng": origem.lng,
            "origem": origem.origem,
            "localizacao": origem.localizacao or "",
        },
        "paradas": [
            {
                "seq": i + 1,
                "cliente": p.rotulo,
                "endereco": p.endereco,
                "lat": p.lat,
                "lng": p.lng,
                "cliente_id": p.cliente_id,
                "order_id": p.order_id,
                "origem": p.origem,
                "aviso": p.aviso,
                "localizacao": p.localizacao or "",
            }
            for i, p in enumerate(ordenados)
        ],
        "modo": modo,
        "distancia_m": distancia_m,
        "duracao_s": duracao_s,
        "maps_url": _maps_url(origem, ordenados),
        "osrm_ok": osrm_ok,
        "avisos": avisos,
    }
