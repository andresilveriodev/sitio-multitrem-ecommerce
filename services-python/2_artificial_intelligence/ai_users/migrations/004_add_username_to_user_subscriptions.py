"""Migração 004: Adicionar coluna username em user_subscriptions"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import DATABASE_URI as DATABASE_URL
import logging

logger = logging.getLogger(__name__)

def add_username_column():
    """Adiciona coluna username em user_subscriptions se não existir"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Verifica se a coluna já existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user_subscriptions' 
                AND column_name = 'username';
            """))
            
            if result.fetchone():
                logger.info("Coluna username ja existe em user_subscriptions")
                print("[INFO] Coluna username ja existe")
            else:
                # Adiciona a coluna username
                logger.info("Adicionando coluna username em user_subscriptions...")
                conn.execute(text("""
                    ALTER TABLE user_subscriptions 
                    ADD COLUMN username VARCHAR(50) DEFAULT 'user';
                """))
                
                # Atualiza registros existentes sem username
                conn.execute(text("""
                    UPDATE user_subscriptions 
                    SET username = 'user_' || user_id::text 
                    WHERE username IS NULL OR username = 'user';
                """))
                
                # Torna a coluna NOT NULL
                conn.execute(text("""
                    ALTER TABLE user_subscriptions 
                    ALTER COLUMN username SET NOT NULL;
                """))
                
                # Cria índice para performance
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_user_subscriptions_username 
                    ON user_subscriptions(username);
                """))
                
                logger.info("Coluna username adicionada com sucesso!")
                print("[OK] Coluna username adicionada com sucesso!")
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro na migracao: {e}")
            print(f"[ERRO] Erro na migracao: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    add_username_column()

