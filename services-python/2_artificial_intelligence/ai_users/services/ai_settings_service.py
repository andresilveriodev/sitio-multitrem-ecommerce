from sqlalchemy.orm import Session
from models.user_ai_settings import UserAISettings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AISettingsService:
    """Serviço para gerenciar configurações de IA dos usuários"""
    
    @staticmethod
    def get_user_settings(db: Session, user_id: int) -> Optional[UserAISettings]:
        """Busca configurações de IA do usuário"""
        return db.query(UserAISettings).filter(UserAISettings.user_id == user_id).first()
    
    @staticmethod
    def create_or_update_settings(db: Session, user_id: int, username: str, settings_data: Dict[str, Any]) -> UserAISettings:
        """Cria ou atualiza configurações de IA do usuário"""
        settings = AISettingsService.get_user_settings(db, user_id)
        
        if not settings:
            # Cria novas configurações
            settings_data['user_id'] = user_id
            settings_data['username'] = username
            settings = UserAISettings(**settings_data)
            db.add(settings)
        else:
            # Atualiza configurações existentes
            for key, value in settings_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
        
        db.commit()
        db.refresh(settings)
        return settings
    
    @staticmethod
    def get_default_model(db: Session, user_id: int) -> str:
        """Obtém o modelo padrão do usuário"""
        settings = AISettingsService.get_user_settings(db, user_id)
        if settings:
            return settings.default_model
        return 'ollama'  # Modelo padrão
    
    @staticmethod
    def get_preferred_models(db: Session, user_id: int) -> list:
        """Obtém os modelos preferidos do usuário"""
        settings = AISettingsService.get_user_settings(db, user_id)
        if settings and settings.preferred_models:
            return settings.preferred_models
        return ['ollama', 'deepseek']  # Modelos padrão
    
    @staticmethod
    def update_default_model(db: Session, user_id: int, model_id: str) -> bool:
        """Atualiza o modelo padrão do usuário"""
        settings = AISettingsService.get_user_settings(db, user_id)
        if not settings:
            # Cria configurações se não existirem
            settings = UserAISettings(user_id=user_id, default_model=model_id)
            db.add(settings)
        else:
            settings.default_model = model_id
        
        db.commit()
        return True
    
    @staticmethod
    def update_preferred_models(db: Session, user_id: int, models: list) -> bool:
        """Atualiza os modelos preferidos do usuário"""
        settings = AISettingsService.get_user_settings(db, user_id)
        if not settings:
            # Cria configurações se não existirem
            settings = UserAISettings(user_id=user_id, preferred_models=models)
            db.add(settings)
        else:
            settings.preferred_models = models
        
        db.commit()
        return True
    
    @staticmethod
    def get_notification_settings(db: Session, user_id: int) -> Dict[str, Any]:
        """Obtém configurações de notificação do usuário"""
        settings = AISettingsService.get_user_settings(db, user_id)
        if settings and settings.notifications:
            return settings.notifications
        return {
            'usage_alerts': True,
            'cost_alerts': True,
            'limit_alerts': True,
            'email_notifications': False
        }
    
    @staticmethod
    def update_notification_settings(db: Session, user_id: int, notification_settings: Dict[str, Any]) -> bool:
        """Atualiza configurações de notificação do usuário"""
        settings = AISettingsService.get_user_settings(db, user_id)
        if not settings:
            # Cria configurações se não existirem
            settings = UserAISettings(user_id=user_id, notifications=notification_settings)
            db.add(settings)
        else:
            settings.notifications = notification_settings
        
        db.commit()
        return True

# Instância global do serviço
ai_settings_service = AISettingsService()
