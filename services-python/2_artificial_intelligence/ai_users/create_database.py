#!/usr/bin/env python3
"""
Script para criar o banco de dados ecommerce_ai
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

# Obter DATABASE_URI do .env
database_uri = os.getenv("DATABASE_URI")

if not database_uri:
    print("ERRO: DATABASE_URI nao encontrada no arquivo .env")
    exit(1)

# Extrair informações da URI
# postgresql://postgres:123456@localhost:5434/ecommerce_ai
uri_parts = database_uri.replace("postgresql://", "").split("@")
if len(uri_parts) != 2:
    print("ERRO: Formato de DATABASE_URI invalido")
    exit(1)

auth_part = uri_parts[0].split(":")
host_part = uri_parts[1].split("/")

username = auth_part[0]
password = auth_part[1] if len(auth_part) > 1 else ""
host_port = host_part[0].split(":")
host = host_port[0]
port = int(host_port[1]) if len(host_port) > 1 else 5432
database_name = host_part[1] if len(host_part) > 1 else "postgres"

print("=" * 60)
print("CRIACAO DO BANCO DE DADOS")
print("=" * 60)
print(f"Host: {host}")
print(f"Port: {port}")
print(f"Username: {username}")
print(f"Database: {database_name}")
print("=" * 60)

try:
    # Conectar ao PostgreSQL (sem especificar database para criar um novo)
    print(f"\nConectando ao PostgreSQL em {host}:{port}...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database="postgres"  # Conectar ao banco padrão
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Verificar se o banco já existe
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
    exists = cursor.fetchone()
    
    if exists:
        print(f"\n[AVISO] O banco de dados '{database_name}' ja existe!")
        print("Nenhuma acao necessaria.")
    else:
        # Criar o banco de dados
        print(f"\nCriando banco de dados '{database_name}'...")
        cursor.execute(f'CREATE DATABASE "{database_name}"')
        print(f"[SUCESSO] Banco de dados '{database_name}' criado com sucesso!")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("PROXIMOS PASSOS:")
    print("=" * 60)
    print("1. O banco de dados foi criado")
    print("2. Reinicie o servico AI Service")
    print("3. O servico criara automaticamente os schemas e tabelas")
    print("=" * 60)
    
except psycopg2.OperationalError as e:
    print(f"\n[ERRO] Nao foi possivel conectar ao PostgreSQL:")
    print(f"   {str(e)}")
    print("\nVerifique se:")
    print("  - PostgreSQL esta rodando")
    print("  - Host e porta estao corretos no .env")
    print("  - Usuario e senha estao corretos")
    exit(1)
except Exception as e:
    print(f"\n[ERRO] Erro inesperado: {str(e)}")
    exit(1)
