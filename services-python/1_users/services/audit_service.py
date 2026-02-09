"""
Serviço para auditoria de ações
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import structlog

from models.acl import AuditLog

logger = structlog.get_logger()


class AuditService:
    """Serviço para registro de auditoria"""
    
    def __init__(self):
        pass
    
    async def log_action(
        self,
        db: Session,
        user_id: int,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ) -> AuditLog:
        """Registra uma ação de auditoria"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.info(
                "Ação de auditoria registrada",
                user_id=user_id,
                action=action,
                resource=resource,
                success=success
            )
            
            return audit_log
            
        except Exception as e:
            logger.error("Erro ao registrar auditoria", error=str(e))
            db.rollback()
            raise
    
    async def get_user_audit_logs(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """Obtém logs de auditoria de um usuário"""
        try:
            logs = db.query(AuditLog)\
                .filter(AuditLog.user_id == user_id)\
                .order_by(AuditLog.created_at.desc())\
                .offset(skip)\
                .limit(limit)\
                .all()
            
            return logs
            
        except Exception as e:
            logger.error("Erro ao obter logs de auditoria", user_id=user_id, error=str(e))
            raise
    
    async def get_resource_audit_logs(
        self,
        db: Session,
        resource: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """Obtém logs de auditoria de um recurso"""
        try:
            logs = db.query(AuditLog)\
                .filter(AuditLog.resource == resource)\
                .order_by(AuditLog.created_at.desc())\
                .offset(skip)\
                .limit(limit)\
                .all()
            
            return logs
            
        except Exception as e:
            logger.error("Erro ao obter logs de auditoria", resource=resource, error=str(e))
            raise
    
    async def get_action_audit_logs(
        self,
        db: Session,
        action: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """Obtém logs de auditoria de uma ação"""
        try:
            logs = db.query(AuditLog)\
                .filter(AuditLog.action == action)\
                .order_by(AuditLog.created_at.desc())\
                .offset(skip)\
                .limit(limit)\
                .all()
            
            return logs
            
        except Exception as e:
            logger.error("Erro ao obter logs de auditoria", action=action, error=str(e))
            raise
    
    async def get_failed_audit_logs(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """Obtém logs de auditoria de ações que falharam"""
        try:
            logs = db.query(AuditLog)\
                .filter(AuditLog.success == False)\
                .order_by(AuditLog.created_at.desc())\
                .offset(skip)\
                .limit(limit)\
                .all()
            
            return logs
            
        except Exception as e:
            logger.error("Erro ao obter logs de auditoria de falhas", error=str(e))
            raise
    
    async def cleanup_old_logs(self, db: Session, days: int = 90) -> int:
        """Remove logs de auditoria antigos"""
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted_count = db.query(AuditLog)\
                .filter(AuditLog.created_at < cutoff_date)\
                .delete()
            
            db.commit()
            
            logger.info(
                "Logs de auditoria antigos removidos",
                deleted_count=deleted_count,
                cutoff_date=cutoff_date
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error("Erro ao limpar logs antigos", error=str(e))
            db.rollback()
            raise



