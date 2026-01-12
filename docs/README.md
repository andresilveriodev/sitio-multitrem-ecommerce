# 🌿 Sítio Multitrem - E-commerce

E-commerce single-page para o Sítio Multitrem (Terezópolis de Goiás) que vende hortaliças frescas e ovos caipiras.

## 📋 Sobre o Projeto

Sistema completo de e-commerce com:
- **Frontend**: Next.js 14 com React e Tailwind CSS
- **Backend**: Microserviços NestJS
- **Banco de Dados**: PostgreSQL
- **Cache**: Redis
- **Autenticação**: Keycloak
- **Pagamentos**: Mercado Pago (Pix, Boleto, Cartão)
- **WhatsApp**: Evolution API
- **IA**: OpenAI GPT-4o-mini (Assistente de Vendas)

## 🚀 Requisitos

- Node.js 18+ e npm 9+
- PostgreSQL 14+
- Redis 6+
- Keycloak (opcional para desenvolvimento)
- Evolution API (opcional para WhatsApp)

## 📦 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/andresilveriodev/sitio-multitrem-ecommerce.git
cd sitio-multitrem-ecommerce
```

### 2. Instale as dependências

```bash
# Instalar dependências do projeto raiz
npm install

# Instalar dependências do shared package
cd shared && npm install && npm run build && cd ..

# Instalar dependências do frontend
cd frontend && npm install && cd ..

# Instalar dependências de cada serviço
cd services/product-service && npm install && cd ../..
cd services/cart-service && npm install && cd ../..
cd services/order-service && npm install && cd ../..
cd services/payment-service && npm install && cd ../..
cd services/auth-service && npm install && cd ../..
cd services/whatsapp-service && npm install && cd ../..
cd services/ai-service && npm install && cd ../..
cd services/gateway && npm install && cd ../..
```

### 3. Configure as variáveis de ambiente

Consulte o arquivo `ENV_VARIABLES.md` para todas as variáveis necessárias.

Copie os arquivos `.env.example` para `.env` em cada serviço:

```bash
# Na raiz do projeto
cp .env.example .env

# Em cada serviço
cp services/product-service/.env.example services/product-service/.env
cp services/cart-service/.env.example services/cart-service/.env
cp services/order-service/.env.example services/order-service/.env
cp services/payment-service/.env.example services/payment-service/.env
cp services/auth-service/.env.example services/auth-service/.env
cp services/whatsapp-service/.env.example services/whatsapp-service/.env
cp services/ai-service/.env.example services/ai-service/.env
cp services/gateway/.env.example services/gateway/.env
```

### 4. Configure o banco de dados

```bash
# Criar banco de dados
createdb sitio_multitrem

# Ou via psql
psql -U postgres -c "CREATE DATABASE sitio_multitrem;"
```

### 5. Inicie PostgreSQL e Redis

```bash
# PostgreSQL (Linux/Mac)
sudo systemctl start postgresql

# Redis (Linux/Mac)
sudo systemctl start redis

# Windows: Use os serviços do Windows ou Docker
```

## 🏃 Executando o Projeto

### Desenvolvimento

Para iniciar todos os serviços de uma vez:

```bash
npm run dev
```

Isso iniciará:
- Frontend (porta 3000)
- Gateway (porta 8000)
- Product Service (porta 3001)
- Cart Service (porta 3002)
- Order Service (porta 3003)
- Payment Service (porta 3004)
- Auth Service (porta 3005)
- WhatsApp Service (porta 3006)
- AI Service (porta 3007)

### Serviços Individuais

```bash
# Frontend
npm run dev:frontend

# Gateway
npm run dev:gateway

# Product Service
npm run dev:product

# Cart Service
npm run dev:cart

# Order Service
npm run dev:order

# Payment Service
npm run dev:payment

# Auth Service
npm run dev:auth

# WhatsApp Service
npm run dev:whatsapp

# AI Service
npm run dev:ai
```

## 📡 Portas dos Serviços

| Serviço | Porta | URL |
|---------|-------|-----|
| Gateway | 8000 | http://localhost:8000 |
| Frontend | 3000 | http://localhost:3000 (em dev) |
| Product Service | 3001 | http://localhost:3001 |
| Cart Service | 3002 | http://localhost:3002 |
| Order Service | 3003 | http://localhost:3003 |
| Payment Service | 3004 | http://localhost:3004 |
| Auth Service | 3005 | http://localhost:3005 |
| WhatsApp Service | 3006 | http://localhost:3006 |
| AI Service | 3007 | http://localhost:3007 |

## 🧪 Testando a API

### Health Checks

```bash
# Gateway
curl http://localhost:8000/health

# Status de todos os serviços
curl http://localhost:8000/health/services
```

### Exemplos de Requisições

```bash
# Listar produtos
curl http://localhost:8000/api/products

# Criar carrinho
curl -X POST http://localhost:8000/api/cart/visitor123/items \
  -H "Content-Type: application/json" \
  -d '{"productId": 1, "quantity": 2}'

# Ver carrinho
curl http://localhost:8000/api/cart/visitor123
```

## 📁 Estrutura do Projeto

```
sitio-multitrem/
├── frontend/              # Next.js 14
├── services/
│   ├── gateway/           # API Gateway
│   ├── product-service/   # Catálogo de produtos
│   ├── cart-service/      # Carrinho de compras
│   ├── order-service/     # Pedidos
│   ├── payment-service/   # Pagamentos (Mercado Pago)
│   ├── auth-service/      # Autenticação (Keycloak)
│   ├── whatsapp-service/ # WhatsApp (Evolution API)
│   └── ai-service/        # Assistente IA (OpenAI)
├── shared/                # Tipos e DTOs compartilhados
├── scripts/               # Scripts de setup
└── docs/                  # Documentação
```

## 🔧 Configuração Adicional

### Keycloak

**⚠️ IMPORTANTE**: Este projeto usa o Keycloak hospedado em `https://auth.rendacontinua.com`

Para configurar a integração completa, consulte o **[Guia de Configuração Keycloak](GUIA_KEYCLOAK_CONFIGURACAO.md)**.

**Resumo rápido:**
1. Crie o arquivo `frontend/.env.local`:
   ```bash
   NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=sitio-multitrem-app
   NEXT_PUBLIC_APP_URL=http://localhost:3000
   ```
2. Configure o Client no Keycloak Admin Console
3. Reinicie o servidor Next.js

**📖 Documentação completa**: [GUIA_KEYCLOAK_CONFIGURACAO.md](GUIA_KEYCLOAK_CONFIGURACAO.md)

### Evolution API (WhatsApp)

**⚠️ IMPORTANTE**: Este projeto usa a Evolution API para integração com WhatsApp Web.

Para configurar a integração completa, consulte o **[Guia de Instalação Evolution API](GUIA_EVOLUTION_API_INSTALACAO.md)**.

**Resumo rápido:**
1. Instale Node.js v20+, PostgreSQL e Redis
2. Clone a Evolution API em `services/evolution-api`
3. Configure o `.env` com credenciais do banco
4. Execute `npm run db:deploy` e `npm run start`
5. Crie uma instância e escaneie o QR Code
6. Configure o WhatsApp Service

**📖 Documentação completa**: [GUIA_EVOLUTION_API_INSTALACAO.md](GUIA_EVOLUTION_API_INSTALACAO.md)

### Mercado Pago

1. Acesse https://www.mercadopago.com.br/developers
2. Crie uma aplicação
3. Copie o Access Token e Public Key

### OpenAI

1. Acesse https://platform.openai.com/api-keys
2. Crie uma nova chave de API
3. Configure no `.env` do ai-service

## 📚 Documentação

- [Variáveis de Ambiente](ENV_VARIABLES.md)
- [Guia de Configuração Keycloak](GUIA_KEYCLOAK_CONFIGURACAO.md) ⭐
- [Guia de Instalação Evolution API](GUIA_EVOLUTION_API_INSTALACAO.md) ⭐ **NOVO**
- [Guia AgentOS (AI Service)](services/ai-service/agno-agent/GUIA_AGENTOS.md)
- [Integração WhatsApp Service](services/whatsapp-service/INTEGRACAO_EVOLUTION.md) ⭐ **NOVO**
- [Guia de Deploy](frontend/DEPLOY.md)

## 🛠️ Scripts Disponíveis

```bash
# Desenvolvimento
npm run dev                 # Inicia todos os serviços
npm run dev:frontend        # Apenas frontend
npm run dev:services        # Apenas serviços backend

# Build
npm run build              # Build de todos os projetos
npm run build:shared       # Build apenas do shared package
```

## 🐛 Troubleshooting

### Porta já em uso

Se a porta 8000 (Gateway) ou 3000 (Frontend) estiver em uso, ajuste as portas nos arquivos `.env`.

### Erro de conexão com banco

Verifique se o PostgreSQL está rodando e se as credenciais no `.env` estão corretas.

### Erro de conexão com Redis

Verifique se o Redis está rodando e se a porta está correta.

## 📝 Licença

Este projeto é privado e pertence ao Sítio Multitrem.

## 👥 Contribuindo

Este é um projeto privado. Para sugestões ou problemas, entre em contato com a equipe de desenvolvimento.

---

**Desenvolvido com ❤️ para o Sítio Multitrem** 🌿
