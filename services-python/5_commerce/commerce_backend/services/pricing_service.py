"""
Serviço de precificação - Aplica regras de negócio de preços
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from decimal import Decimal
import structlog

from models.commerce import (
    Product, Customer, CustomerProductPrice, PriceProfile
)
from config import settings

logger = structlog.get_logger()


class PricingService:
    """Serviço para calcular preços baseado em regras de negócio"""
    
    # Tabela de preços por perfil (hardcoded conforme regras de negócio)
    PRICE_TABLE = {
        PriceProfile.RESTAURANTE_HIGH: {
            "hortalica": Decimal("3.00"),
            "palito_alface": Decimal("8.00"),
        },
        PriceProfile.RESTAURANTE_LOW: {
            "hortalica": Decimal("3.50"),
            "palito_alface": Decimal("9.00"),
        },
        PriceProfile.VAREJO: {
            "hortalica": Decimal("4.00"),
            "palito_alface": None,  # Normalmente não usado
        },
    }
    
    @staticmethod
    def get_product_price(
        db: Session,
        customer: Customer,
        product: Product,
        is_palito: bool = False
    ) -> Decimal:
        """
        Obtém o preço de um produto para um cliente.
        Prioridade: preço específico do cliente > preço do perfil > preço padrão
        """
        # 1. Verifica se existe preço específico para o cliente
        customer_price = db.query(CustomerProductPrice).filter(
            and_(
                CustomerProductPrice.customer_id == customer.id,
                CustomerProductPrice.product_id == product.id
            )
        ).first()
        
        if customer_price:
            logger.info(
                "Preço específico do cliente aplicado",
                customer_id=customer.id,
                product_id=product.id,
                price=customer_price.price
            )
            return customer_price.price
        
        # 2. Aplica preço baseado no perfil do cliente
        profile = customer.price_profile
        
        # Identifica o tipo de produto
        if is_palito or "palito" in product.name.lower() or "palito" in (product.sku or "").lower():
            price_key = "palito_alface"
        else:
            price_key = "hortalica"
        
        # Obtém preço do perfil
        profile_prices = PricingService.PRICE_TABLE.get(profile, {})
        price = profile_prices.get(price_key)
        
        if price is not None:
            logger.info(
                "Preço do perfil aplicado",
                customer_id=customer.id,
                profile=profile.value,
                product_id=product.id,
                price=price
            )
            return price
        
        # 3. Fallback: retorna 0 (deve ser tratado como erro)
        logger.warning(
            "Preço não encontrado",
            customer_id=customer.id,
            profile=profile.value,
            product_id=product.id
        )
        return Decimal("0.00")
    
    @staticmethod
    def normalize_alface_units(qty: Decimal, product_sku: Optional[str] = None) -> Tuple[Decimal, Decimal]:
        """
        Normaliza unidades de alface para palitos.
        Regra: 1 palito = 3 alfaces
        
        Retorna: (qty_palitos, qty_unidades)
        """
        # Se for palito explicitamente, não normaliza
        if product_sku and "palito" in product_sku.lower():
            return (qty, Decimal("0"))
        
        # Normaliza: 3 alfaces = 1 palito
        palitos = qty // 3
        unidades = qty % 3
        
        return (palitos, unidades)
    
    @staticmethod
    def calculate_item_price(
        db: Session,
        customer: Customer,
        product: Product,
        qty: Decimal,
        is_palito: bool = False
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calcula o preço de um item do pedido.
        Retorna: (unit_price, subtotal, qty_final)
        
        Aplica normalização de alfaces se necessário.
        """
        # Normaliza alfaces se não for palito
        if not is_palito and ("alface" in product.name.lower() or (product.sku and "alface" in product.sku.lower())):
            palitos, unidades = PricingService.normalize_alface_units(qty, product.sku)
            
            if palitos > 0 and unidades > 0:
                # Precisa dividir em dois itens: palitos e unidades
                # Por enquanto, calcula como se fosse tudo em palitos
                # O chatbot/sistema deve criar itens separados
                qty_final = palitos + (unidades / 3)  # Converte unidades para fração de palito
            elif palitos > 0:
                qty_final = palitos
                is_palito = True
            else:
                qty_final = unidades
        else:
            qty_final = qty
        
        # Obtém preço unitário
        unit_price = PricingService.get_product_price(db, customer, product, is_palito)
        
        # Calcula subtotal
        subtotal = qty_final * unit_price
        
        return (unit_price, subtotal, qty_final)
