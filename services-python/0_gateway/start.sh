#!/bin/bash

# Script de inicialização do Gateway Service

set -e

echo "🚀 Iniciando Gateway Service..."

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.11+"
    exit 1
fi

# Verificar se pip está instalado
if ! command -v pip &> /dev/null; then
    echo "❌ pip não encontrado. Instale pip"
    exit 1
fi

# Verificar se virtualenv está instalado
if ! command -v virtualenv &> /dev/null; then
    echo "📦 Instalando virtualenv..."
    pip install virtualenv
fi

# Criar virtualenv se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    virtualenv venv
fi

# Ativar virtualenv
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Verificar variáveis de ambiente
if [ ! -f ".env" ]; then
    echo "⚠️  Arquivo .env não encontrado. Criando .env.example..."
    cat > .env.example << EOF
# Gateway Service Configuration

# Debug mode
DEBUG=false

# Server configuration
HOST=0.0.0.0
PORT=8000

# Redis
REDIS_URL=redis://localhost:6379/0

# Microservices URLs
AUTH_SERVICE_URL=http://localhost:8001
USER_SERVICE_URL=http://localhost:8004
IMPORT_SERVICE_URL=http://localhost:8002
CHATBOT_SERVICE_URL=http://localhost:8002
AI_SERVICE_URL=http://localhost:8003

# Keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=ecommerce
KEYCLOAK_CLIENT_ID=ecommerce-gateway
KEYCLOAK_CLIENT_SECRET=your-secret

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Cache
CACHE_TTL=300

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
    echo "📝 Copie .env.example para .env e configure as variáveis"
    exit 1
fi

# Verificar se Redis está rodando
echo "🔍 Verificando conectividade com Redis..."
if ! python -c "import redis; redis.Redis.from_url('redis://localhost:6379/0').ping()" 2>/dev/null; then
    echo "⚠️  Redis não está rodando. Inicie o Redis primeiro:"
    echo "   docker run -d -p 6379:6379 redis:7-alpine"
    echo "   ou"
    echo "   redis-server"
fi

# Executar aplicação
echo "🚀 Iniciando Gateway Service na porta 8000..."
echo "📖 Documentação disponível em: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo "📊 Status: http://localhost:8000/api/v1/status"
echo ""
echo "Pressione Ctrl+C para parar"
echo ""

python main.py
