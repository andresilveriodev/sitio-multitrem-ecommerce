"""
Serviço de pagamentos
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
import structlog

from models.commerce import Payment, PaymentStatus, PaymentMethod
from schemas.payment import PaymentCreate, PaymentUpdate

logger = structlog.get_logger()


class PaymentService:
    """Serviço para gerenciar pagamentos"""
    
    @staticmethod
    def get_payments(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        order_id: Optional[UUID] = None,
        status: Optional[PaymentStatus] = None
    ) -> List[Payment]:
        """Lista pagamentos"""
        query = db.query(Payment)
        
        if order_id:
            query = query.filter(Payment.order_id == order_id)
        
        if status:
            query = query.filter(Payment.status == status)
        
        return query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_payment(db: Session, payment_id: int) -> Optional[Payment]:
        """Busca um pagamento por ID"""
        return db.query(Payment).filter(Payment.id == payment_id).first()
    
    @staticmethod
    def create_payment(db: Session, payment: PaymentCreate) -> Payment:
        """Cria um novo pagamento"""
        db_payment = Payment(**payment.model_dump())
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        logger.info("Pagamento criado", payment_id=db_payment.id, order_id=payment.order_id)
        return db_payment
    
    @staticmethod
    def update_payment(db: Session, payment_id: int, payment: PaymentUpdate) -> Optional[Payment]:
        """Atualiza um pagamento"""
        db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not db_payment:
            return None
        
        update_data = payment.model_dump(exclude_unset=True)
        
        # Se mudou para paid, atualiza paid_at
        if update_data.get("status") == PaymentStatus.PAID and not db_payment.paid_at:
            update_data["paid_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_payment, field, value)
        
        db.commit()
        db.refresh(db_payment)
        logger.info("Pagamento atualizado", payment_id=payment_id, status=update_data.get("status"))
        return db_payment
    
    @staticmethod
    def mark_as_paid(db: Session, payment_id: int, external_ref: Optional[str] = None) -> Optional[Payment]:
        """Marca um pagamento como pago"""
        db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not db_payment:
            return None
        
        db_payment.status = PaymentStatus.PAID
        db_payment.paid_at = datetime.utcnow()
        if external_ref:
            db_payment.external_ref = external_ref
        
        db.commit()
        db.refresh(db_payment)
        logger.info("Pagamento marcado como pago", payment_id=payment_id)
        return db_payment
