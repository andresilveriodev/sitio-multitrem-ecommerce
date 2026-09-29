"""
Serviço de entregas
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, date
import structlog

from models.commerce import DeliveryRoute, DeliveryStop, DeliveryRouteStatus, DeliveryStopStatus
from schemas.delivery import DeliveryRouteCreate, DeliveryRouteUpdate, DeliveryStopCreate, DeliveryStopUpdate

logger = structlog.get_logger()


class DeliveryService:
    """Serviço para gerenciar rotas e entregas"""
    
    @staticmethod
    def get_routes(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        route_date: Optional[date] = None,
        status: Optional[DeliveryRouteStatus] = None
    ) -> List[DeliveryRoute]:
        """Lista rotas de entrega"""
        query = db.query(DeliveryRoute)
        
        if route_date:
            query = query.filter(DeliveryRoute.date == route_date)
        
        if status:
            query = query.filter(DeliveryRoute.status == status)
        
        return query.order_by(DeliveryRoute.date.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_route(db: Session, route_id: int) -> Optional[DeliveryRoute]:
        """Busca uma rota por ID"""
        return db.query(DeliveryRoute).filter(DeliveryRoute.id == route_id).first()
    
    @staticmethod
    def create_route(db: Session, route: DeliveryRouteCreate) -> DeliveryRoute:
        """Cria uma nova rota"""
        route_data = route.model_dump(exclude={"stops"})
        db_route = DeliveryRoute(**route_data)
        db.add(db_route)
        db.flush()  # Para obter o ID
        
        # Cria as paradas
        for stop in route.stops:
            stop_data = stop.model_dump()
            stop_data["route_id"] = db_route.id
            db_stop = DeliveryStop(**stop_data)
            db.add(db_stop)
        
        db.commit()
        db.refresh(db_route)
        logger.info("Rota criada", route_id=db_route.id, date=route.date)
        return db_route
    
    @staticmethod
    def update_route(db: Session, route_id: int, route: DeliveryRouteUpdate) -> Optional[DeliveryRoute]:
        """Atualiza uma rota"""
        db_route = db.query(DeliveryRoute).filter(DeliveryRoute.id == route_id).first()
        if not db_route:
            return None
        
        update_data = route.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_route, field, value)
        
        db.commit()
        db.refresh(db_route)
        logger.info("Rota atualizada", route_id=route_id)
        return db_route
    
    @staticmethod
    def get_stop(db: Session, stop_id: int) -> Optional[DeliveryStop]:
        """Busca uma parada por ID"""
        return db.query(DeliveryStop).filter(DeliveryStop.id == stop_id).first()
    
    @staticmethod
    def update_stop(db: Session, stop_id: int, stop: DeliveryStopUpdate) -> Optional[DeliveryStop]:
        """Atualiza uma parada"""
        db_stop = db.query(DeliveryStop).filter(DeliveryStop.id == stop_id).first()
        if not db_stop:
            return None
        
        update_data = stop.model_dump(exclude_unset=True)
        
        # Se mudou para delivered, atualiza delivered_at
        if update_data.get("status") == DeliveryStopStatus.DELIVERED and not db_stop.delivered_at:
            update_data["delivered_at"] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(db_stop, field, value)
        
        db.commit()
        db.refresh(db_stop)
        logger.info("Parada atualizada", stop_id=stop_id, status=update_data.get("status"))
        return db_stop
