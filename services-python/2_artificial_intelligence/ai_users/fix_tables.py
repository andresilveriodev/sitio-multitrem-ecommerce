#!/usr/bin/env python3
"""
Script para criar tabelas com schema correto
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, MetaData
from app.db import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables_manually():
    """Cria as tabelas manualmente com SQL direto"""
    
    sql_commands = [
        # Criar schema
        "CREATE SCHEMA IF NOT EXISTS chatbot;",
        
        # Tabela users
        """
        CREATE TABLE IF NOT EXISTS chatbot.users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            full_name VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            total_tokens_used INTEGER DEFAULT 0 NOT NULL,
            total_cost_spent FLOAT DEFAULT 0.0 NOT NULL,
            total_requests INTEGER DEFAULT 0 NOT NULL,
            total_conversations INTEGER DEFAULT 0 NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Tabela conversations
        """
        CREATE TABLE IF NOT EXISTS chatbot.conversations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES chatbot.users(id),
            title VARCHAR(200),
            total_tokens INTEGER DEFAULT 0,
            total_cost FLOAT DEFAULT 0.0,
            model_used VARCHAR(100),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Tabela transactions
        """
        CREATE TABLE IF NOT EXISTS chatbot.transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES chatbot.users(id),
            conversation_id INTEGER REFERENCES chatbot.conversations(id),
            model_name VARCHAR(100) NOT NULL,
            provider VARCHAR(50) NOT NULL,
            request_tokens INTEGER DEFAULT 0,
            response_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            cost FLOAT DEFAULT 0.0,
            request_data TEXT,
            response_data TEXT,
            processing_time FLOAT,
            status VARCHAR(20) DEFAULT 'completed',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Tabela usage
        """
        CREATE TABLE IF NOT EXISTS chatbot.usage (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES chatbot.users(id),
            model_name VARCHAR(100) NOT NULL,
            provider VARCHAR(50) NOT NULL,
            period_start TIMESTAMP NOT NULL,
            period_end TIMESTAMP NOT NULL,
            total_requests INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            total_cost FLOAT DEFAULT 0.0,
            avg_processing_time FLOAT DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Índices para performance
        "CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON chatbot.transactions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_transactions_conversation_id ON chatbot.transactions(conversation_id);",
        "CREATE INDEX IF NOT EXISTS idx_transactions_model_name ON chatbot.transactions(model_name);",
        "CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON chatbot.transactions(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON chatbot.conversations(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_usage_user_id ON chatbot.usage(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_usage_period ON chatbot.usage(period_start, period_end);"
    ]
    
    try:
        with engine.connect() as conn:
            for sql in sql_commands:
                logger.info(f"Executando: {sql[:50]}...")
                conn.execute(text(sql))
            
            conn.commit()
            logger.info("✅ Todas as tabelas foram criadas com sucesso!")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        raise

def verify_tables():
    """Verifica se as tabelas foram criadas corretamente"""
    try:
        with engine.connect() as conn:
            # Listar tabelas no schema chatbot
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'chatbot'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result]
            logger.info(f"📋 Tabelas criadas: {tables}")
            
            # Verificar estrutura de cada tabela
            for table in tables:
                result = conn.execute(text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'chatbot' 
                    AND table_name = '{table}'
                    ORDER BY ordinal_position;
                """))
                
                columns = [(row[0], row[1]) for row in result]
                logger.info(f"📊 Tabela '{table}': {len(columns)} colunas")
                
    except Exception as e:
        logger.error(f"❌ Erro ao verificar tabelas: {e}")

def main():
    """Executa a criação e verificação das tabelas"""
    logger.info("🚀 Iniciando criação manual das tabelas")
    
    try:
        create_tables_manually()
        verify_tables()
        logger.info("🎉 Processo concluído com sucesso!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Erro durante o processo: {e}")
        return 1

if __name__ == "__main__":
    exit(main())