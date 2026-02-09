from sqlalchemy.orm import Session
from models.ai_model import AIModel
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AIModelsService:
    """Serviço para gerenciar modelos de IA"""
    
    @staticmethod
    def get_all_models(db: Session, available_only: bool = True) -> List[AIModel]:
        """Busca todos os modelos de IA"""
        query = db.query(AIModel)
        if available_only:
            query = query.filter(AIModel.is_available == True)
        return query.order_by(AIModel.name).all()
    
    @staticmethod
    def get_model_by_id(db: Session, model_id: str) -> Optional[AIModel]:
        """Busca modelo por ID"""
        return db.query(AIModel).filter(AIModel.model_id == model_id).first()
    
    @staticmethod
    def get_models_by_provider(db: Session, provider: str, available_only: bool = True) -> List[AIModel]:
        """Busca modelos por provedor"""
        query = db.query(AIModel).filter(AIModel.provider == provider)
        if available_only:
            query = query.filter(AIModel.is_available == True)
        return query.order_by(AIModel.name).all()
    
    @staticmethod
    def create_model(db: Session, model_data: Dict[str, Any]) -> AIModel:
        """Cria um novo modelo de IA"""
        model = AIModel(**model_data)
        db.add(model)
        db.commit()
        db.refresh(model)
        return model
    
    @staticmethod
    def update_model(db: Session, model_id: str, model_data: Dict[str, Any]) -> Optional[AIModel]:
        """Atualiza um modelo de IA"""
        model = AIModelsService.get_model_by_id(db, model_id)
        if not model:
            return None
        
        for key, value in model_data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        db.commit()
        db.refresh(model)
        return model
    
    @staticmethod
    def delete_model(db: Session, model_id: str) -> bool:
        """Deleta um modelo de IA"""
        model = AIModelsService.get_model_by_id(db, model_id)
        if not model:
            return False
        
        db.delete(model)
        db.commit()
        return True
    
    @staticmethod
    def get_model_cost_info(db: Session, model_id: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de custo do modelo"""
        model = AIModelsService.get_model_by_id(db, model_id)
        if not model:
            return None
        
        return {
            'model_id': model.model_id,
            'name': model.name,
            'provider': model.provider,
            'is_paid': model.is_paid,
            'cost_per_1k_tokens': model.cost_per_1k_tokens,
            'max_tokens_per_request': model.max_tokens_per_request
        }

# Instância global do serviço
ai_models_service = AIModelsService()
