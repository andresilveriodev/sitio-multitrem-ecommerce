#!/usr/bin/env python3
"""
Script para criar todas as tabelas do Commerce Service
Ignora erros de tabelas/índices já existentes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from sqlalchemy.exc import ProgrammingError
from db_session import engine, Base
from models import (
    ProductCategory, Product, PriceList, ProductPrice, PriceProfile,
    Customer, CustomerAddress, CustomerProductPrice, DeliveryZone,
    Order, OrderItem, Payment, DeliveryRoute, DeliveryStop, AuditLog,
    ChannelAccount, Conversation, Message, IntentRule, Outbox
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables_safe():
    """Cria todas as tabelas, ignorando erros de tabelas já existentes"""
    try:
        logger.info("Criando todas as tabelas...")
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("✅ Todas as tabelas foram criadas/verificadas com sucesso!")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Erro ao criar tabelas (pode ser normal se já existirem): {e}")
        # Tenta criar individualmente
        try:
            for table in Base.metadata.sorted_tables:
                try:
                    table.create(bind=engine, checkfirst=True)
                    logger.info(f"✅ Tabela {table.name} criada/verificada")
                except Exception as e2:
                    logger.warning(f"⚠️ Tabela {table.name} pode já existir: {e2}")
            return True
        except Exception as e3:
            logger.error(f"❌ Erro ao criar tabelas individualmente: {e3}")
            return False

def verify_tables():
    """Verifica quais tabelas existem"""
    inspector = inspect(engine)
    schemas = ['commerce', 'chatbot']
    
    for schema in schemas:
        try:
            tables = inspector.get_table_names(schema=schema)
            logger.info(f"\n📊 Schema '{schema}': {len(tables)} tabelas")
            for table in tables:
                columns = inspector.get_columns(table, schema=schema)
                logger.info(f"  ✅ {schema}.{table} ({len(columns)} colunas)")
        except Exception as e:
            logger.warning(f"⚠️ Schema {schema} não encontrado ou erro: {e}")

def main():
    """Executa a criação das tabelas"""
    logger.info("🚀 Criando tabelas do Commerce Service")
    logger.info("="*60)
    
    # Criar tabelas
    if create_tables_safe():
        # Verificar tabelas criadas
        verify_tables()
        logger.info("\n✅ Processo concluído!")
        return 0
    else:
        logger.error("\n❌ Erro ao criar tabelas!")
        return 1

if __name__ == "__main__":
    exit(main())
