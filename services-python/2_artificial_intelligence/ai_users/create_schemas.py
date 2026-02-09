#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar os schemas chatbot e ai_management
"""

from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do banco de dados
DATABASE_URL = "postgresql://postgres:123456@localhost:5434/sitio_multitrem"

def create_schemas():
    """Cria os schemas chatbot e ai_management se não existirem"""
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Criar schema chatbot
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS chatbot"))
            logger.info("✅ Schema 'chatbot' criado/verificado")
            
            # Criar schema ai_management
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS ai_management"))
            logger.info("✅ Schema 'ai_management' criado/verificado")
            
            conn.commit()
            
            # Verificar schemas criados
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name IN ('chatbot', 'ai_management')
                ORDER BY schema_name
            """))
            schemas = result.fetchall()
            
            logger.info("\n📋 Schemas encontrados no banco:")
            for schema in schemas:
                logger.info(f"  ✅ {schema[0]}")
            
            if len(schemas) == 2:
                logger.info("\n🎉 Ambos os schemas foram criados com sucesso!")
            else:
                logger.warning(f"\n⚠️ Apenas {len(schemas)} schema(s) encontrado(s)")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar schemas: {e}")
        raise

if __name__ == "__main__":
    create_schemas()
