#!/usr/bin/env python3
import psycopg2
from psycopg2 import sql

def check_and_create_tables():
    try:
        # Conectar ao banco
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5434/b3_trader')
        cur = conn.cursor()
        
        print("🔍 Verificando tabelas no banco de dados...")
        print("=" * 50)
        
        # Listar todas as tabelas
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        existing_tables = [row[0] for row in cur.fetchall()]
        print("📋 Tabelas existentes:")
        for table in existing_tables:
            print(f"  • {table}")
        
        print()
        
        # Tabelas que deveriam existir
        required_tables = [
            'conversations',
            'messages', 
            'transactions',
            'usage',
            'usage_summary',
            'ai_models',
            'ai_subscriptions',
            'user_subscriptions',
            'user_ai_settings',
            'ai_usage_alerts'
        ]
        
        missing_tables = []
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
                print(f"❌ Tabela '{table}' NÃO EXISTE!")
            else:
                print(f"✅ Tabela '{table}' existe!")
        
        if missing_tables:
            print(f"\n🔧 Criando {len(missing_tables)} tabelas faltantes...")
            
            # Criar tabela transactions
            if 'transactions' in missing_tables:
                print("📝 Criando tabela 'transactions'...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id SERIAL PRIMARY KEY,
                        transaction_id VARCHAR(100) UNIQUE NOT NULL,
                        conversation_id INTEGER,
                        user_id INTEGER,
                        username VARCHAR(50),
                        provider VARCHAR(50) NOT NULL,
                        model VARCHAR(100) NOT NULL,
                        endpoint VARCHAR(100) NOT NULL,
                        request_data JSONB NOT NULL,
                        response_data JSONB,
                        prompt_tokens INTEGER DEFAULT 0,
                        completion_tokens INTEGER DEFAULT 0,
                        total_tokens INTEGER DEFAULT 0,
                        prompt_cost DECIMAL(10,6) DEFAULT 0.0,
                        completion_cost DECIMAL(10,6) DEFAULT 0.0,
                        total_cost DECIMAL(10,6) DEFAULT 0.0,
                        response_time_ms INTEGER,
                        is_streaming BOOLEAN DEFAULT FALSE,
                        chunks_count INTEGER DEFAULT 0,
                        status VARCHAR(20) DEFAULT 'pending',
                        error_message TEXT,
                        ip_address VARCHAR(45),
                        user_agent VARCHAR(500),
                        session_id VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("✅ Tabela 'transactions' criada!")
            
            # Criar tabela messages
            if 'messages' in missing_tables:
                print("📝 Criando tabela 'messages'...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        conversation_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        message_metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("✅ Tabela 'messages' criada!")
            
            # Criar tabela usage
            if 'usage' in missing_tables:
                print("📝 Criando tabela 'usage'...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS usage (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        provider VARCHAR(50) NOT NULL,
                        model VARCHAR(100) NOT NULL,
                        date DATE NOT NULL,
                        total_requests INTEGER DEFAULT 0,
                        total_tokens INTEGER DEFAULT 0,
                        total_cost DECIMAL(10,6) DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("✅ Tabela 'usage' criada!")
            
            # Commit das alterações
            conn.commit()
            print("\n🎉 Todas as tabelas foram criadas com sucesso!")
        
        else:
            print("\n🎉 Todas as tabelas necessárias já existem!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar/criar tabelas: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    check_and_create_tables()
