# 🔌 Portas do Sistema - Sítio Multitrem

Este documento lista todas as portas que precisam estar abertas/disponíveis para o sistema funcionar.

## 📋 Resumo Rápido

**Total: 11 portas** (9 obrigatórias + 2 opcionais)

---

## 🚀 Portas Obrigatórias

### Frontend
- **Porta 3000** - Next.js (Frontend)
  - Acesso: `http://localhost:3000`
  - Descrição: Interface do usuário

### Gateway
- **Porta 8000** - API Gateway
  - Acesso: `http://localhost:8000`
  - Descrição: Ponto de entrada único para todos os serviços backend
  - Health Check: `http://localhost:8000/health`

### Microserviços Backend

#### Product Service
- **Porta 3001** - Product Service
  - Acesso: `http://localhost:3001`
  - Swagger: `http://localhost:3001/api/docs`
  - Descrição: Gerenciamento de produtos

#### Cart Service
- **Porta 3002** - Cart Service
  - Acesso: `http://localhost:3002`
  - Swagger: `http://localhost:3002/api/docs`
  - Descrição: Gerenciamento de carrinho de compras

#### Order Service
- **Porta 3003** - Order Service
  - Acesso: `http://localhost:3003`
  - Swagger: `http://localhost:3003/api/docs`
  - Descrição: Gerenciamento de pedidos

#### Payment Service
- **Porta 3004** - Payment Service
  - Acesso: `http://localhost:3004`
  - Swagger: `http://localhost:3004/api/docs`
  - Descrição: Processamento de pagamentos

#### Auth Service
- **Porta 3005** - Auth Service
  - Acesso: `http://localhost:3005`
  - Swagger: `http://localhost:3005/api/docs`
  - Descrição: Autenticação e autorização

#### WhatsApp Service
- **Porta 3006** - WhatsApp Service
  - Acesso: `http://localhost:3006`
  - Swagger: `http://localhost:3006/api/docs`
  - Descrição: Integração com WhatsApp via Evolution API

#### AI Service
- **Porta 3007** - AI Service
  - Acesso: `http://localhost:3007`
  - Swagger: `http://localhost:3007/api/docs`
  - Descrição: Assistente de vendas com IA (OpenAI)

### Bancos de Dados

#### PostgreSQL
- **Porta 5432** - PostgreSQL
  - Acesso: `localhost:5432`
  - Descrição: Banco de dados principal (produtos, pedidos, pagamentos)
  - **Obrigatório**: Sim

#### Redis
- **Porta 6379** - Redis
  - Acesso: `localhost:6379`
  - Descrição: Cache e armazenamento de sessões (carrinho, histórico de chat)
  - **Obrigatório**: Sim

---

## 🔐 Portas Opcionais

### Keycloak (Autenticação)
- **Porta 8080** - Keycloak
  - Acesso: `http://localhost:8080`
  - Descrição: Servidor de autenticação (opcional para desenvolvimento)
  - **Obrigatório**: Não (pode usar mock em dev)

### Evolution API (WhatsApp)
- **Porta 8081** - Evolution API
  - Acesso: `http://localhost:8081`
  - Descrição: API para integração com WhatsApp (opcional)
  - **Obrigatório**: Não (pode desabilitar funcionalidade de WhatsApp)

---

## 📊 Tabela Resumo

| Porta | Serviço | Tipo | Obrigatório | Descrição |
|-------|---------|------|-------------|-----------|
| 3000 | Frontend | Aplicação | ✅ Sim | Next.js |
| 8000 | Gateway | Aplicação | ✅ Sim | API Gateway |
| 3001 | Product Service | Aplicação | ✅ Sim | Produtos |
| 3002 | Cart Service | Aplicação | ✅ Sim | Carrinho |
| 3003 | Order Service | Aplicação | ✅ Sim | Pedidos |
| 3004 | Payment Service | Aplicação | ✅ Sim | Pagamentos |
| 3005 | Auth Service | Aplicação | ✅ Sim | Autenticação |
| 3006 | WhatsApp Service | Aplicação | ✅ Sim | WhatsApp |
| 3007 | AI Service | Aplicação | ✅ Sim | IA |
| 5432 | PostgreSQL | Banco | ✅ Sim | Banco de dados |
| 6379 | Redis | Cache | ✅ Sim | Cache/Sessões |
| 8080 | Keycloak | Aplicação | ❌ Não | Autenticação (opcional) |
| 8081 | Evolution API | Aplicação | ❌ Não | WhatsApp (opcional) |

---

## 🔥 Firewall / Portas a Abrir

### Desenvolvimento Local
Todas as portas acima devem estar disponíveis localmente. Normalmente não é necessário configurar firewall em desenvolvimento local.

### Produção / Servidor
Se estiver rodando em um servidor, você precisa abrir as seguintes portas no firewall:

**Portas Públicas (acessíveis externamente):**
- **3000** - Frontend (ou use um proxy reverso como Nginx)
- **8000** - Gateway (ou use um proxy reverso como Nginx)

**Portas Internas (apenas dentro da rede):**
- **3001-3007** - Microserviços (não expor publicamente)
- **5432** - PostgreSQL (apenas localhost ou rede interna)
- **6379** - Redis (apenas localhost ou rede interna)
- **8080** - Keycloak (se usar)
- **8081** - Evolution API (se usar)

---

## ✅ Verificação de Portas

### Windows (PowerShell)
```powershell
# Verificar se uma porta está em uso
netstat -ano | findstr :3000

# Verificar todas as portas do sistema
netstat -ano | findstr "3000 3001 3002 3003 3004 3005 3006 3007 8000 5432 6379"
```

### Linux/Mac
```bash
# Verificar se uma porta está em uso
lsof -i :3000

# Verificar todas as portas do sistema
lsof -i :3000,3001,3002,3003,3004,3005,3006,3007,8000,5432,6379
```

---

## 🚨 Conflitos Comuns

### Porta 3000
- **Conflito**: Frontend Next.js
- **Solução**: O Gateway foi movido para a porta 8000 para evitar conflito

### Porta 5432
- **Conflito**: PostgreSQL
- **Solução**: Verifique se o PostgreSQL está rodando: `pg_isready` ou `psql -U postgres`

### Porta 6379
- **Conflito**: Redis
- **Solução**: Verifique se o Redis está rodando: `redis-cli ping`

---

## 📝 Notas Importantes

1. **Desenvolvimento Local**: Todas as portas devem estar disponíveis em `localhost`
2. **Produção**: Use um proxy reverso (Nginx, Traefik) para expor apenas as portas necessárias
3. **Docker**: Se usar Docker, mapeie as portas corretamente no `docker-compose.yml`
4. **Firewall**: Em produção, configure o firewall para permitir apenas as portas necessárias
5. **Segurança**: Nunca exponha portas de banco de dados (5432, 6379) publicamente

---

## 🔗 URLs de Acesso

### Desenvolvimento Local

- **Frontend**: http://localhost:3000
- **Gateway**: http://localhost:8000
- **Swagger (Product)**: http://localhost:3001/api/docs
- **Swagger (Cart)**: http://localhost:3002/api/docs
- **Swagger (Order)**: http://localhost:3003/api/docs
- **Swagger (Payment)**: http://localhost:3004/api/docs
- **Swagger (Auth)**: http://localhost:3005/api/docs
- **Swagger (WhatsApp)**: http://localhost:3006/api/docs
- **Swagger (AI)**: http://localhost:3007/api/docs

---

**Última atualização**: 2024




