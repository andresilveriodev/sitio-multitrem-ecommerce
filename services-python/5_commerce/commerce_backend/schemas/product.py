"""
Schemas Pydantic para produtos
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class ProductCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    sort_order: int = Field(default=0, ge=0)


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = Field(None, ge=0)


class ProductCategoryResponse(ProductCategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    category_id: int
    sku: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., max_length=200)
    unit: str = Field(..., max_length=20)  # un, maço, bandeja, dz, pct
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    sku: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    unit: Optional[str] = Field(None, max_length=20)
    active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PriceListBase(BaseModel):
    name: str = Field(..., max_length=100)
    active: bool = True


class PriceListCreate(PriceListBase):
    pass


class PriceListUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None


class PriceListResponse(PriceListBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductPriceBase(BaseModel):
    product_id: int
    price_list_id: int
    price: Decimal = Field(..., ge=0)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class ProductPriceCreate(ProductPriceBase):
    pass


class ProductPriceUpdate(BaseModel):
    product_id: Optional[int] = None
    price_list_id: Optional[int] = None
    price: Optional[Decimal] = Field(None, ge=0)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class ProductPriceResponse(ProductPriceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
