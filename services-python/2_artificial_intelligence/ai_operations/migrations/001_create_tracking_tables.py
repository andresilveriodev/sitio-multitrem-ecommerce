"""Migration para criar tabelas de tracking de transações e uso

Cria as tabelas:
- transactions: para armazenar transações de IA
- usage: para métricas agregadas de uso
- usage_summary: para resumos de uso por período
- Atualiza tabelas existentes com novas colunas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import engine, Session
from models import BaseModel
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """Aplica as mudanças do banco de dados"""
    try:
        # Criar schema se não existir
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS chatbot"))
            conn.commit()
        
        # Criar todas as tabelas
        BaseModel.metadata.create_all(bind=engine)
        
        # Adicionar colunas de métricas na tabela users se não existirem
        with engine.connect() as conn:
            # Verificar se as colunas já existem
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'chatbot' 
                AND table_name = 'users' 
                AND column_name IN ('total_tokens_used', 'total_cost_spent', 'total_requests', 'total_conversations')
            """))
            
            existing_columns = [row[0] for row in result]
            
            # Adicionar colunas que não existem
            if 'total_tokens_used' not in existing_columns:
                conn.execute(text("ALTER TABLE chatbot.users ADD COLUMN total_tokens_used INTEGER DEFAULT 0 NOT NULL"))
            
            if 'total_cost_spent' not in existing_columns:
                conn.execute(text("ALTER TABLE chatbot.users ADD COLUMN total_cost_spent FLOAT DEFAULT 0.0 NOT NULL"))
            
            if 'total_requests' not in existing_columns:
                conn.execute(text("ALTER TABLE chatbot.users ADD COLUMN total_requests INTEGER DEFAULT 0 NOT NULL"))
            
            if 'total_conversations' not in existing_columns:
                conn.execute(text("ALTER TABLE chatbot.users ADD COLUMN total_conversations INTEGER DEFAULT 0 NOT NULL"))
            
            conn.commit()
        
        logger.info("Migration 001 aplicada com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao aplicar migration 001: {e}")
        raise

def downgrade():
    """Reverte as mudanças do banco de dados"""
    try:
        with engine.connect() as conn:
            # Remover tabelas criadas
            conn.execute(text("DROP TABLE IF EXISTS chatbot.usage_summary CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS chatbot.usage CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS chatbot.transactions CASCADE"))
            
            # Remover colunas adicionadas
            conn.execute(text("ALTER TABLE chatbot.users DROP COLUMN IF EXISTS total_tokens_used"))
            conn.execute(text("ALTER TABLE chatbot.users DROP COLUMN IF EXISTS total_cost_spent"))
            conn.execute(text("ALTER TABLE chatbot.users DROP COLUMN IF EXISTS total_requests"))
            conn.execute(text("ALTER TABLE chatbot.users DROP COLUMN IF EXISTS total_conversations"))
            
            conn.commit()
        
        logger.info("Migration 001 revertida com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao reverter migration 001: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()