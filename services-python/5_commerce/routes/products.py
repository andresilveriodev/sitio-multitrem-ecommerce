"""
Rotas para produtos, categorias e preços
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db_session import get_db_session
from services.product_service import ProductService
from schemas.product import (
    ProductCategoryCreate, ProductCategoryUpdate, ProductCategoryResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    PriceListCreate, PriceListUpdate, PriceListResponse,
    ProductPriceCreate, ProductPriceUpdate, ProductPriceResponse
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/categories", response_model=List[ProductCategoryResponse])
def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db_session)
):
    """Lista todas as categorias"""
    return ProductService.get_categories(db, skip=skip, limit=limit)


@router.get("/categories/{category_id}", response_model=ProductCategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db_session)):
    """Busca uma categoria por ID"""
    category = ProductService.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return category


@router.post("/categories", response_model=ProductCategoryResponse, status_code=201)
def create_category(category: ProductCategoryCreate, db: Session = Depends(get_db_session)):
    """Cria uma nova categoria"""
    return ProductService.create_category(db, category)


@router.put("/categories/{category_id}", response_model=ProductCategoryResponse)
def update_category(
    category_id: int,
    category: ProductCategoryUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza uma categoria"""
    updated = ProductService.update_category(db, category_id, category)
    if not updated:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return updated


@router.get("", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db_session)
):
    """Lista produtos"""
    return ProductService.get_products(db, skip=skip, limit=limit, category_id=category_id, active_only=active_only)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db_session)):
    """Busca um produto por ID"""
    product = ProductService.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db_session)):
    """Cria um novo produto"""
    return ProductService.create_product(db, product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db_session)
):
    """Atualiza um produto"""
    updated = ProductService.update_product(db, product_id, product)
    if not updated:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return updated


@router.get("/price-lists", response_model=List[PriceListResponse])
def list_price_lists(
    active_only: bool = Query(True),
    db: Session = Depends(get_db_session)
):
    """Lista listas de preços"""
    return ProductService.get_price_lists(db, active_only=active_only)


@router.post("/price-lists", response_model=PriceListResponse, status_code=201)
def create_price_list(price_list: PriceListCreate, db: Session = Depends(get_db_session)):
    """Cria uma nova lista de preços"""
    return ProductService.create_price_list(db, price_list)


@router.get("/{product_id}/prices/{price_list_id}", response_model=ProductPriceResponse)
def get_product_price(
    product_id: int,
    price_list_id: int,
    db: Session = Depends(get_db_session)
):
    """Busca preço de um produto em uma lista de preços"""
    price = ProductService.get_product_price(db, product_id, price_list_id)
    if not price:
        raise HTTPException(status_code=404, detail="Preço não encontrado")
    return price


@router.post("/prices", response_model=ProductPriceResponse, status_code=201)
def set_product_price(price: ProductPriceCreate, db: Session = Depends(get_db_session)):
    """Define preço de um produto"""
    return ProductService.set_product_price(db, price)
