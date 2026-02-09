#!/bin/bash

# Script de inicialização do Auth Service
set -e

echo "🚀 Iniciando Auth Service..."

# Aguardar banco de dados estar disponível
echo "⏳ Aguardando banco de dados..."
until python -c "
import psycopg2
try:
    conn = psycopg2.connect('$DATABASE_URI')
    conn.close()
    print('Banco de dados disponível')
except:
    exit(1)
"; do
    echo "Banco de dados ainda não está disponível, aguardando..."
    sleep 2
done

# Inicializar banco de dados
echo "🗄️  Inicializando banco de dados..."
python init_db.py

# Iniciar aplicação
echo "🌟 Iniciando aplicação..."
exec python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

