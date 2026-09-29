#!/usr/bin/env python3
"""
Script para inicializar o banco de dados do Commerce Service
Cria schemas e todas as tabelas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from db_session import engine, Base, create_schemas
from models import (
    # Commerce models
    ProductCategory,
    Product,
    PriceList,
    ProductPrice,
    PriceProfile,
    Customer,
    CustomerAddress,
    CustomerProductPrice,
    DeliveryZone,
    Order,
    OrderItem,
    Payment,
    DeliveryRoute,
    DeliveryStop,
    AuditLog,
    # Chatbot models
    ChannelAccount,
    Conversation,
    Message,
    IntentRule,
    Outbox
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_existing_tables():
    """Verifica quais tabelas já existem"""
    inspector = inspect(engine)
    existing_tables = []
    
    for schema in ['commerce', 'chatbot']:
        try:
            tables = inspector.get_table_names(schema=schema)
            existing_tables.extend([f"{schema}.{table}" for table in tables])
        except Exception as e:
            logger.warning(f"Schema {schema} ainda não existe ou erro ao verificar: {e}")
    
    return existing_tables

def create_all_tables():
    """Cria todas as tabelas"""
    try:
        logger.info("Criando todas as tabelas...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Todas as tabelas foram criadas/verificadas com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        raise

def verify_table_structure():
    """Verifica a estrutura das tabelas criadas"""
    try:
        inspector = inspect(engine)
        schemas_to_check = ['commerce', 'chatbot']
        
        for schema in schemas_to_check:
            tables = inspector.get_table_names(schema=schema)
            logger.info(f"Tabelas no schema '{schema}': {len(tables)}")
            for table in tables:
                columns = inspector.get_columns(table, schema=schema)
                logger.info(f"  - {schema}.{table}: {len(columns)} colunas")
    except Exception as e:
        logger.error(f"Erro ao verificar estrutura das tabelas: {e}")

def main():
    """Executa a inicialização completa do banco de dados"""
    logger.info("🚀 Iniciando inicialização do banco de dados do Commerce Service")
    
    try:
        # Passo 1: Criar schemas
        logger.info("Passo 1: Criando schemas...")
        create_schemas()
        
        # Passo 2: Verificar tabelas existentes
        logger.info("Passo 2: Verificando tabelas existentes...")
        existing_tables = check_existing_tables()
        if existing_tables:
            logger.info(f"Tabelas já existentes: {existing_tables}")
        
        # Passo 3: Criar todas as tabelas
        logger.info("Passo 3: Criando todas as tabelas...")
        create_all_tables()
        
        # Passo 4: Verificar estrutura
        logger.info("Passo 4: Verificando estrutura das tabelas...")
        verify_table_structure()
        
        logger.info("✅ Inicialização do banco de dados concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante a inicialização do banco de dados: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
