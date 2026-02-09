"""Migração 003: Alterar user_id de INTEGER para VARCHAR (UUID)"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import DATABASE_URI as DATABASE_URL
import logging

logger = logging.getLogger(__name__)

def alter_user_id_to_uuid():
    """Altera user_id de INTEGER para VARCHAR para aceitar UUID"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # 1. Remove foreign key constraint de user_subscriptions
            logger.info("Removendo foreign key constraint de user_subscriptions...")
            conn.execute(text("""
                ALTER TABLE user_subscriptions 
                DROP CONSTRAINT IF EXISTS user_subscriptions_user_id_fkey;
            """))
            
            # 2. Altera user_id para VARCHAR(50) em user_subscriptions
            logger.info("Alterando user_id para VARCHAR(50) em user_subscriptions...")
            conn.execute(text("""
                ALTER TABLE user_subscriptions 
                ALTER COLUMN user_id TYPE VARCHAR(50) USING user_id::VARCHAR(50);
            """))
            
            # 3. Remove foreign key constraint de user_ai_settings
            logger.info("Removendo foreign key constraint de user_ai_settings...")
            conn.execute(text("""
                ALTER TABLE user_ai_settings 
                DROP CONSTRAINT IF EXISTS user_ai_settings_user_id_fkey;
            """))
            
            # 4. Altera user_id para VARCHAR(50) em user_ai_settings
            logger.info("Alterando user_id para VARCHAR(50) em user_ai_settings...")
            conn.execute(text("""
                ALTER TABLE user_ai_settings 
                ALTER COLUMN user_id TYPE VARCHAR(50) USING user_id::VARCHAR(50);
            """))
            
            # 5. Remove foreign key constraint de ai_usage_alerts
            logger.info("Removendo foreign key constraint de ai_usage_alerts...")
            conn.execute(text("""
                ALTER TABLE ai_usage_alerts 
                DROP CONSTRAINT IF EXISTS ai_usage_alerts_user_id_fkey;
            """))
            
            # 6. Altera user_id para VARCHAR(50) em ai_usage_alerts
            logger.info("Alterando user_id para VARCHAR(50) em ai_usage_alerts...")
            conn.execute(text("""
                ALTER TABLE ai_usage_alerts 
                ALTER COLUMN user_id TYPE VARCHAR(50) USING user_id::VARCHAR(50);
            """))
            
            conn.commit()
            logger.info("Migracao concluida: user_id alterado para VARCHAR(50) em todas as tabelas!")
            print("[OK] Migracao concluida com sucesso!")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro na migracao: {e}")
            print(f"[ERRO] Erro na migracao: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    alter_user_id_to_uuid()

