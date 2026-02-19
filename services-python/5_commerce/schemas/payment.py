"""
Schemas Pydantic para pagamentos
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from models.commerce import PaymentMethod, PaymentStatus


class PaymentBase(BaseModel):
    order_id: UUID
    method: PaymentMethod
    amount: Decimal = Field(..., ge=0)
    external_ref: Optional[str] = Field(None, max_length=200)  # txid pix, etc.


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    paid_at: Optional[datetime] = None
    external_ref: Optional[str] = Field(None, max_length=200)


class PaymentResponse(PaymentBase):
    id: int
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
