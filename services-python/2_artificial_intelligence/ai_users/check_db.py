from app.db import engine
from sqlalchemy import text

def check_database():
    try:
        conn = engine.connect()
        
        # Verificar se a tabela users existe no schema public
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users'"))
        users_exists = result.fetchone() is not None
        print(f"Tabela users no schema public existe: {users_exists}")
        
        # Verificar schemas existentes
        result = conn.execute(text("SELECT schema_name FROM information_schema.schemata"))
        schemas = [row[0] for row in result.fetchall()]
        print(f"Schemas existentes: {schemas}")
        
        # Verificar tabelas no schema chatbot
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'chatbot'"))
        chatbot_tables = [row[0] for row in result.fetchall()]
        print(f"Tabelas no schema chatbot: {chatbot_tables}")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")

if __name__ == "__main__":
    check_database()


