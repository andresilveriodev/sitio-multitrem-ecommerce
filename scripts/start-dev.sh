#!/bin/bash

# Script para iniciar o projeto em modo desenvolvimento
# Inicia PostgreSQL, Redis e todos os serviços

set -e

echo "🌿 Sítio Multitrem - Iniciando Desenvolvimento"
echo "=============================================="
echo ""

# Verificar se PostgreSQL está rodando
echo -n "Verificando PostgreSQL... "
if command -v pg_isready &> /dev/null; then
    if pg_isready -q; then
        echo "✓ Rodando"
    else
        echo "⚠ Não está rodando. Inicie o PostgreSQL antes de continuar."
    fi
else
    echo "⚠ pg_isready não encontrado. Verifique manualmente."
fi

# Verificar se Redis está rodando
echo -n "Verificando Redis... "
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✓ Rodando"
    else
        echo "⚠ Não está rodando. Inicie o Redis antes de continuar."
    fi
else
    echo "⚠ redis-cli não encontrado. Verifique manualmente."
fi

echo ""
echo "🚀 Iniciando serviços..."
echo ""

# Iniciar todos os serviços
npm run dev

