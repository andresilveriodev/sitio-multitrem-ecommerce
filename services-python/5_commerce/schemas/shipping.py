"""
Schemas Pydantic para zonas de entrega
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class DeliveryZoneBase(BaseModel):
    name: str = Field(..., max_length=100)
    fee: Decimal = Field(..., ge=0)
    active: bool = True


class DeliveryZoneCreate(DeliveryZoneBase):
    pass


class DeliveryZoneUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    fee: Optional[Decimal] = Field(None, ge=0)
    active: Optional[bool] = None


class DeliveryZoneResponse(DeliveryZoneBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CustomerProductPriceBase(BaseModel):
    customer_id: int
    product_id: int
    price: Decimal = Field(..., ge=0)


class CustomerProductPriceCreate(CustomerProductPriceBase):
    pass


class CustomerProductPriceUpdate(BaseModel):
    price: Optional[Decimal] = Field(None, ge=0)


class CustomerProductPriceResponse(CustomerProductPriceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
