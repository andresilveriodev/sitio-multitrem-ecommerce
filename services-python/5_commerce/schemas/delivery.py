"""
Schemas Pydantic para entregas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from models.commerce import DeliveryRouteStatus, DeliveryStopStatus


class DeliveryStopBase(BaseModel):
    route_id: int
    order_id: UUID
    sequence: int = Field(..., ge=1)
    fee_per_stop: Decimal = Field(default=1.50, ge=0)


class DeliveryStopCreate(DeliveryStopBase):
    pass


class DeliveryStopUpdate(BaseModel):
    status: Optional[DeliveryStopStatus] = None
    delivered_at: Optional[datetime] = None
    proof: Optional[str] = None
    fee_per_stop: Optional[Decimal] = Field(None, ge=0)


class DeliveryStopResponse(DeliveryStopBase):
    id: int
    status: DeliveryStopStatus
    delivered_at: Optional[datetime] = None
    proof: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeliveryRouteBase(BaseModel):
    date: date
    driver_name: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class DeliveryRouteCreate(DeliveryRouteBase):
    stops: List[DeliveryStopCreate] = Field(default_factory=list)


class DeliveryRouteUpdate(BaseModel):
    date: Optional[date] = None
    driver_name: Optional[str] = Field(None, max_length=200)
    status: Optional[DeliveryRouteStatus] = None
    notes: Optional[str] = None


class DeliveryRouteResponse(DeliveryRouteBase):
    id: int
    status: DeliveryRouteStatus
    created_at: datetime
    stops: List[DeliveryStopResponse] = []
    
    class Config:
        from_attributes = True
