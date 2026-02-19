"""
Serviço de cálculo de frete
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from decimal import Decimal
import structlog

from models.commerce import CustomerAddress, DeliveryZone, Order
from config import settings

logger = structlog.get_logger()


class ShippingService:
    """Serviço para calcular frete"""
    
    # Configurações de frete grátis (podem ser movidas para banco/config)
    FREE_SHIPPING_MINIMUM = Decimal("50.00")  # Frete grátis acima de R$ 50
    FREE_SHIPPING_ENABLED = True
    
    @staticmethod
    def calculate_shipping(
        db: Session,
        address: CustomerAddress,
        order_subtotal: Decimal
    ) -> Decimal:
        """
        Calcula o frete baseado na zona de entrega e valor do pedido.
        
        Regras:
        1. Se frete grátis habilitado e subtotal >= mínimo → frete = 0
        2. Caso contrário, usa o valor da zona de entrega
        """
        # Verifica frete grátis por ticket mínimo
        if ShippingService.FREE_SHIPPING_ENABLED and order_subtotal >= ShippingService.FREE_SHIPPING_MINIMUM:
            logger.info(
                "Frete grátis aplicado",
                address_id=address.id,
                subtotal=order_subtotal
            )
            return Decimal("0.00")
        
        # Obtém frete da zona
        if address.delivery_zone_id:
            zone = db.query(DeliveryZone).filter(DeliveryZone.id == address.delivery_zone_id).first()
            if zone and zone.active:
                logger.info(
                    "Frete da zona aplicado",
                    address_id=address.id,
                    zone_id=zone.id,
                    zone_name=zone.name,
                    fee=zone.fee
                )
                return zone.fee
        
        # Se não tem zona, retorna 0 (deve ser configurado)
        logger.warning(
            "Zona de entrega não encontrada",
            address_id=address.id
        )
        return Decimal("0.00")
    
    @staticmethod
    def get_delivery_zones(db: Session, active_only: bool = True) -> List[DeliveryZone]:
        """Lista zonas de entrega"""
        query = db.query(DeliveryZone)
        if active_only:
            query = query.filter(DeliveryZone.active == True)
        return query.all()
    
    @staticmethod
    def get_delivery_zone(db: Session, zone_id: int) -> Optional[DeliveryZone]:
        """Busca uma zona por ID"""
        return db.query(DeliveryZone).filter(DeliveryZone.id == zone_id).first()
    
    @staticmethod
    def get_zone_by_name(db: Session, name: str) -> Optional[DeliveryZone]:
        """Busca uma zona por nome"""
        return db.query(DeliveryZone).filter(DeliveryZone.name == name).first()
