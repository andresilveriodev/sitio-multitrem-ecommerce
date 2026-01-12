# 📱 Guia de Instalação - Evolution API

> **Instalação e configuração completa da Evolution API para integração com WhatsApp Web**

## 📖 Índice

1. [⚡ Quick Start](#⚡-quick-start-tldr)
2. [📋 Pré-requisitos](#📋-pré-requisitos)
3. [🔧 Instalação da Evolution API](#🔧-instalação-da-evolution-api)
4. [⚙️ Configuração](#⚙️-configuração)
5. [🚀 Executando a Evolution API](#🚀-executando-a-evolution-api)
6. [📱 Conectando ao WhatsApp Web](#📱-conectando-ao-whatsapp-web)
7. [🔗 Integração com WhatsApp Service](#🔗-integração-com-whatsapp-service)
8. [🧪 Testando a Integração](#🧪-testando-a-integração)
9. [🔍 Troubleshooting](#🔍-troubleshooting)
10. [❓ FAQ](#❓-faq)

---

## ⚡ Quick Start (TL;DR)

**Se você só quer fazer funcionar rápido:**

```bash
# 1. Instalar Node.js v20+
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install v20.10.0 && nvm use v20.10.0

# 2. Clonar Evolution API
git clone https://github.com/EvolutionAPI/evolution-api.git
cd evolution-api

# 3. Instalar dependências
npm install

# 4. Configurar .env
cp .env.example .env
# Edite o .env com suas credenciais PostgreSQL e Redis

# 5. Setup banco de dados
npm run db:generate
npm run db:deploy

# 6. Build e executar
npm run build
npm run start

# 7. Acessar: http://localhost:8080
```

---

## 📋 Pré-requisitos

### ✅ Software Necessário

#### 1. **Node.js v20+**
```bash
# Instalar NVM (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Recarregar terminal
source ~/.bashrc  # Linux/Mac
# ou
source ~/.zshrc   # Mac com Zsh

# Instalar Node.js v20
nvm install v20.10.0
nvm use v20.10.0
nvm alias default v20.10.0

# Verificar instalação
node --version  # Deve mostrar v20.10.0
npm --version
```

**Windows:**
```powershell
# Baixe e instale o NVM para Windows
# https://github.com/coreybutler/nvm-windows/releases

# Após instalar, abra PowerShell como Admin:
nvm install 20.10.0
nvm use 20.10.0

# Verificar
node --version
```

#### 2. **PostgreSQL 14+**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Iniciar PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Criar banco de dados
sudo -u postgres psql
CREATE DATABASE evolution_api;
CREATE USER evolution WITH PASSWORD 'sua_senha_segura';
GRANT ALL PRIVILEGES ON DATABASE evolution_api TO evolution;
\q
```

**Windows:**
- Baixe o instalador: https://www.postgresql.org/download/windows/
- Instale e configure a senha do postgres
- Use pgAdmin para criar o banco `evolution_api`

#### 3. **Redis**
```bash
# Ubuntu/Debian
sudo apt install redis-server

# Iniciar Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Testar
redis-cli ping  # Deve retornar PONG
```

**Windows:**
- Baixe o Redis para Windows: https://github.com/microsoftarchive/redis/releases
- Ou use WSL2 com Ubuntu

#### 4. **Git**
```bash
# Linux
sudo apt install git

# Windows: baixe de https://git-scm.com/download/win
```

---

## 🔧 Instalação da Evolution API

### 1️⃣ Clonar o Repositório

```bash
# Navegar para o diretório de serviços
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services"

# Clonar Evolution API
git clone https://github.com/EvolutionAPI/evolution-api.git
cd evolution-api
```

### 2️⃣ Instalar Dependências

```bash
npm install
```

**⏱️ Tempo estimado**: 2-5 minutos

---

## ⚙️ Configuração

### 1️⃣ Criar arquivo `.env`

```bash
cp .env.example .env
```

### 2️⃣ Editar `.env` com suas configurações

```bash
# ==================================================
# EVOLUTION API - CONFIGURAÇÃO
# ==================================================

# Servidor
SERVER_URL=http://localhost:8080
PORT=8080

# ==================================================
# BANCO DE DADOS - PostgreSQL
# ==================================================
DATABASE_ENABLED=true
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=postgresql://evolution:sua_senha_segura@localhost:5432/evolution_api
DATABASE_CONNECTION_CLIENT_NAME=evolution_api

# ==================================================
# REDIS - Cache e Sessões
# ==================================================
REDIS_ENABLED=true
REDIS_URI=redis://localhost:6379
REDIS_PREFIX_KEY=evolution

# ==================================================
# AUTENTICAÇÃO
# ==================================================
AUTHENTICATION_TYPE=apikey
AUTHENTICATION_API_KEY=sua_api_key_super_secreta_aqui
AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true

# ==================================================
# INSTÂNCIAS
# ==================================================
DEL_INSTANCE=false
INSTANCE_EXPIRATION_TIME=false

# ==================================================
# WEBHOOKS
# ==================================================
WEBHOOK_GLOBAL_URL=http://localhost:3006/webhooks/whatsapp
WEBHOOK_GLOBAL_ENABLED=true
WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=false

# ==================================================
# WHATSAPP
# ==================================================
QRCODE_LIMIT=30
QRCODE_COLOR=#198754

# ==================================================
# LOGS
# ==================================================
LOG_LEVEL=ERROR,WARN,DEBUG,INFO,LOG,VERBOSE,DARK,WEBHOOKS
LOG_COLOR=true
LOG_BAILEYS=false

# ==================================================
# CORS
# ==================================================
CORS_ORIGIN=*
CORS_METHODS=POST,GET,PUT,DELETE
CORS_CREDENTIALS=true
```

### 3️⃣ Gerar API Key Segura

```bash
# Linux/Mac
openssl rand -base64 32

# Windows (PowerShell)
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
[Convert]::ToBase64String($bytes)
```

**Copie a chave gerada** e cole em `AUTHENTICATION_API_KEY` no `.env`.

---

## 🗄️ Setup do Banco de Dados

### 1️⃣ Gerar Cliente Prisma

```bash
npm run db:generate
```

### 2️⃣ Aplicar Migrations

```bash
npm run db:deploy
```

**✅ Resultado esperado:**
```
✔ Generated Prisma Client
✔ Applied migrations
```

---

## 🚀 Executando a Evolution API

### 1️⃣ Build da Aplicação

```bash
npm run build
```

### 2️⃣ Iniciar o Servidor

```bash
npm run start
```

**✅ Servidor rodando em**: `http://localhost:8080`

### 3️⃣ Verificar Status

```bash
# Windows (PowerShell)
Invoke-WebRequest -Uri http://localhost:8080

# Linux/Mac
curl http://localhost:8080
```

---

## 📱 Conectando ao WhatsApp Web

### 1️⃣ Criar uma Instância

**Windows PowerShell:**
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "apikey" = "sua_api_key_super_secreta_aqui"
}

$body = @{
    instanceName = "sitio-multitrem"
    qrcode = $true
    integration = "WHATSAPP-BAILEYS"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8080/instance/create" -Method Post -Headers $headers -Body $body
```

**Linux/Mac:**
```bash
curl -X POST http://localhost:8080/instance/create \
  -H "Content-Type: application/json" \
  -H "apikey: sua_api_key_super_secreta_aqui" \
  -d '{
    "instanceName": "sitio-multitrem",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'
```

### 2️⃣ Obter QR Code

**PowerShell:**
```powershell
$headers = @{ "apikey" = "sua_api_key_super_secreta_aqui" }
Invoke-RestMethod -Uri "http://localhost:8080/instance/connect/sitio-multitrem" -Headers $headers
```

**Resposta:**
```json
{
  "base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "code": "1@abc123def456..."
}
```

### 3️⃣ Escanear QR Code

1. **Copie o base64** da resposta
2. **Cole no navegador**: `data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...`
3. **Abra o WhatsApp** no celular
4. **Vá em**: Configurações → Aparelhos conectados → Conectar um aparelho
5. **Escaneie o QR Code** que apareceu no navegador

### 4️⃣ Verificar Conexão

```powershell
$headers = @{ "apikey" = "sua_api_key_super_secreta_aqui" }
Invoke-RestMethod -Uri "http://localhost:8080/instance/connectionState/sitio-multitrem" -Headers $headers
```

**Resposta esperada:**
```json
{
  "instance": "sitio-multitrem",
  "state": "open"
}
```

✅ **Conectado com sucesso!**

---

## 🔗 Integração com WhatsApp Service

### 1️⃣ Configurar Webhook na Evolution API

O webhook já foi configurado no `.env`:
```bash
WEBHOOK_GLOBAL_URL=http://localhost:3006/webhooks/whatsapp
```

### 2️⃣ Configurar WhatsApp Service

Edite `services/whatsapp-service/.env`:

```bash
# Evolution API
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua_api_key_super_secreta_aqui
EVOLUTION_INSTANCE=sitio-multitrem

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# AI Service
AI_SERVICE_URL=http://localhost:3007

# Porta
PORT=3006
NODE_ENV=development
```

### 3️⃣ Iniciar WhatsApp Service

```bash
cd services/whatsapp-service
npm install
npm run start:dev
```

**✅ Serviço rodando em**: `http://localhost:3006`

---

## 🧪 Testando a Integração

### 1️⃣ Testar Envio de Mensagem

**PowerShell:**
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    phone = "5562999999999"
    message = "Olá! Teste do Sítio Multitrem 🌿"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3006/whatsapp/send" -Method Post -Headers $headers -Body $body
```

### 2️⃣ Verificar Status

```powershell
Invoke-RestMethod -Uri "http://localhost:3006/whatsapp/status"
```

### 3️⃣ Testar Recebimento de Mensagens

1. **Envie uma mensagem** do seu WhatsApp para o número conectado
2. **Verifique os logs** do WhatsApp Service
3. **A IA deve responder** automaticamente

---

## 🔍 Troubleshooting

### ❌ Erro: "Cannot connect to database"

**Causa**: PostgreSQL não está rodando ou credenciais incorretas.

**Solução Windows**:
1. Abra "Serviços" (services.msc)
2. Procure por "postgresql"
3. Inicie o serviço
4. Teste a conexão com pgAdmin

### ❌ Erro: "Redis connection failed"

**Causa**: Redis não está rodando.

**Solução Windows**:
```powershell
# Se instalou via WSL
wsl redis-server

# Ou inicie o serviço do Redis
```

### ❌ Erro: "QR Code expired"

**Causa**: QR Code tem validade de 30 segundos.

**Solução**:
1. Gere um novo QR Code
2. Escaneie rapidamente

### ❌ Erro: "Instance not found"

**Causa**: Instância não foi criada ou foi deletada.

**Solução**:
```powershell
# Listar instâncias
$headers = @{ "apikey" = "sua_api_key" }
Invoke-RestMethod -Uri "http://localhost:8080/instance/fetchInstances" -Headers $headers

# Criar nova instância se necessário
```

### ❌ Erro: "Webhook not receiving messages"

**Causa**: URL do webhook incorreta ou WhatsApp Service não está rodando.

**Solução**:
1. Verifique se o WhatsApp Service está rodando na porta 3006
2. Verifique se o `WEBHOOK_GLOBAL_URL` está correto no `.env` da Evolution API
3. Teste manualmente: `Invoke-WebRequest -Uri http://localhost:3006/webhooks/whatsapp`

---

## 📊 Arquitetura da Integração

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USUÁRIO ENVIA MENSAGEM VIA WHATSAPP                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. EVOLUTION API RECEBE MENSAGEM                            │
│    - Processa via Baileys (WhatsApp Web Protocol)          │
│    - Armazena no PostgreSQL                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. EVOLUTION API ENVIA WEBHOOK                              │
│    - POST http://localhost:3006/webhooks/whatsapp           │
│    - Payload com dados da mensagem                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. WHATSAPP SERVICE RECEBE WEBHOOK                          │
│    - Armazena histórico no Redis                            │
│    - Formata mensagem                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. WHATSAPP SERVICE CHAMA AI SERVICE                        │
│    - POST http://localhost:3007/ai/chat                     │
│    - Envia mensagem + histórico                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. AI SERVICE (AGNO) PROCESSA                               │
│    - Analisa intenção do usuário                            │
│    - Consulta produtos, carrinho, etc.                      │
│    - Gera resposta inteligente                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. WHATSAPP SERVICE ENVIA RESPOSTA                          │
│    - POST http://localhost:8080/message/sendText/...        │
│    - Via Evolution API                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. USUÁRIO RECEBE RESPOSTA NO WHATSAPP                      │
└─────────────────────────────────────────────────────────────┘
```

---

## ❓ FAQ

### 1. **Posso usar a mesma instância PostgreSQL do projeto?**
Sim! A Evolution API criará suas próprias tabelas com prefixo. Não há conflito.

### 2. **Preciso de um número de telefone dedicado?**
Não! Você pode usar seu número pessoal ou comercial. A Evolution API conecta via WhatsApp Web.

### 3. **Quantas instâncias posso criar?**
Ilimitadas! Cada instância = um número de WhatsApp conectado.

### 4. **A conexão cai se eu fechar o terminal?**
Não! Depois de conectado, a sessão fica salva no PostgreSQL. Use PM2 para manter rodando em produção.

### 5. **Como fazer deploy em produção?**
Use PM2, Docker ou serviços como Railway, Render, AWS. Configure HTTPS e domínio próprio.

### 6. **Posso enviar imagens e arquivos?**
Sim! A Evolution API suporta texto, imagens, áudio, vídeo, documentos, localização, etc.

### 7. **Como proteger a API?**
Use a `apikey` em todos os requests. Em produção, use HTTPS e firewall.

### 8. **O WhatsApp pode banir minha conta?**
Risco mínimo se usado com moderação. Evite spam e respeite as políticas do WhatsApp.

### 9. **Como monitorar a Evolution API?**
Logs em tempo real, endpoints de health check, e integração com ferramentas como Grafana.

### 10. **Preciso renovar o QR Code?**
Não! Após a primeira conexão, a sessão fica salva. Só precisa reconectar se desconectar manualmente.

---

## 🔗 Links Úteis

- **Evolution API GitHub**: https://github.com/EvolutionAPI/evolution-api
- **Documentação Oficial**: https://doc.evolution-api.com/
- **Baileys (WhatsApp Web Protocol)**: https://github.com/WhiskeySockets/Baileys
- **Swagger UI**: http://localhost:8080/api-docs (após iniciar)

---

## ✅ Checklist de Instalação

- [ ] Node.js v20+ instalado
- [ ] PostgreSQL rodando
- [ ] Redis rodando
- [ ] Evolution API clonada
- [ ] Dependências instaladas (`npm install`)
- [ ] Arquivo `.env` configurado
- [ ] API Key gerada e configurada
- [ ] Migrations aplicadas (`npm run db:deploy`)
- [ ] Evolution API rodando (`npm run start`)
- [ ] Instância criada (`sitio-multitrem`)
- [ ] QR Code escaneado
- [ ] Conexão verificada (state: "open")
- [ ] WhatsApp Service configurado
- [ ] WhatsApp Service rodando
- [ ] Teste de envio de mensagem funcionando
- [ ] Webhook recebendo mensagens
- [ ] IA respondendo automaticamente

---

**🎉 Parabéns! A Evolution API está instalada e integrada com sucesso!**

**Data de Criação**: Janeiro 2026  
**Versão**: 1.0.0  
**Status**: ✅ Produção Ready

---

**Desenvolvido com ❤️ para o Sítio Multitrem** 🌿

