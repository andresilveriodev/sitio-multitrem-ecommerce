"""
Serviço para gestão de usuários
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import structlog

from models.acl import User
from models.auth import UserCreate, UserUpdate, UserInDB

logger = structlog.get_logger()


class UserService:
    """Serviço para operações CRUD de usuários"""
    
    def __init__(self):
        pass
    
    async def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtém lista de usuários com paginação"""
        try:
            users = db.query(User).offset(skip).limit(limit).all()
            return users
        except Exception as e:
            logger.error("Erro ao obter usuários", error=str(e))
            raise
    
    async def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Obtém usuário por ID"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
        except Exception as e:
            logger.error("Erro ao obter usuário por ID", user_id=user_id, error=str(e))
            raise
    
    async def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Obtém usuário por email"""
        try:
            user = db.query(User).filter(User.email == email).first()
            return user
        except Exception as e:
            logger.error("Erro ao obter usuário por email", email=email, error=str(e))
            raise
    
    async def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Obtém usuário por username"""
        try:
            user = db.query(User).filter(User.username == username).first()
            return user
        except Exception as e:
            logger.error("Erro ao obter usuário por username", username=username, error=str(e))
            raise
    
    async def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Cria novo usuário"""
        try:
            # Verificar se usuário já existe
            existing_user = await self.get_user_by_email(db, user_data.email)
            if existing_user:
                raise ValueError("Usuário com este email já existe")
            
            existing_user = await self.get_user_by_username(db, user_data.username)
            if existing_user:
                raise ValueError("Usuário com este username já existe")
            
            # Criar usuário
            user = User(
                username=user_data.username,
                email=user_data.email,
                keycloak_id=user_data.keycloak_id,
                is_active=user_data.is_active,
                is_verified=user_data.is_verified
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info("Usuário criado com sucesso", user_id=user.id, username=user.username)
            return user
            
        except Exception as e:
            logger.error("Erro ao criar usuário", error=str(e))
            db.rollback()
            raise
    
    async def update_user(self, db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Atualiza usuário"""
        try:
            user = await self.get_user_by_id(db, user_id)
            if not user:
                return None
            
            # Atualizar campos fornecidos
            update_data = user_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            db.commit()
            db.refresh(user)
            
            logger.info("Usuário atualizado com sucesso", user_id=user.id)
            return user
            
        except Exception as e:
            logger.error("Erro ao atualizar usuário", user_id=user_id, error=str(e))
            db.rollback()
            raise
    
    async def delete_user(self, db: Session, user_id: int) -> bool:
        """Deleta usuário"""
        try:
            user = await self.get_user_by_id(db, user_id)
            if not user:
                return False
            
            db.delete(user)
            db.commit()
            
            logger.info("Usuário deletado com sucesso", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Erro ao deletar usuário", user_id=user_id, error=str(e))
            db.rollback()
            raise
    
    async def activate_user(self, db: Session, user_id: int) -> bool:
        """Ativa usuário"""
        try:
            user = await self.get_user_by_id(db, user_id)
            if not user:
                return False
            
            user.is_active = True
            db.commit()
            
            logger.info("Usuário ativado com sucesso", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Erro ao ativar usuário", user_id=user_id, error=str(e))
            db.rollback()
            raise
    
    async def deactivate_user(self, db: Session, user_id: int) -> bool:
        """Desativa usuário"""
        try:
            user = await self.get_user_by_id(db, user_id)
            if not user:
                return False
            
            user.is_active = False
            db.commit()
            
            logger.info("Usuário desativado com sucesso", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Erro ao desativar usuário", user_id=user_id, error=str(e))
            db.rollback()
            raise
    
    async def verify_user(self, db: Session, user_id: int) -> bool:
        """Verifica usuário"""
        try:
            user = await self.get_user_by_id(db, user_id)
            if not user:
                return False
            
            user.is_verified = True
            db.commit()
            
            logger.info("Usuário verificado com sucesso", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Erro ao verificar usuário", user_id=user_id, error=str(e))
            db.rollback()
            raise
    
    async def search_users(self, db: Session, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Busca usuários por nome, email ou username"""
        try:
            users = db.query(User).filter(
                and_(
                    User.is_active == True,
                    (
                        User.username.ilike(f"%{query}%") |
                        User.email.ilike(f"%{query}%")
                    )
                )
            ).offset(skip).limit(limit).all()
            
            return users
            
        except Exception as e:
            logger.error("Erro ao buscar usuários", query=query, error=str(e))
            raise



