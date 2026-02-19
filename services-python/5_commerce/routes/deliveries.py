"""
Rotas para entregas
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from db_session import get_db_session
from services.delivery_service import DeliveryService
from models.commerce import DeliveryRouteStatus
from schemas.delivery import (
    DeliveryRouteCreate, DeliveryRouteUpdate, DeliveryRouteResponse,
    DeliveryStopUpdate, DeliveryStopResponse
)

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


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
