"""
Rotas para entregas
"""

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from datetime import date

from db_session import get_db_session
from services.delivery_service import DeliveryService
from services.rota_service import otimizar_rota, osrm_disponivel
from models.commerce import DeliveryRouteStatus
from schemas.delivery import (
    DeliveryRouteCreate, DeliveryRouteUpdate, DeliveryRouteResponse,
    DeliveryStopUpdate, DeliveryStopResponse
)

router = APIRouter(prefix="/deliveries", tags=["deliveries"])

MARCA_ROTA_OPERACAO = "rota_operacao_v1"


class ParadaRotaIn(BaseModel):
    cliente: str = ""
    endereco: str = ""
    cliente_id: Optional[int] = None
    order_id: Optional[str] = None
    localizacao: Optional[str] = None


class OtimizarRotaIn(BaseModel):
    partida: str = ""
    paradas: List[ParadaRotaIn] = Field(default_factory=list)


class RotaDoDiaIn(BaseModel):
    data: date
    partida: str = ""
    rota: Dict[str, Any]


class RotaDoDiaOut(BaseModel):
    id: int
    data: date
    partida: str = ""
    rota: Dict[str, Any]


@router.get("/osrm")
def status_osrm():
    return {"ok": osrm_disponivel()}


@router.post("/otimizar")
def criar_rota_otimizada(body: OtimizarRotaIn, db: Session = Depends(get_db_session)) -> dict[str, Any]:
    """Monta a ordem das entregas (OSRM quando disponível) a partir das paradas da tela."""
    if not body.paradas:
        raise HTTPException(status_code=400, detail="Informe ao menos uma parada")
    return otimizar_rota(
        db,
        body.partida,
        [p.model_dump() for p in body.paradas],
    )


@router.put("/rota-do-dia", response_model=RotaDoDiaOut)
def salvar_rota_do_dia(body: RotaDoDiaIn, db: Session = Depends(get_db_session)):
    """Grava a rota montada/reordenada do dia (ordem manual incluída)."""
    if not isinstance(body.rota, dict) or not body.rota.get("paradas"):
        raise HTTPException(status_code=400, detail="Informe a rota com paradas")
    salvo = DeliveryService.salvar_rota_operacao(
        db,
        body.data,
        body.partida,
        body.rota,
        marca=MARCA_ROTA_OPERACAO,
    )
    return RotaDoDiaOut(
        id=salvo.id,
        data=salvo.date,
        partida=body.partida,
        rota=body.rota,
    )


@router.get("/rota-do-dia", response_model=RotaDoDiaOut)
def obter_rota_do_dia(data: date = Query(...), db: Session = Depends(get_db_session)):
    """Carrega a última rota salva daquele dia."""
    salvo = DeliveryService.obter_rota_operacao(db, data, marca=MARCA_ROTA_OPERACAO)
    if not salvo:
        raise HTTPException(status_code=404, detail="Nenhuma rota salva neste dia")
    try:
        pacote = json.loads(salvo.notes or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Rota salva inválida") from exc
    return RotaDoDiaOut(
        id=salvo.id,
        data=salvo.date,
        partida=str(pacote.get("partida") or ""),
        rota=pacote.get("rota") if isinstance(pacote.get("rota"), dict) else {},
    )


@router.get("/routes", response_model=List[DeliveryRouteResponse])
def list_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    route_date: Optional[date] = Query(None),
    status: Optional[DeliveryRouteStatus] = Query(None),
    db: Session = Depends(get_db_session)
):
    """Lista rotas de entrega"""
    return DeliveryService.get_routes(db, skip=skip, limit=limit, route_date=route_date, status=status)


@router.get("/routes/{route_id}", response_model=DeliveryRouteResponse)
def get_route(route_id: int, db: Session = Depends(get_db_session)):
    """Busca uma rota por ID"""
    route = DeliveryService.get_route(db, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Rota não encontrada")
    return route


@router.post("/routes", response_model=DeliveryRouteResponse, status_code=201)
def create_route(route: DeliveryRouteCreate, db: Session = Depends(get_db_session)):
    """Cria uma nova rota"""
    return DeliveryService.create_route(db, route)


@router.put("/routes/{route_id}", response_model=DeliveryRouteResponse)
def update_route(
    route_id: int,
    route: DeliveryRouteUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza uma rota"""
    updated = DeliveryService.update_route(db, route_id, route)
    if not updated:
        raise HTTPException(status_code=404, detail="Rota não encontrada")
    return updated


@router.get("/stops/{stop_id}", response_model=DeliveryStopResponse)
def get_stop(stop_id: int, db: Session = Depends(get_db_session)):
    """Busca uma parada por ID"""
    stop = DeliveryService.get_stop(db, stop_id)
    if not stop:
        raise HTTPException(status_code=404, detail="Parada não encontrada")
    return stop


@router.put("/stops/{stop_id}", response_model=DeliveryStopResponse)
def update_stop(
    stop_id: int,
    stop: DeliveryStopUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza uma parada"""
    updated = DeliveryService.update_stop(db, stop_id, stop)
    if not updated:
        raise HTTPException(status_code=404, detail="Parada não encontrada")
    return updated
