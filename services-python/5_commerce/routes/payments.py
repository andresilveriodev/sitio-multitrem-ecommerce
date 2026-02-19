"""
Rotas para pagamentos
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from db_session import get_db_session
from services.payment_service import PaymentService
from models.commerce import PaymentStatus
from schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=List[PaymentResponse])
def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    order_id: Optional[UUID] = Query(None),
    status: Optional[PaymentStatus] = Query(None),
    db: Session = Depends(get_db_session)
):
    """Lista pagamentos"""
    return PaymentService.get_payments(db, skip=skip, limit=limit, order_id=order_id, status=status)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db_session)):
    """Busca um pagamento por ID"""
    payment = PaymentService.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return payment


@router.post("", response_model=PaymentResponse, status_code=201)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db_session)):
    """Cria um novo pagamento"""
    return PaymentService.create_payment(db, payment)


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int,
    payment: PaymentUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza um pagamento"""
    updated = PaymentService.update_payment(db, payment_id, payment)
    if not updated:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return updated


@router.post("/{payment_id}/mark-paid", response_model=PaymentResponse)
def mark_payment_as_paid(
    payment_id: int,
    external_ref: Optional[str] = Query(None),
    db: Session = Depends(get_db_session)
):
    """Marca um pagamento como pago"""
    payment = PaymentService.mark_as_paid(db, payment_id, external_ref)
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return payment
