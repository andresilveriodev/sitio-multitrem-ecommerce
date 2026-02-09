#!/usr/bin/env python3
import psycopg2
from psycopg2 import sql

def fix_database():
    try:
        # Conectar ao banco
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5434/sitio_multitrem')
        cur = conn.cursor()
        
        print("🔧 Corrigindo estrutura do banco de dados...")
        print("=" * 50)
        
        # Verificar se a coluna username existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'conversations' AND column_name = 'username'
            );
        """)
        username_exists = cur.fetchone()[0]
        
        if username_exists:
            print("✅ Coluna 'username' já existe!")
        else:
            print("❌ Coluna 'username' não existe. Adicionando...")
            
            # Adicionar a coluna username
            cur.execute("""
                ALTER TABLE conversations 
                ADD COLUMN username VARCHAR(50);
            """)
            
            print("✅ Coluna 'username' adicionada com sucesso!")
            
            # Criar índice para melhor performance
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_username 
                ON conversations(username);
            """)
            
            print("✅ Índice criado para a coluna 'username'!")
        
        # Verificar se há dados existentes e atualizar username se necessário
        cur.execute("""
            SELECT COUNT(*) FROM conversations WHERE username IS NULL;
        """)
        null_usernames = cur.fetchone()[0]
        
        if null_usernames > 0:
            print(f"⚠️  Encontrados {null_usernames} registros sem username")
            print("   Atualizando com valores padrão...")
            
            # Atualizar registros existentes com username padrão
            cur.execute("""
                UPDATE conversations 
                SET username = 'user_' || user_id::text 
                WHERE username IS NULL;
            """)
            
            print("✅ Registros atualizados com username padrão!")
        
        # Commit das alterações
        conn.commit()
        print()
        print("🎉 Banco de dados corrigido com sucesso!")
        
        # Verificar estrutura final
        print()
        print("📋 Estrutura final da tabela 'conversations':")
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'conversations' 
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        for col in columns:
            print(f"  • {col[0]}: {col[1]} (nullable: {col[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao corrigir banco: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    fix_database()
