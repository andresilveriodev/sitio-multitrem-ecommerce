"""
Script para limpar o banco de dados
"""

from db_session import engine
from sqlalchemy import text

def clean_database():
    """Limpa completamente o banco de dados"""
    try:
        with engine.connect() as conn:
            # Remover schema público e recriar
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
            print("✅ Schema público removido e recriado")
            
            # Recriar tabelas
            from db_session import create_tables
            create_tables()
            print("✅ Tabelas recriadas")
            
    except Exception as e:
        print(f"❌ Erro ao limpar banco: {e}")

if __name__ == "__main__":
    clean_database()



