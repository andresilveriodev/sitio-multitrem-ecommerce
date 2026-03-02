"""
Schemas Pydantic para clientes
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from models.commerce import PriceProfile


class CustomerBase(BaseModel):
    name: str = Field(..., max_length=200)
    phone_e164: str = Field(..., max_length=20)  # +5562...
    document: Optional[str] = Field(None, max_length=20)  # CPF/CNPJ
    price_profile: PriceProfile = Field(default=PriceProfile.VAREJO)
    default_price_list_id: Optional[int] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    phone_e164: Optional[str] = Field(None, max_length=20)
    document: Optional[str] = Field(None, max_length=20)
    price_profile: Optional[PriceProfile] = None
    default_price_list_id: Optional[int] = None
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CustomerAddressBase(BaseModel):
    customer_id: int
    delivery_zone_id: Optional[int] = None
    label: str = Field(..., max_length=100)  # "Casa", "Restaurante", etc.
    street: str = Field(..., max_length=200)
    number: Optional[str] = Field(None, max_length=20)
    district: str = Field(..., max_length=100)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=2)
    zip: str = Field(..., max_length=10)
    reference: Optional[str] = None
    location_url: Optional[str] = Field(None, max_length=500)  # URL do Google Maps
    lat: Optional[Decimal] = None
    lng: Optional[Decimal] = None
    is_default: bool = False


class CustomerAddressCreate(CustomerAddressBase):
    pass


class CustomerAddressUpdate(BaseModel):
    delivery_zone_id: Optional[int] = None
    label: Optional[str] = Field(None, max_length=100)
    street: Optional[str] = Field(None, max_length=200)
    number: Optional[str] = Field(None, max_length=20)
    district: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip: Optional[str] = Field(None, max_length=10)
    reference: Optional[str] = None
    location_url: Optional[str] = Field(None, max_length=500)
    lat: Optional[Decimal] = None
    lng: Optional[Decimal] = None
    is_default: Optional[bool] = None


class CustomerAddressResponse(CustomerAddressBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CustomerContactBase(BaseModel):
    customer_id: int
    name: str = Field(..., max_length=200)
    phone_e164: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, max_length=100)  # "proprietario", "cozinheira", "gerente", etc.
    keycloak_user_id: Optional[str] = Field(None, max_length=200)
    active: bool = True
    notes: Optional[str] = None


class CustomerContactCreate(CustomerContactBase):
    pass


class CustomerContactUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    phone_e164: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, max_length=100)
    keycloak_user_id: Optional[str] = Field(None, max_length=200)
    active: Optional[bool] = None
    notes: Optional[str] = None


class CustomerContactResponse(CustomerContactBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
