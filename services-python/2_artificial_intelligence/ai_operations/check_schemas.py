#!/usr/bin/env python3
import psycopg2
from psycopg2 import sql

def check_all_schemas():
    try:
        # Conectar ao banco
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5434/sitio_multitrem')
        cur = conn.cursor()
        
        print("🔍 Verificando TODOS os schemas e tabelas...")
        print("=" * 60)
        
        # Listar todos os schemas
        cur.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name;
        """)
        
        schemas = [row[0] for row in cur.fetchall()]
        print("📋 Schemas existentes:")
        for schema in schemas:
            print(f"  • {schema}")
        
        print("\n" + "=" * 60)
        
        # Para cada schema, listar as tabelas
        for schema in schemas:
            print(f"\n🔍 Tabelas no schema '{schema}':")
            print("-" * 40)
            
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY table_name;
            """, (schema,))
            
            tables = [row[0] for row in cur.fetchall()]
            if tables:
                for table in tables:
                    print(f"  • {table}")
            else:
                print("  (nenhuma tabela)")
        
        # Verificar especificamente as tabelas que deveriam existir
        print("\n" + "=" * 60)
        print("🔍 Verificando tabelas específicas:")
        
        expected_tables = [
            'transactions', 'usage', 'ai_models', 'ai_subscriptions', 
            'user_subscriptions', 'user_ai_settings', 'ai_usage_alerts'
        ]
        
        for table in expected_tables:
            cur.execute("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_name = %s
                ORDER BY table_schema;
            """, (table,))
            
            results = cur.fetchall()
            if results:
                for schema, table_name in results:
                    print(f"  ✅ {table_name} existe no schema '{schema}'")
            else:
                print(f"  ❌ {table} NÃO EXISTE em nenhum schema")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar schemas: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_all_schemas()
