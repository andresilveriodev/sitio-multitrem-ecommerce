"""
Rotas para pedidos
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from db_session import get_db_session
from services.order_service import OrderService
from models.commerce import OrderStatus
from schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderSummary

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=List[OrderResponse])
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None),
    customer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session)
):
    """Lista pedidos"""
    return OrderService.get_orders(db, skip=skip, limit=limit, status=status, customer_id=customer_id)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: UUID, db: Session = Depends(get_db_session)):
    """Busca um pedido por ID"""
    order = OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(order: OrderCreate, db: Session = Depends(get_db_session)):
    """Cria um novo pedido"""
    try:
        return OrderService.create_order(db, order)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: UUID,
    order: OrderUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza um pedido"""
    updated = OrderService.update_order(db, order_id, order)
    if not updated:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return updated


@router.post("/{order_id}/confirm", response_model=OrderResponse)
def confirm_order(order_id: UUID, db: Session = Depends(get_db_session)):
    """Confirma um pedido"""
    try:
        order = OrderService.confirm_order(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: UUID, db: Session = Depends(get_db_session)):
    """Cancela um pedido"""
    try:
        order = OrderService.cancel_order(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
