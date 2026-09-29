"""
Rotas para zonas de entrega e preços específicos de clientes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db_session import get_db_session
from services.shipping_service import ShippingService
from schemas.shipping import (
    DeliveryZoneCreate, DeliveryZoneUpdate, DeliveryZoneResponse,
    CustomerProductPriceCreate, CustomerProductPriceUpdate, CustomerProductPriceResponse
)
from models.commerce import CustomerProductPrice

router = APIRouter(prefix="/shipping", tags=["shipping"])


@router.get("/zones", response_model=List[DeliveryZoneResponse])
def list_delivery_zones(
    active_only: bool = Query(True),
    db: Session = Depends(get_db_session)
):
    """Lista zonas de entrega"""
    return ShippingService.get_delivery_zones(db, active_only=active_only)


@router.get("/zones/{zone_id}", response_model=DeliveryZoneResponse)
def get_delivery_zone(zone_id: int, db: Session = Depends(get_db_session)):
    """Busca uma zona por ID"""
    zone = ShippingService.get_delivery_zone(db, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zona não encontrada")
    return zone


@router.post("/zones", response_model=DeliveryZoneResponse, status_code=201)
def create_delivery_zone(zone: DeliveryZoneCreate, db: Session = Depends(get_db_session)):
    """Cria uma nova zona de entrega"""
    from models.commerce import DeliveryZone
    db_zone = DeliveryZone(**zone.model_dump())
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone


@router.put("/zones/{zone_id}", response_model=DeliveryZoneResponse)
def update_delivery_zone(
    zone_id: int,
    zone: DeliveryZoneUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza uma zona de entrega"""
    db_zone = ShippingService.get_delivery_zone(db, zone_id)
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zona não encontrada")
    
    update_data = zone.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_zone, field, value)
    
    db.commit()
    db.refresh(db_zone)
    return db_zone


@router.get("/customers/{customer_id}/product-prices", response_model=List[CustomerProductPriceResponse])
def list_customer_product_prices(customer_id: int, db: Session = Depends(get_db_session)):
    """Lista preços específicos de um cliente"""
    prices = db.query(CustomerProductPrice).filter(
        CustomerProductPrice.customer_id == customer_id
    ).all()
    return prices


@router.get("/customers/{customer_id}/product-prices/{product_id}", response_model=CustomerProductPriceResponse)
def get_customer_product_price(
    customer_id: int,
    product_id: int,
    db: Session = Depends(get_db_session)
):
    """Busca preço específico de um produto para um cliente"""
    price = db.query(CustomerProductPrice).filter(
        CustomerProductPrice.customer_id == customer_id,
        CustomerProductPrice.product_id == product_id
    ).first()
    if not price:
        raise HTTPException(status_code=404, detail="Preço não encontrado")
    return price


@router.post("/customers/product-prices", response_model=CustomerProductPriceResponse, status_code=201)
def create_customer_product_price(price: CustomerProductPriceCreate, db: Session = Depends(get_db_session)):
    """Cria um preço específico para um cliente"""
    # Verifica se já existe
    existing = db.query(CustomerProductPrice).filter(
        CustomerProductPrice.customer_id == price.customer_id,
        CustomerProductPrice.product_id == price.product_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Preço já existe para este cliente e produto")
    
    db_price = CustomerProductPrice(**price.model_dump())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price


@router.put("/customers/product-prices/{price_id}", response_model=CustomerProductPriceResponse)
def update_customer_product_price(
    price_id: int,
    price: CustomerProductPriceUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza um preço específico de cliente"""
    db_price = db.query(CustomerProductPrice).filter(CustomerProductPrice.id == price_id).first()
    if not db_price:
        raise HTTPException(status_code=404, detail="Preço não encontrado")
    
    update_data = price.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_price, field, value)
    
    db.commit()
    db.refresh(db_price)
    return db_price


@router.delete("/customers/product-prices/{price_id}", status_code=204)
def delete_customer_product_price(price_id: int, db: Session = Depends(get_db_session)):
    """Remove um preço específico de cliente"""
    db_price = db.query(CustomerProductPrice).filter(CustomerProductPrice.id == price_id).first()
    if not db_price:
        raise HTTPException(status_code=404, detail="Preço não encontrado")
    
    db.delete(db_price)
    db.commit()
    return None
