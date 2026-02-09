#!/usr/bin/env python3
"""
Script de migração para adicionar campos first_name e last_name na tabela users
"""

import asyncio
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings

logger = structlog.get_logger()

def migrate_user_fields():
    """Adiciona campos first_name e last_name na tabela users"""
    try:
        logger.info("Iniciando migração dos campos first_name e last_name")
        
        # Criar engine do banco
        engine = create_engine(
            settings.DATABASE_URI,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE
        )
        
        # Verificar se os campos já existem
        with engine.connect() as conn:
            # Verificar se first_name existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'first_name'
            """))
            first_name_exists = result.fetchone() is not None
            
            # Verificar se last_name existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'last_name'
            """))
            last_name_exists = result.fetchone() is not None
            
            if first_name_exists and last_name_exists:
                logger.info("Campos first_name e last_name já existem na tabela users")
                return
            
            # Adicionar campos se não existirem
            if not first_name_exists:
                logger.info("Adicionando campo first_name")
                conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(100)"))
                conn.commit()
            
            if not last_name_exists:
                logger.info("Adicionando campo last_name")
                conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(100)"))
                conn.commit()
        
        logger.info("Migração dos campos first_name e last_name concluída")
        
    except Exception as e:
        logger.error("Erro na migração dos campos first_name e last_name", error=str(e))
        raise

def verify_migration():
    """Verifica se a migração foi bem-sucedida"""
    try:
        logger.info("Verificando migração")
        
        engine = create_engine(settings.DATABASE_URI)
        
        with engine.connect() as conn:
            # Verificar se os campos existem
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('first_name', 'last_name')
                ORDER BY column_name
            """))
            
            columns = [row[0] for row in result.fetchall()]
            
            if len(columns) == 2 and 'first_name' in columns and 'last_name' in columns:
                logger.info("Migração verificada com sucesso")
                return True
            else:
                logger.error(f"Campos faltando. Encontrados: {columns}")
                return False
        
    except Exception as e:
        logger.error("Erro ao verificar migração", error=str(e))
        return False

if __name__ == "__main__":
    try:
        migrate_user_fields()
        
        if verify_migration():
            logger.info("Migração concluída com sucesso!")
        else:
            logger.error("Migração falhou na verificação")
            exit(1)
            
    except Exception as e:
        logger.error("Erro durante a migração", error=str(e))
        exit(1)



