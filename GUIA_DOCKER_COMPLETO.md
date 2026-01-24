# 🐳 Guia Completo Docker - Sítio Multitrem

Este guia contém todas as instruções e arquivos necessários para containerizar completamente a aplicação Sítio Multitrem com Docker.

## 📋 Índice

1. [Análise da Arquitetura](#análise-da-arquitetura)
2. [Estrutura de Arquivos](#estrutura-de-arquivos)
3. [Passo a Passo da Implementação](#passo-a-passo-da-implementação)
4. [Códigos dos Arquivos](#códigos-dos-arquivos)
5. [Comandos para Execução](#comandos-para-execução)
6. [Troubleshooting](#troubleshooting)

---

## 🏗️ Análise da Arquitetura

### **Componentes da Aplicação:**

#### **Frontend:**
- Next.js (porta 3000)

#### **Backend - Microserviços:**
- Gateway (porta 8000)
- Product Service (porta 3001)
- Cart Service (porta 3002) - usa Redis
- Order Service (porta 3003)
- Payment Service (porta 3004) - usa PostgreSQL
- Auth Service (porta 3005)
- WhatsApp Service (porta 3006)
- AI Service (porta 3007)

#### **AI Agent Python:**
- Agno Agent (porta 3008) - Python com FastAPI

#### **Banco de Dados:**
- PostgreSQL (porta 5432)
- Redis (porta 6379)

#### **Serviços Externos:**
- Evolution API (porta 8081)

---

## 📁 Estrutura de Arquivos

Crie a seguinte estrutura de pastas e arquivos:

```
E-commerce 02/
├── docker/
│   ├── nestjs.Dockerfile
│   ├── shared.Dockerfile
│   └── postgres/
│       └── init.sql
├── frontend/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── .dockerignore
├── services/
│   └── ai-service/
│       └── agno_agente_horta_multitrem/
│           └── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .env
├── .env.example
├── .dockerignore
└── GUIA_DOCKER_COMPLETO.md (este arquivo)
```

---

## 🚀 Passo a Passo da Implementação

### **Passo 1: Preparar o Ambiente**

1. **Certifique-se que o Docker Desktop está rodando**
2. **Abra o PowerShell como Administrador**:
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02"
```

### **Passo 2: Criar Estrutura de Pastas**

```powershell
# Criar pastas necessárias
New-Item -ItemType Directory -Force -Path "docker"
New-Item -ItemType Directory -Force -Path "docker\postgres"
New-Item -ItemType Directory -Force -Path "frontend" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path "services\ai-service\agno_agente_horta_multitrem" -ErrorAction SilentlyContinue
```

### **Passo 3: Criar Arquivos Docker**

Siga os códigos na seção [Códigos dos Arquivos](#códigos-dos-arquivos) abaixo.

### **Passo 4: Configurar Variáveis de Ambiente**

1. **Copie `.env.example` para `.env`**
2. **Edite o `.env`** com suas chaves reais

### **Passo 5: Primeira Execução**

1. **Construir tudo:**
```powershell
docker-compose build
```

2. **Subir bancos de dados primeiro:**
```powershell
docker-compose up -d postgres redis evolution-postgres evolution-redis
```

3. **Aguardar 2-3 minutos para os bancos ficarem prontos**

4. **Subir todos os serviços:**
```powershell
docker-compose up -d
```

### **Passo 6: Verificar Funcionamento**

```powershell
# Ver status dos containers
docker ps

# Ver logs
docker-compose logs -f

# Testar endpoints
curl http://localhost:3000  # Frontend
curl http://localhost:8000/health  # Gateway
```

---

## 📄 Códigos dos Arquivos

### 1. **docker-compose.yml** (Principal)

```yaml
version: '3.8'

services:
  # ================================
  # BANCOS DE DADOS
  # ================================
  postgres:
    image: postgres:15-alpine
    container_name: sitio_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: sitio_multitrem
      POSTGRES_USER: sitio_user
      POSTGRES_PASSWORD: sitio_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sitio_user -d sitio_multitrem"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: sitio_redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass sitio_redis_pass
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "sitio_redis_pass", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ================================
  # SHARED PACKAGE
  # ================================
  shared:
    build:
      context: .
      dockerfile: docker/shared.Dockerfile
    container_name: sitio_shared
    volumes:
      - shared_dist:/app/shared/dist

  # ================================
  # MICROSERVIÇOS BACKEND
  # ================================
  product-service:
    build:
      context: .
      dockerfile: docker/nestjs.Dockerfile
      args:
        SERVICE_PATH: services/product-service
        SERVICE_PORT: 3001
    container_name: sitio_product_service
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      shared:
        condition: service_completed_successfully
    environment:
      NODE_ENV: production
      PORT: 3001
      DATABASE_URL: postgresql://sitio_user:sitio_password@postgres:5432/sitio_multitrem
    volumes:
      - shared_dist:/app/node_modules/@sitio/shared/dist
    ports:
      - "3001:3001"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  cart-service:
    build:
      context: .
      dockerfile: docker/nestjs.Dockerfile
      args:
        SERVICE_PATH: services/cart-service
        SERVICE_PORT: 3002
    container_name: sitio_cart_service
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
      shared:
        condition: service_completed_successfully
    environment:
      NODE_ENV: production
      PORT: 3002
      REDIS_URL: redis://:sitio_redis_pass@redis:6379
    volumes:
      - shared_dist:/app/node_modules/@sitio/shared/dist
    ports:
      - "3002:3002"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  order-service:
    build:
      context: .
      dockerfile: docker/nestjs.Dockerfile
      args:
        SERVICE_PATH: services/order-service
        SERVICE_PORT: 3003
    container_name: sitio_order_service
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      shared:
        condition: service_completed_successfully
    environment:
      NODE_ENV: production
      PORT: 3003
      DATABASE_URL: postgresql://sitio_user:sitio_password@postgres:5432/sitio_multitrem
    volumes:
      - shared_dist:/app/node_modules/@sitio/shared/dist
    ports:
      - "3003:3003"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3003/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  payment-service:
    build:
      context: .
      dockerfile: docker/nestjs.Dockerfile
      args:
        SERVICE_PATH: services/payment-service
        SERVICE_PORT: 3004
    container_name: sitio_payment_service
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      shared:
        condition: service_completed_successfully
    environment:
      NODE_ENV: production
      PORT: 3004
      DATABASE_URL: postgresql://sitio_user:sitio_password@postgres:5432/sitio_multitrem
      MERCADOPAGO_ACCESS_TOKEN: ${MERCADOPAGO_ACCESS_TOKEN}
    volumes:
      - shared_dist:/app/node_modules/@sitio/shared/dist
    ports:
      - "3004:3004"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3004/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  auth-service:
    build:
      context: .
      dockerfile: docker/nestjs.Dockerfile
      args:
        SERVICE_PATH: services/auth-service
        SERVICE_PORT: 3005
    container_name: sitio_auth_service
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      shared:
        condition: service_completed_successfully
    environment:
      NODE_ENV: production
      PORT: 3005
      DATABASE_URL: postgresql://sitio_user:sitio_password@postgres:5432/sitio_multitrem
      JWT_SECRET: ${JWT_SECRET}
      KEYCLOAK_URL: ${KEYCLOAK_URL:-http://localhost:8080}
    volumes:
      - shared_dist:/app/node_modules/@sitio/shared/dist
    ports:
      - "3005:3005"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3005/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  whatsapp-service:
    build:
      context: .
      dockerfile: docker/nestjs.Dockerfile
      args:
        SERVICE_PATH: services/whatsapp-service
        SERVICE_PORT: 3006
    container_name: sitio_whatsapp_service
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
      shared:
        condition: service_completed_successfully
    environment:
      NODE_ENV: production
      PORT: 3006
      REDIS_URL: redis://:sitio_redis_pass@redis:6379
      EVOLUTION_API_URL: http://evolution-api:8080
      EVOLUTION_API_TOKEN: ${EVOLUTION_API_TOKEN}
    volumes:
      - shared_dist:/app/node_modules/@sitio/shared/dist
    ports:
      - "3006:3006"
    networks:
      - sitio-network
      - evolution-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3006/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ai-service:
    build:
      context: .
      dockerfile: docker/nestjs.Dockerfile
      args:
        SERVICE_PATH: services/ai-service
        SERVICE_PORT: 3007
    container_name: sitio_ai_service
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
      shared:
        condition: service_completed_successfully
    environment:
      NODE_ENV: production
      PORT: 3007
      REDIS_URL: redis://:sitio_redis_pass@redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - shared_dist:/app/node_modules/@sitio/shared/dist
    ports:
      - "3007:3007"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3007/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ================================
  # AI AGENT PYTHON
  # ================================
  ai-agent-python:
    build:
      context: services/ai-service/agno_agente_horta_multitrem
      dockerfile: Dockerfile
    container_name: sitio_ai_agent_python
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      DATABASE_URL: postgresql://sitio_user:sitio_password@postgres:5432/sitio_multitrem
    ports:
      - "3008:8000"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ================================
  # GATEWAY
  # ================================
  gateway:
    build:
      context: .
      dockerfile: docker/nestjs.Dockerfile
      args:
        SERVICE_PATH: services/gateway
        SERVICE_PORT: 8000
    container_name: sitio_gateway
    restart: unless-stopped
    depends_on:
      product-service:
        condition: service_healthy
      cart-service:
        condition: service_healthy
      order-service:
        condition: service_healthy
      payment-service:
        condition: service_healthy
      auth-service:
        condition: service_healthy
      whatsapp-service:
        condition: service_healthy
      ai-service:
        condition: service_healthy
    environment:
      NODE_ENV: production
      PORT: 8000
      PRODUCT_SERVICE_URL: http://product-service:3001
      CART_SERVICE_URL: http://cart-service:3002
      ORDER_SERVICE_URL: http://order-service:3003
      PAYMENT_SERVICE_URL: http://payment-service:3004
      AUTH_SERVICE_URL: http://auth-service:3005
      WHATSAPP_SERVICE_URL: http://whatsapp-service:3006
      AI_SERVICE_URL: http://ai-service:3007
    ports:
      - "8000:8000"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ================================
  # FRONTEND
  # ================================
  frontend:
    build:
      context: frontend
      dockerfile: Dockerfile
    container_name: sitio_frontend
    restart: unless-stopped
    depends_on:
      gateway:
        condition: service_healthy
    environment:
      NODE_ENV: production
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_WS_URL: ws://localhost:8000
    ports:
      - "3000:3000"
    networks:
      - sitio-network
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ================================
  # EVOLUTION API (Já configurado)
  # ================================
  evolution-api:
    image: evoapicloud/evolution-api:latest
    container_name: evolution_api
    restart: unless-stopped
    depends_on:
      evolution-redis:
        condition: service_healthy
      evolution-postgres:
        condition: service_healthy
    ports:
      - "8081:8080"
    volumes:
      - evolution_instances:/evolution/instances
    networks:
      - evolution-net
    environment:
      - CACHE_REDIS_ENABLED=true
      - CACHE_REDIS_URI=redis://evolution-redis:6379/6
      - DATABASE_CONNECTION_URI=postgresql://evolution:evolution123@evolution-postgres:5432/evolution
      - DATABASE_PROVIDER=postgresql
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/manager"]
      interval: 30s
      timeout: 10s
      retries: 3

  evolution-redis:
    image: redis:7-alpine
    container_name: evolution_redis
    restart: unless-stopped
    command: redis-server --port 6379 --appendonly yes
    volumes:
      - evolution_redis:/data
    networks:
      - evolution-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  evolution-postgres:
    image: postgres:15-alpine
    container_name: evolution_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: evolution
      POSTGRES_USER: evolution
      POSTGRES_PASSWORD: evolution123
    volumes:
      - evolution_postgres_data:/var/lib/postgresql/data
    networks:
      - evolution-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U evolution -d evolution"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  shared_dist:
  evolution_instances:
  evolution_redis:
  evolution_postgres_data:

networks:
  sitio-network:
    driver: bridge
  evolution-net:
    driver: bridge
```

### 2. **docker/nestjs.Dockerfile**

```dockerfile
FROM node:22-alpine AS builder

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy and build shared package
COPY shared/ ./shared/
WORKDIR /app/shared
RUN npm ci && npm run build

# Copy service files
WORKDIR /app/service
ARG SERVICE_PATH
ARG SERVICE_PORT=3001
COPY ${SERVICE_PATH}/package*.json ./
COPY ${SERVICE_PATH}/tsconfig.json ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY ${SERVICE_PATH}/src ./src

# Build the service
RUN npm run build

# Production stage
FROM node:22-alpine AS runner

WORKDIR /app

RUN addgroup --system --gid 1001 nestjs
RUN adduser --system --uid 1001 nestjs

# Install curl for health checks
RUN apk add --no-cache curl

COPY --from=builder /app/service/dist ./dist
COPY --from=builder /app/service/node_modules ./node_modules
COPY --from=builder /app/service/package*.json ./

USER nestjs

ARG SERVICE_PORT=3001
EXPOSE ${SERVICE_PORT}

CMD ["node", "dist/main.js"]
```

### 3. **docker/shared.Dockerfile**

```dockerfile
FROM node:22-alpine

WORKDIR /app/shared

COPY shared/package*.json ./
COPY shared/tsconfig.json ./

RUN npm ci --silent

COPY shared/src ./src

RUN npm run build

VOLUME ["/app/shared/dist"]
```

### 4. **frontend/Dockerfile**

```dockerfile
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies for Next.js build
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./
COPY next.config.ts ./
COPY postcss.config.mjs ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY src ./src
COPY public ./public

# Build the application
RUN npm run build

# Production stage
FROM node:22-alpine AS runner

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Install wget for health checks
RUN apk add --no-cache wget

# Copy built application
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Copy standalone build
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

### 5. **frontend/Dockerfile.dev** (Para desenvolvimento)

```dockerfile
FROM node:22-alpine

WORKDIR /app

# Install dependencies
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

### 6. **services/ai-service/agno_agente_horta_multitrem/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "uvicorn", "horta_organica_agent:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7. **docker/postgres/init.sql**

```sql
-- Criar bancos de dados
CREATE DATABASE IF NOT EXISTS sitio_multitrem;
CREATE DATABASE IF NOT EXISTS evolution;

-- Criar usuários
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sitio_user') THEN
      CREATE USER sitio_user WITH PASSWORD 'sitio_password';
   END IF;
   
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'evolution') THEN
      CREATE USER evolution WITH PASSWORD 'evolution123';
   END IF;
END
$$;

-- Conceder permissões
GRANT ALL PRIVILEGES ON DATABASE sitio_multitrem TO sitio_user;
GRANT ALL PRIVILEGES ON DATABASE evolution TO evolution;

-- Extensões úteis
\c sitio_multitrem;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c evolution;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 8. **.env.example**

```env
# ================================
# CONFIGURAÇÕES DE BANCO DE DADOS
# ================================
DATABASE_URL=postgresql://sitio_user:sitio_password@localhost:5432/sitio_multitrem
POSTGRES_USER=sitio_user
POSTGRES_PASSWORD=sitio_password
POSTGRES_DATABASE=sitio_multitrem

# ================================
# CONFIGURAÇÕES REDIS
# ================================
REDIS_URL=redis://:sitio_redis_pass@localhost:6379
REDIS_PASSWORD=sitio_redis_pass

# ================================
# CONFIGURAÇÕES JWT
# ================================
JWT_SECRET=meu_jwt_secret_super_seguro_de_256_bits_no_minimo

# ================================
# MERCADO PAGO
# ================================
MERCADOPAGO_ACCESS_TOKEN=seu_token_do_mercado_pago_aqui

# ================================
# OPENAI
# ================================
OPENAI_API_KEY=sua_chave_da_openai_aqui

# ================================
# EVOLUTION API
# ================================
EVOLUTION_API_TOKEN=seu_token_da_evolution_api
EVOLUTION_API_URL=http://localhost:8081

# ================================
# KEYCLOAK (OPCIONAL)
# ================================
KEYCLOAK_URL=http://localhost:8080

# ================================
# CONFIGURAÇÕES DE REDE
# ================================
FRONTEND_URL=http://localhost:3000
GATEWAY_URL=http://localhost:8000

# ================================
# CONFIGURAÇÕES DE AMBIENTE
# ================================
NODE_ENV=production
LOG_LEVEL=info
```

### 9. **.dockerignore** (Raiz)

```dockerignore
# Node
node_modules
npm-debug.log
.npm

# Logs
*.log
logs

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Directory for instrumented libs generated by jscoverage/JSCover
lib-cov

# Coverage directory used by tools like istanbul
coverage
*.lcov

# nyc test coverage
.nyc_output

# Dependency directories
node_modules/
jspm_packages/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env
.env.test
.env.local
.env.development.local
.env.test.local
.env.production.local

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# next.js build output
.next
out

# nuxt.js build output
.nuxt

# vuepress build output
.vuepress/dist

# Serverless directories
.serverless

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port

# Stores VSCode versions used for testing VSCode extensions
.vscode-test

# IDEs
.vscode/
.idea/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Git
.git
.gitignore
.gitmodules

# Documentation
README.md
*.md
docs/

# Build outputs
dist/
build/
```

### 10. **frontend/.dockerignore**

```dockerignore
node_modules
npm-debug.log
.git
.gitignore
README.md
.env.local
.env.development.local
.env.test.local
.env.production.local
.next
.DS_Store
*.log
dist
build
coverage
.nyc_output
```

### 11. **docker-compose.dev.yml** (Desenvolvimento)

```yaml
version: '3.8'

services:
  # Sobrescrever para desenvolvimento
  frontend:
    build:
      context: frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend/src:/app/src:cached
      - ./frontend/public:/app/public:cached
      - ./frontend/package.json:/app/package.json:ro
    environment:
      NODE_ENV: development
      NEXT_PUBLIC_API_URL: http://localhost:8000
    command: npm run dev

  # Bancos expostos para acesso local
  postgres:
    ports:
      - "5432:5432"
    
  redis:
    ports:
      - "6379:6379"

  # Services com hot reload
  product-service:
    volumes:
      - ./services/product-service/src:/app/src:cached
    environment:
      NODE_ENV: development
    command: npm run start:dev

  cart-service:
    volumes:
      - ./services/cart-service/src:/app/src:cached
    environment:
      NODE_ENV: development
    command: npm run start:dev

  order-service:
    volumes:
      - ./services/order-service/src:/app/src:cached
    environment:
      NODE_ENV: development
    command: npm run start:dev

  payment-service:
    volumes:
      - ./services/payment-service/src:/app/src:cached
    environment:
      NODE_ENV: development
    command: npm run start:dev

  auth-service:
    volumes:
      - ./services/auth-service/src:/app/src:cached
    environment:
      NODE_ENV: development
    command: npm run start:dev

  whatsapp-service:
    volumes:
      - ./services/whatsapp-service/src:/app/src:cached
    environment:
      NODE_ENV: development
    command: npm run start:dev

  ai-service:
    volumes:
      - ./services/ai-service/src:/app/src:cached
    environment:
      NODE_ENV: development
    command: npm run start:dev

  gateway:
    volumes:
      - ./services/gateway/src:/app/src:cached
    environment:
      NODE_ENV: development
    command: npm run start:dev

  # AI Agent Python com hot reload
  ai-agent-python:
    volumes:
      - ./services/ai-service/agno_agente_horta_multitrem:/app:cached
    environment:
      PYTHONPATH: /app
      ENVIRONMENT: development
    command: uv run uvicorn horta_organica_agent:app --host 0.0.0.0 --port 8000 --reload
```

### 12. **docker-compose.prod.yml** (Produção)

```yaml
version: '3.8'

services:
  # Configurações específicas para produção
  frontend:
    environment:
      NODE_ENV: production
      NEXT_PUBLIC_API_URL: https://api.sitiomultitrem.com
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  gateway:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  # Services com recursos limitados
  product-service:
    deploy:
      resources:
        limits:
          cpus: '0.3'
          memory: 256M

  cart-service:
    deploy:
      resources:
        limits:
          cpus: '0.3'
          memory: 256M

  # Bancos não expostos publicamente
  postgres:
    ports: []
    
  redis:
    ports: []

  # Nginx como proxy reverso
  nginx:
    image: nginx:alpine
    container_name: sitio_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/ssl:/etc/ssl/certs:ro
    depends_on:
      - frontend
      - gateway
    networks:
      - sitio-network
```

---

## 🔧 Comandos para Execução

### **Comandos Básicos**

```powershell
# 1. Construir todas as imagens
docker-compose build

# 2. Subir apenas bancos de dados
docker-compose up -d postgres redis evolution-postgres evolution-redis

# 3. Aguardar bancos ficarem prontos (2-3 minutos)
Start-Sleep -Seconds 180

# 4. Subir todos os serviços
docker-compose up -d

# 5. Ver status de todos os containers
docker ps

# 6. Ver logs de todos os serviços
docker-compose logs -f

# 7. Ver logs de um serviço específico
docker-compose logs -f frontend

# 8. Parar todos os serviços
docker-compose down

# 9. Parar e remover volumes (CUIDADO - apaga dados!)
docker-compose down -v
```

### **Desenvolvimento**

```powershell
# Subir em modo desenvolvimento com hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Rebuild um serviço específico
docker-compose build frontend

# Executar comando dentro de um container
docker-compose exec frontend sh
docker-compose exec postgres psql -U sitio_user -d sitio_multitrem
```

### **Produção**

```powershell
# Subir em modo produção
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Deploy com rolling update
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale frontend=3
```

### **Manutenção**

```powershell
# Ver uso de espaço
docker system df

# Limpar imagens não utilizadas
docker image prune

# Limpar containers parados
docker container prune

# Limpar volumes não utilizados (CUIDADO!)
docker volume prune

# Backup do banco de dados
docker-compose exec postgres pg_dump -U sitio_user sitio_multitrem > backup.sql

# Restaurar backup
docker-compose exec -T postgres psql -U sitio_user sitio_multitrem < backup.sql
```

---

## 🏥 Health Checks e Monitoramento

### **URLs de Health Check**

```
Frontend:     http://localhost:3000
Gateway:      http://localhost:8000/health
Product:      http://localhost:3001/health
Cart:         http://localhost:3002/health
Order:        http://localhost:3003/health
Payment:      http://localhost:3004/health
Auth:         http://localhost:3005/health
WhatsApp:     http://localhost:3006/health
AI Service:   http://localhost:3007/health
AI Python:    http://localhost:3008/health
Evolution:    http://localhost:8081/manager
```

### **Script de Verificação**

```powershell
# Salve como check-health.ps1
$services = @(
    @{Name="Frontend"; URL="http://localhost:3000"},
    @{Name="Gateway"; URL="http://localhost:8000/health"},
    @{Name="Product"; URL="http://localhost:3001/health"},
    @{Name="Cart"; URL="http://localhost:3002/health"},
    @{Name="Order"; URL="http://localhost:3003/health"},
    @{Name="Payment"; URL="http://localhost:3004/health"},
    @{Name="Auth"; URL="http://localhost:3005/health"},
    @{Name="WhatsApp"; URL="http://localhost:3006/health"},
    @{Name="AI Service"; URL="http://localhost:3007/health"},
    @{Name="AI Python"; URL="http://localhost:3008/health"},
    @{Name="Evolution"; URL="http://localhost:8081/manager"}
)

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.URL -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.Name): OK" -ForegroundColor Green
        } else {
            Write-Host "❌ $($service.Name): $($response.StatusCode)" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ $($service.Name): ERRO - $($_.Exception.Message)" -ForegroundColor Red
    }
}
```

---

## 🔥 Troubleshooting

### **Problemas Comuns**

#### **1. Container não inicia**

```powershell
# Ver logs detalhados
docker-compose logs [nome-do-serviço]

# Verificar se a porta está ocupada
netstat -ano | findstr :3000

# Matar processo na porta
taskkill /PID [PID] /F
```

#### **2. Banco de dados não conecta**

```powershell
# Verificar se PostgreSQL está rodando
docker-compose exec postgres pg_isready -U sitio_user

# Conectar diretamente ao banco
docker-compose exec postgres psql -U sitio_user -d sitio_multitrem

# Verificar logs do PostgreSQL
docker-compose logs postgres
```

#### **3. Redis não conecta**

```powershell
# Testar conexão Redis
docker-compose exec redis redis-cli -a sitio_redis_pass ping

# Ver logs do Redis
docker-compose logs redis
```

#### **4. Shared package não funciona**

```powershell
# Rebuild do shared package
docker-compose build shared

# Verificar se o volume foi criado
docker volume ls | findstr shared
```

#### **5. Health checks falhando**

```powershell
# Verificar se curl está instalado no container
docker-compose exec frontend which curl

# Testar health check manualmente
docker-compose exec frontend curl -f http://localhost:3000/health
```

### **Comandos de Debug**

```powershell
# Entrar no container para debug
docker-compose exec frontend sh

# Ver variáveis de ambiente
docker-compose exec frontend env

# Ver processos rodando
docker-compose exec frontend ps aux

# Ver arquivos do container
docker-compose exec frontend ls -la /app
```

### **Reset Completo**

```powershell
# Parar tudo
docker-compose down

# Remover volumes (perde dados!)
docker-compose down -v

# Limpar imagens
docker image prune -a

# Rebuild tudo do zero
docker-compose build --no-cache

# Subir novamente
docker-compose up -d
```

---

## 📝 Checklist de Implementação

### **Antes de Começar:**
- [ ] Docker Desktop instalado e rodando
- [ ] PowerShell com permissões de administrador
- [ ] Arquivo `.env` configurado com suas chaves
- [ ] Estrutura de pastas criada

### **Arquivos Criados:**
- [ ] `docker-compose.yml`
- [ ] `docker-compose.dev.yml`
- [ ] `docker-compose.prod.yml`
- [ ] `docker/nestjs.Dockerfile`
- [ ] `docker/shared.Dockerfile`
- [ ] `docker/postgres/init.sql`
- [ ] `frontend/Dockerfile`
- [ ] `frontend/Dockerfile.dev`
- [ ] `services/ai-service/agno_agente_horta_multitrem/Dockerfile`
- [ ] `.env` (baseado no `.env.example`)
- [ ] `.dockerignore` (raiz)
- [ ] `frontend/.dockerignore`

### **Primeira Execução:**
- [ ] `docker-compose build` executado com sucesso
- [ ] Bancos de dados subiram primeiro
- [ ] Todos os serviços iniciaram
- [ ] Health checks passando
- [ ] Frontend acessível em http://localhost:3000
- [ ] Gateway acessível em http://localhost:8000

### **Testes:**
- [ ] Todos os endpoints de health respondem OK
- [ ] Frontend carrega corretamente
- [ ] API Gateway roteia corretamente
- [ ] Banco de dados aceita conexões
- [ ] Redis aceita conexões
- [ ] Evolution API funciona

---

## 🎯 Próximos Passos

1. **Configure as chaves no `.env`**
2. **Execute passo a passo conforme o guia**
3. **Teste todos os endpoints**
4. **Configure CI/CD se necessário**
5. **Documente personalizations específicas**

---

**Última atualização**: Janeiro 2026

Este guia fornece uma base sólida para containerizar completamente sua aplicação. Ajuste conforme necessário para suas especificidades!