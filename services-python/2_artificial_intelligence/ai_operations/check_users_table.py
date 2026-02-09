from app.db import engine
from sqlalchemy import text

def check_users_table():
    try:
        conn = engine.connect()
        
        # Verificar se a tabela users existe
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users'"))
        users_exists = result.fetchone() is not None
        print(f"Tabela users no schema public existe: {users_exists}")
        
        if users_exists:
            # Verificar estrutura da tabela users
            result = conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'users' ORDER BY ordinal_position"))
            columns = result.fetchall()
            print("\nEstrutura da tabela users:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
            
            # Verificar se a coluna id existe e é primary key
            result = conn.execute(text("""
                SELECT c.column_name, c.data_type, tc.constraint_type
                FROM information_schema.columns c
                LEFT JOIN information_schema.key_column_usage kcu ON c.table_name = kcu.table_name AND c.column_name = kcu.column_name
                LEFT JOIN information_schema.table_constraints tc ON kcu.constraint_name = tc.constraint_name
                WHERE c.table_schema = 'public' AND c.table_name = 'users' AND c.column_name = 'id'
            """))
            id_info = result.fetchone()
            if id_info:
                print(f"\nColuna id: {id_info[0]}, tipo: {id_info[1]}, constraint: {id_info[2]}")
            else:
                print("\n❌ Coluna 'id' não encontrada na tabela users!")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_users_table()


