#!/usr/bin/env python3
"""
Script para criar os schemas necessários no banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from db_session import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_schemas():
    """Cria os schemas commerce, chatbot e ai_management se não existirem"""
    schemas = ['commerce', 'chatbot', 'ai_management']
    
    try:
        with engine.connect() as conn:
            for schema in schemas:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                logger.info(f"Schema '{schema}' criado/verificado com sucesso")
            conn.commit()
            logger.info("✅ Todos os schemas foram criados/verificados com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro ao criar schemas: {e}")
        raise

if __name__ == "__main__":
    create_schemas()
