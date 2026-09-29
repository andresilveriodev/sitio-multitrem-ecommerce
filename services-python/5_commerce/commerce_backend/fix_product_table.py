#!/usr/bin/env python3
"""
Script para criar a tabela product manualmente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from db_session import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_product_table():
    """Cria a tabela product manualmente"""
    sql = """
    CREATE TABLE IF NOT EXISTS commerce.product (
        id SERIAL PRIMARY KEY,
        category_id INTEGER NOT NULL,
        sku VARCHAR(50) UNIQUE,
        name VARCHAR(200) NOT NULL,
        unit VARCHAR(20) NOT NULL,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
        FOREIGN KEY(category_id) REFERENCES commerce.product_category(id)
    );
    
    CREATE INDEX IF NOT EXISTS ix_commerce_product_category_id ON commerce.product(category_id);
    CREATE INDEX IF NOT EXISTS ix_commerce_product_sku ON commerce.product(sku) WHERE sku IS NOT NULL;
    CREATE INDEX IF NOT EXISTS ix_commerce_product_id ON commerce.product(id);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
            logger.info("✅ Tabela product criada com sucesso!")
            return True
    except Exception as e:
        logger.warning(f"⚠️ Erro ao criar tabela product (pode já existir): {e}")
        return False

def create_dependent_tables():
    """Cria tabelas que dependem de product"""
    tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS commerce.product_price (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL,
            price_list_id INTEGER NOT NULL,
            price NUMERIC(10, 2) NOT NULL,
            valid_from DATE,
            valid_to DATE,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            FOREIGN KEY(product_id) REFERENCES commerce.product(id),
            FOREIGN KEY(price_list_id) REFERENCES commerce.price_list(id)
        );
        CREATE INDEX IF NOT EXISTS idx_product_price_composite ON commerce.product_price(product_id, price_list_id, valid_from);
        CREATE INDEX IF NOT EXISTS ix_commerce_product_price_product_id ON commerce.product_price(product_id);
        CREATE INDEX IF NOT EXISTS ix_commerce_product_price_price_list_id ON commerce.product_price(price_list_id);
        """,
        """
        CREATE TABLE IF NOT EXISTS commerce.customer_product_price (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            price NUMERIC(10, 2) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            FOREIGN KEY(customer_id) REFERENCES commerce.customer(id),
            FOREIGN KEY(product_id) REFERENCES commerce.product(id),
            UNIQUE(customer_id, product_id)
        );
        CREATE INDEX IF NOT EXISTS idx_customer_product_price_unique ON commerce.customer_product_price(customer_id, product_id);
        CREATE INDEX IF NOT EXISTS ix_commerce_customer_product_price_customer_id ON commerce.customer_product_price(customer_id);
        CREATE INDEX IF NOT EXISTS ix_commerce_customer_product_price_product_id ON commerce.customer_product_price(product_id);
        """,
        """
        CREATE TABLE IF NOT EXISTS commerce.order_item (
            id SERIAL PRIMARY KEY,
            order_id UUID NOT NULL,
            product_id INTEGER NOT NULL,
            qty NUMERIC(10, 2) NOT NULL,
            unit_price NUMERIC(10, 2) NOT NULL,
            subtotal NUMERIC(10, 2) NOT NULL,
            notes TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            FOREIGN KEY(order_id) REFERENCES commerce."order"(id),
            FOREIGN KEY(product_id) REFERENCES commerce.product(id)
        );
        CREATE INDEX IF NOT EXISTS idx_order_item_order ON commerce.order_item(order_id);
        CREATE INDEX IF NOT EXISTS idx_order_item_product ON commerce.order_item(product_id);
        CREATE INDEX IF NOT EXISTS ix_commerce_order_item_order_id ON commerce.order_item(order_id);
        CREATE INDEX IF NOT EXISTS ix_commerce_order_item_product_id ON commerce.order_item(product_id);
        """
    ]
    
    try:
        with engine.connect() as conn:
            for sql in tables_sql:
                try:
                    conn.execute(text(sql))
                    logger.info("✅ Tabela dependente criada!")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao criar tabela dependente (pode já existir): {e}")
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas dependentes: {e}")
        return False

def main():
    """Executa a criação das tabelas"""
    logger.info("🔧 Corrigindo tabela product e dependentes")
    logger.info("="*60)
    
    if create_product_table():
        create_dependent_tables()
        logger.info("\n✅ Processo concluído!")
        return 0
    else:
        logger.error("\n❌ Erro ao criar tabelas!")
        return 1

if __name__ == "__main__":
    exit(main())
