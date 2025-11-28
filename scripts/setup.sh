#!/bin/bash

# Script de setup do projeto Sítio Multitrem
# Verifica dependências e configura o ambiente

set -e

echo "🌿 Sítio Multitrem - Setup"
echo "=========================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Node.js
echo -n "Verificando Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✓${NC} $NODE_VERSION"
else
    echo -e "${RED}✗${NC} Node.js não encontrado. Instale Node.js 18+"
    exit 1
fi

# Verificar npm
echo -n "Verificando npm... "
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm -v)
    echo -e "${GREEN}✓${NC} $NPM_VERSION"
else
    echo -e "${RED}✗${NC} npm não encontrado"
    exit 1
fi

# Verificar PostgreSQL
echo -n "Verificando PostgreSQL... "
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL encontrado"
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL não encontrado. Você precisará instalá-lo."
fi

# Verificar Redis
echo -n "Verificando Redis... "
if command -v redis-cli &> /dev/null; then
    echo -e "${GREEN}✓${NC} Redis encontrado"
else
    echo -e "${YELLOW}⚠${NC} Redis não encontrado. Você precisará instalá-lo."
fi

echo ""
echo "📦 Instalando dependências..."
npm install

echo ""
echo "🔨 Construindo shared package..."
npm run build:shared

echo ""
echo "📋 Copiando arquivos .env.example..."
# Copiar .env.example para .env em cada serviço (se não existir)
for dir in services/*/; do
    if [ -f "${dir}.env.example" ] && [ ! -f "${dir}.env" ]; then
        cp "${dir}.env.example" "${dir}.env"
        echo "  ✓ Criado ${dir}.env"
    fi
done

# Copiar .env.example do frontend (se existir)
if [ -f "frontend/.env.example" ] && [ ! -f "frontend/.env" ]; then
    cp "frontend/.env.example" "frontend/.env"
    echo "  ✓ Criado frontend/.env"
fi

echo ""
echo -e "${GREEN}✓${NC} Setup concluído!"
echo ""
echo "Próximos passos:"
echo "1. Configure as variáveis de ambiente nos arquivos .env"
echo "2. Inicie PostgreSQL e Redis"
echo "3. Execute: npm run dev"
echo ""

