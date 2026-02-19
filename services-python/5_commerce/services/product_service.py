"""
Serviço de produtos
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from decimal import Decimal
import structlog

from models.commerce import Product, ProductCategory, PriceList, ProductPrice
from schemas.product import (
    ProductCategoryCreate, ProductCategoryUpdate,
    ProductCreate, ProductUpdate,
    PriceListCreate, PriceListUpdate,
    ProductPriceCreate, ProductPriceUpdate
)

logger = structlog.get_logger()


class ProductService:
    """Serviço para gerenciar produtos, categorias e preços"""
    
    @staticmethod
    def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[ProductCategory]:
        """Lista todas as categorias"""
        return db.query(ProductCategory).order_by(ProductCategory.sort_order).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_category(db: Session, category_id: int) -> Optional[ProductCategory]:
        """Busca uma categoria por ID"""
        return db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
    
    @staticmethod
    def create_category(db: Session, category: ProductCategoryCreate) -> ProductCategory:
        """Cria uma nova categoria"""
        db_category = ProductCategory(**category.model_dump())
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        logger.info("Categoria criada", category_id=db_category.id, name=db_category.name)
        return db_category
    
    @staticmethod
    def update_category(db: Session, category_id: int, category: ProductCategoryUpdate) -> Optional[ProductCategory]:
        """Atualiza uma categoria"""
        db_category = db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
        if not db_category:
            return None
        
        update_data = category.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        db.commit()
        db.refresh(db_category)
        logger.info("Categoria atualizada", category_id=category_id)
        return db_category
    
    @staticmethod
    def get_products(db: Session, skip: int = 0, limit: int = 100, category_id: Optional[int] = None, active_only: bool = True) -> List[Product]:
        """Lista produtos"""
        query = db.query(Product)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if active_only:
            query = query.filter(Product.active == True)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_product(db: Session, product_id: int) -> Optional[Product]:
        """Busca um produto por ID"""
        return db.query(Product).filter(Product.id == product_id).first()
    
    @staticmethod
    def create_product(db: Session, product: ProductCreate) -> Product:
        """Cria um novo produto"""
        db_product = Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        logger.info("Produto criado", product_id=db_product.id, name=db_product.name)
        return db_product
    
    @staticmethod
    def update_product(db: Session, product_id: int, product: ProductUpdate) -> Optional[Product]:
        """Atualiza um produto"""
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            return None
        
        update_data = product.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        db.commit()
        db.refresh(db_product)
        logger.info("Produto atualizado", product_id=product_id)
        return db_product
    
    @staticmethod
    def get_price_lists(db: Session, active_only: bool = True) -> List[PriceList]:
        """Lista listas de preços"""
        query = db.query(PriceList)
        if active_only:
            query = query.filter(PriceList.active == True)
        return query.all()
    
    @staticmethod
    def create_price_list(db: Session, price_list: PriceListCreate) -> PriceList:
        """Cria uma nova lista de preços"""
        db_price_list = PriceList(**price_list.model_dump())
        db.add(db_price_list)
        db.commit()
        db.refresh(db_price_list)
        logger.info("Lista de preços criada", price_list_id=db_price_list.id)
        return db_price_list
    
    @staticmethod
    def get_product_price(db: Session, product_id: int, price_list_id: int) -> Optional[ProductPrice]:
        """Busca preço de um produto em uma lista de preços"""
        return db.query(ProductPrice).filter(
            and_(
                ProductPrice.product_id == product_id,
                ProductPrice.price_list_id == price_list_id
            )
        ).first()
    
    @staticmethod
    def set_product_price(db: Session, price: ProductPriceCreate) -> ProductPrice:
        """Define preço de um produto"""
        # Verifica se já existe
        existing = db.query(ProductPrice).filter(
            and_(
                ProductPrice.product_id == price.product_id,
                ProductPrice.price_list_id == price.price_list_id
            )
        ).first()
        
        if existing:
            # Atualiza preço existente
            existing.price = price.price
            existing.valid_from = price.valid_from
            existing.valid_to = price.valid_to
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Cria novo preço
            db_price = ProductPrice(**price.model_dump())
            db.add(db_price)
            db.commit()
            db.refresh(db_price)
            logger.info("Preço definido", product_id=price.product_id, price_list_id=price.price_list_id)
            return db_price
