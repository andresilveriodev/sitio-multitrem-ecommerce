"""Migração 006: Remover coluna username de user_subscriptions"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import DATABASE_URI as DATABASE_URL
import logging

logger = logging.getLogger(__name__)

def remove_username_column():
    """Remove coluna username de user_subscriptions"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Verifica se a coluna existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user_subscriptions' 
                AND column_name = 'username';
            """))
            
            if result.fetchone():
                logger.info("Removendo coluna username de user_subscriptions...")
                print("[*] Removendo coluna username...")
                
                # Remove índice se existir
                conn.execute(text("""
                    DROP INDEX IF EXISTS idx_user_subscriptions_username;
                """))
                
                # Remove a coluna
                conn.execute(text("""
                    ALTER TABLE user_subscriptions 
                    DROP COLUMN username;
                """))
                
                logger.info("Coluna username removida com sucesso!")
                print("[OK] Coluna username removida com sucesso!")
            else:
                logger.info("Coluna username nao existe")
                print("[INFO] Coluna username nao existe")
            
            conn.commit()
            print("[OK] Migracao concluida!")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro na migracao: {e}")
            print(f"[ERRO] Erro na migracao: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    remove_username_column()





