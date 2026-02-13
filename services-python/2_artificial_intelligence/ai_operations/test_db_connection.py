#!/usr/bin/env python3
"""
Teste de conexão com o banco de dados PostgreSQL
"""
import os
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import sys

def test_psycopg2_connection():
    """Testa conexão direta com psycopg2"""
    print("🔍 Testando conexão direta com psycopg2...")
    
    try:
        # Configurações do banco baseadas na imagem do pgAdmin
        conn = psycopg2.connect(
            host="localhost",
            port="5434",
            database="b3_trader",
            user="postgres",
            password="123456"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✅ Conexão psycopg2 bem-sucedida!")
        print(f"📊 Versão PostgreSQL: {version[0]}")
        
        # Listar schemas disponíveis
        cursor.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;")
        schemas = cursor.fetchall()
        print(f"📁 Schemas disponíveis: {[s[0] for s in schemas]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão psycopg2: {e}")
        return False

def test_sqlalchemy_connection():
    """Testa conexão com SQLAlchemy"""
    print("\n🔍 Testando conexão com SQLAlchemy...")
    
    try:
        # URI do banco baseada na configuração
        database_uri = "postgresql://postgres:123456@localhost:5434/b3_trader"
        engine = create_engine(database_uri)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database(), current_user;"))
            row = result.fetchone()
            
            print(f"✅ Conexão SQLAlchemy bem-sucedida!")
            print(f"📊 Database atual: {row[0]}")
            print(f"👤 Usuário atual: {row[1]}")
            
            # Verificar se o schema chatbot existe
            result = connection.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'chatbot');"))
            schema_exists = result.fetchone()[0]
            print(f"📁 Schema 'chatbot' existe: {schema_exists}")
            
            if not schema_exists:
                print("🔧 Criando schema 'chatbot'...")
                connection.execute(text("CREATE SCHEMA IF NOT EXISTS chatbot;"))
                connection.commit()
                print("✅ Schema 'chatbot' criado com sucesso!")
        
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Erro na conexão SQLAlchemy: {e}")
        return False

def test_app_db_connection():
    """Testa conexão usando a configuração da aplicação"""
    print("\n🔍 Testando conexão com configuração da aplicação...")
    
    try:
        # Importar configuração da aplicação
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app.db import engine
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test;"))
            test_result = result.fetchone()[0]
            
            print(f"✅ Conexão da aplicação bem-sucedida!")
            print(f"🧪 Teste: {test_result}")
            
            # Verificar tabelas existentes no schema chatbot
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'chatbot'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"📋 Tabelas no schema 'chatbot': {[t[0] for t in tables]}")
            else:
                print("📋 Nenhuma tabela encontrada no schema 'chatbot'")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão da aplicação: {e}")
        return False

def main():
    """Executa todos os testes de conexão"""
    print("🚀 Iniciando testes de conexão com PostgreSQL")
    print("=" * 50)
    
    results = []
    
    # Teste 1: psycopg2
    results.append(test_psycopg2_connection())
    
    # Teste 2: SQLAlchemy
    results.append(test_sqlalchemy_connection())
    
    # Teste 3: Configuração da aplicação
    results.append(test_app_db_connection())
    
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES:")
    print(f"psycopg2: {'✅ OK' if results[0] else '❌ FALHOU'}")
    print(f"SQLAlchemy: {'✅ OK' if results[1] else '❌ FALHOU'}")
    print(f"App Config: {'✅ OK' if results[2] else '❌ FALHOU'}")
    
    if all(results):
        print("\n🎉 Todos os testes de conexão passaram!")
        return 0
    else:
        print("\n⚠️ Alguns testes falharam. Verifique a configuração do banco.")
        return 1

if __name__ == "__main__":
    exit(main())