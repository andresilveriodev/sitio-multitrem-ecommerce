#!/usr/bin/env python3
"""
Script para criar todas as tabelas do sistema de tracking
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.db import engine
from models import BaseModel
from models.user import User
from models.conversation import Conversation
from models.transaction import Transaction
from models.usage import Usage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_schema():
    """Cria o schema chatbot se não existir"""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS chatbot"))
            conn.commit()
            logger.info("Schema 'chatbot' criado/verificado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar schema: {e}")
        raise

def check_existing_tables():
    """Verifica quais tabelas já existem"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema='chatbot')
        logger.info(f"Tabelas existentes no schema 'chatbot': {tables}")
        return tables
    except Exception as e:
        logger.error(f"Erro ao verificar tabelas existentes: {e}")
        return []

def create_all_tables():
    """Cria todas as tabelas definidas nos modelos"""
    try:
        # Criar todas as tabelas
        BaseModel.metadata.create_all(bind=engine)
        logger.info("Todas as tabelas foram criadas com sucesso")
        
        # Verificar tabelas criadas
        tables_after = check_existing_tables()
        logger.info(f"Tabelas após criação: {tables_after}")
        
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise

def verify_table_structure():
    """Verifica a estrutura das tabelas criadas"""
    try:
        inspector = inspect(engine)
        
        for table_name in ['users', 'conversations', 'transactions', 'usage']:
            try:
                columns = inspector.get_columns(table_name, schema='chatbot')
                logger.info(f"Tabela '{table_name}' - Colunas: {[col['name'] for col in columns]}")
            except Exception as e:
                logger.warning(f"Tabela '{table_name}' não encontrada: {e}")
                
    except Exception as e:
        logger.error(f"Erro ao verificar estrutura das tabelas: {e}")

def main():
    """Executa a criação completa das tabelas"""
    logger.info("🚀 Iniciando criação das tabelas do sistema de tracking")
    
    try:
        # Passo 1: Criar schema
        create_schema()
        
        # Passo 2: Verificar tabelas existentes
        existing_tables = check_existing_tables()
        
        # Passo 3: Criar todas as tabelas
        create_all_tables()
        
        # Passo 4: Verificar estrutura
        verify_table_structure()
        
        logger.info("✅ Criação das tabelas concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante a criação das tabelas: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())