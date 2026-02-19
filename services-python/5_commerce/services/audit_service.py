"""
Serviço de auditoria
"""

from typing import Optional
from sqlalchemy.orm import Session
import json
import structlog

from models.commerce import AuditLog

logger = structlog.get_logger()


class AuditService:
    """Serviço para registrar logs de auditoria"""
    
    @staticmethod
    def log(
        db: Session,
        entity_type: str,
        entity_id: str,
        action: str,
        data: Optional[dict] = None
    ) -> AuditLog:
        """Registra um log de auditoria"""
        db_log = AuditLog(
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            data=json.dumps(data) if data else None
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        logger.info("Log de auditoria criado", entity_type=entity_type, entity_id=entity_id, action=action)
        return db_log
