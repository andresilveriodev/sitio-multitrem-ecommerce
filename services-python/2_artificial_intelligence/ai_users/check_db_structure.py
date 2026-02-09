#!/usr/bin/env python3
import psycopg2
from psycopg2 import sql

def check_table_structure():
    try:
        # Conectar ao banco
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5434/sitio_multitrem')
        cur = conn.cursor()
        
        print("🔍 Verificando estrutura da tabela 'conversations'...")
        print("=" * 50)
        
        # Verificar se a tabela existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'conversations'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("❌ Tabela 'conversations' NÃO EXISTE!")
            return
        
        print("✅ Tabela 'conversations' existe!")
        print()
        
        # Listar colunas da tabela
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'conversations' 
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        print("📋 Colunas da tabela:")
        for col in columns:
            print(f"  • {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        print()
        
        # Verificar se a coluna username existe
        username_exists = any(col[0] == 'username' for col in columns)
        if username_exists:
            print("✅ Coluna 'username' existe!")
        else:
            print("❌ Coluna 'username' NÃO EXISTE!")
            print()
            print("🔧 SOLUÇÃO: Adicionar a coluna 'username' à tabela")
            print("SQL: ALTER TABLE conversations ADD COLUMN username VARCHAR(50);")
        
        # Verificar outras colunas importantes
        important_columns = [
            'user_id', 'title', 'status', 'total_tokens', 
            'total_prompt_tokens', 'total_completion_tokens', 
            'total_cost', 'total_messages', 'conversation_metadata'
        ]
        
        print()
        print("🔍 Verificando colunas importantes:")
        for col_name in important_columns:
            exists = any(col[0] == col_name for col in columns)
            status = "✅" if exists else "❌"
            print(f"  {status} {col_name}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")

if __name__ == "__main__":
    check_table_structure()
