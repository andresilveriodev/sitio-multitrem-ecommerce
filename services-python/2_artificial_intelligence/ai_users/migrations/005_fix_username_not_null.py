"""Migração 005: Tornar username NOT NULL em user_subscriptions"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import DATABASE_URI as DATABASE_URL
import logging

logger = logging.getLogger(__name__)

def fix_username_not_null():
    """Torna username NOT NULL e atualiza valores nulos"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Verifica se há valores NULL
            result = conn.execute(text("""
                SELECT COUNT(*) FROM user_subscriptions WHERE username IS NULL;
            """))
            null_count = result.scalar()
            
            if null_count > 0:
                logger.info(f"Atualizando {null_count} registros com username NULL...")
                print(f"[*] Atualizando {null_count} registros com username NULL...")
                
                # Atualiza registros com username NULL
                conn.execute(text("""
                    UPDATE user_subscriptions 
                    SET username = 'user_' || user_id::text 
                    WHERE username IS NULL;
                """))
            
            # Verifica se a coluna já é NOT NULL
            result = conn.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'user_subscriptions' 
                AND column_name = 'username';
            """))
            
            is_nullable = result.scalar()
            
            if is_nullable == 'YES':
                logger.info("Tornando username NOT NULL...")
                print("[*] Tornando username NOT NULL...")
                
                conn.execute(text("""
                    ALTER TABLE user_subscriptions 
                    ALTER COLUMN username SET NOT NULL;
                """))
                
                logger.info("Username agora e NOT NULL!")
                print("[OK] Username agora e NOT NULL!")
            else:
                logger.info("Username ja e NOT NULL")
                print("[INFO] Username ja e NOT NULL")
            
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
    fix_username_not_null()





