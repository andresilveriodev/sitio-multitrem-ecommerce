#!/usr/bin/env python3
import psycopg2
from psycopg2 import sql

def check_all_tables():
    try:
        # Conectar ao banco
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5434/sitio_multitrem')
        cur = conn.cursor()
        
        print("🔍 Verificando TODAS as tabelas no banco de dados...")
        print("=" * 60)
        
        # Listar todas as tabelas
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        existing_tables = [row[0] for row in cur.fetchall()]
        print("📋 Todas as tabelas existentes:")
        for table in existing_tables:
            print(f"  • {table}")
        
        print("\n" + "=" * 60)
        
        # Verificar estrutura de cada tabela relacionada a preços
        price_related_tables = [
            'ai_models', 'ai_subscriptions', 'user_subscriptions', 
            'user_ai_settings', 'ai_usage_alerts', 'transactions', 'usage'
        ]
        
        for table in price_related_tables:
            if table in existing_tables:
                print(f"\n🔍 Estrutura da tabela '{table}':")
                print("-" * 40)
                
                cur.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    ORDER BY ordinal_position;
                """)
                
                columns = cur.fetchall()
                for col in columns:
                    print(f"  • {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            else:
                print(f"\n❌ Tabela '{table}' NÃO EXISTE!")
        
        # Verificar se há dados nas tabelas de preços
        print("\n" + "=" * 60)
        print("📊 Verificando dados nas tabelas de preços:")
        
        for table in ['ai_models', 'ai_subscriptions', 'user_subscriptions']:
            if table in existing_tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  • {table}: {count} registros")
                
                if count > 0:
                    # Mostrar alguns registros
                    cur.execute(f"SELECT * FROM {table} LIMIT 3")
                    rows = cur.fetchall()
                    print(f"    Exemplos:")
                    for row in rows:
                        print(f"      - {row}")
            else:
                print(f"  • {table}: Tabela não existe")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_all_tables()
