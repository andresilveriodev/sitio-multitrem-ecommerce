#!/usr/bin/env python3
"""
Script de migração para adicionar tabelas de perfil de usuário
"""

import asyncio
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings
from models.acl import Base
from models.user_profile import UserProfileData, UserPreferences, UserSettings, UserActivity

logger = structlog.get_logger()

def migrate_user_profile_tables():
    """Adiciona tabelas de perfil de usuário ao banco existente"""
    try:
        logger.info("Iniciando migração das tabelas de perfil de usuário")
        
        # Criar engine do banco
        engine = create_engine(
            settings.DATABASE_URI,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE
        )
        
        # Verificar se as tabelas já existem
        inspector = engine.dialect.inspector(engine)
        existing_tables = inspector.get_table_names()
        
        tables_to_create = [
            "user_profiles_data",
            "user_preferences", 
            "user_settings",
            "user_activities"
        ]
        
        missing_tables = [table for table in tables_to_create if table not in existing_tables]
        
        if not missing_tables:
            logger.info("Todas as tabelas de perfil de usuário já existem")
            return
        
        logger.info(f"Criando tabelas: {missing_tables}")
        
        # Criar apenas as tabelas que não existem
        for table_name in missing_tables:
            if table_name == "user_profiles_data":
                UserProfileData.__table__.create(engine, checkfirst=True)
            elif table_name == "user_preferences":
                UserPreferences.__table__.create(engine, checkfirst=True)
            elif table_name == "user_settings":
                UserSettings.__table__.create(engine, checkfirst=True)
            elif table_name == "user_activities":
                UserActivity.__table__.create(engine, checkfirst=True)
        
        logger.info("Migração das tabelas de perfil de usuário concluída")
        
        # Criar índices adicionais se necessário
        create_additional_indexes(engine)
        
    except Exception as e:
        logger.error("Erro na migração das tabelas de perfil de usuário", error=str(e))
        raise

def create_additional_indexes(engine):
    """Cria índices adicionais para melhor performance"""
    try:
        logger.info("Criando índices adicionais")
        
        # Índices para user_activities
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_activities_user_id_created_at ON user_activities(user_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_user_activities_activity_type ON user_activities(activity_type)",
            "CREATE INDEX IF NOT EXISTS idx_user_activities_created_at ON user_activities(created_at DESC)",
        ]
        
        with engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {index_sql}", error=str(e))
        
        logger.info("Índices adicionais criados")
        
    except Exception as e:
        logger.error("Erro ao criar índices adicionais", error=str(e))

def verify_migration():
    """Verifica se a migração foi bem-sucedida"""
    try:
        logger.info("Verificando migração")
        
        engine = create_engine(settings.DATABASE_URI)
        inspector = engine.dialect.inspector(engine)
        
        required_tables = [
            "user_profiles_data",
            "user_preferences", 
            "user_settings",
            "user_activities"
        ]
        
        existing_tables = inspector.get_table_names()
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.error(f"Tabelas faltando: {missing_tables}")
            return False
        
        logger.info("Migração verificada com sucesso")
        return True
        
    except Exception as e:
        logger.error("Erro ao verificar migração", error=str(e))
        return False

if __name__ == "__main__":
    try:
        migrate_user_profile_tables()
        
        if verify_migration():
            logger.info("Migração concluída com sucesso!")
        else:
            logger.error("Migração falhou na verificação")
            exit(1)
            
    except Exception as e:
        logger.error("Erro durante a migração", error=str(e))
        exit(1)



