"""
Modelos de dados para produtos do e-commerce
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Numeric, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

Base = declarative_base()


class Product(Base):
    """Modelo SQLAlchemy para produtos"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    sku = Column(String(100), unique=True, nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100), nullable=False)  # Telegram user_id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"


# Modelos Pydantic para validação e serialização
class ProductCreate(BaseModel):
    """Modelo para criação de produto"""
    name: str = Field(..., min_length=1, max_length=255, description="Nome do produto")
    description: Optional[str] = Field(None, max_length=5000, description="Descrição do produto")
    price: float = Field(..., gt=0, description="Preço do produto")
    stock_quantity: int = Field(0, ge=0, description="Quantidade em estoque")
    sku: Optional[str] = Field(None, max_length=100, description="SKU do produto")
    category: Optional[str] = Field(None, max_length=100, description="Categoria do produto")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Produto Exemplo",
                "description": "Descrição do produto",
                "price": 99.90,
                "stock_quantity": 10,
                "sku": "PROD-001",
                "category": "Eletrônicos"
            }
        }


class ProductUpdate(BaseModel):
    """Modelo para atualização de produto"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Modelo de resposta de produto"""
    id: int
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int
    sku: Optional[str]
    category: Optional[str]
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
