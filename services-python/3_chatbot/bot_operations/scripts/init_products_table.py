"""
Script para criar a tabela de produtos no banco de dados
Execute: python scripts/init_products_table.py
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.database_service import database_service
from models.product_models import Base
import structlog

logger = structlog.get_logger(__name__)


async def init_table():
    """Cria a tabela de produtos"""
    try:
        logger.info("Conectando ao banco de dados...")
        await database_service.connect()
        
        logger.info("Criando tabela de produtos...")
        async with database_service.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Tabela de produtos criada com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabela: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await database_service.disconnect()


if __name__ == "__main__":
    asyncio.run(init_table())
