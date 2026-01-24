# 🔧 Configuração ENV Unificada para Docker

## 📋 **Resumo**

Este guia consolida **TODAS** as configurações de ambiente necessárias para rodar a aplicação Sítio Multitrem em Docker, unificando:

- ✅ Evolution API (WhatsApp) 
- ✅ OpenAI e Google Calendar
- ✅ PostgreSQL e Redis  
- ✅ Todos os microserviços
- ✅ Frontend Next.js

## 🎯 **Como Aplicar a Configuração**

### **Passo 1: Arquivo .env Principal (Raiz)**

Copie o arquivo `env.docker.unified` para `.env` na raiz do projeto:

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02"
Copy-Item env.docker.unified .env
```

### **Passo 2: AI Agent Python (.env)**

Copie a configuração específica para o AI Agent:

```powershell
cd "services\ai-service\agno_agente_horta_multitrem"
Copy-Item env.docker .env
```

### **Passo 3: Configurar Chaves Faltantes**

Edite o arquivo `.env` na raiz e substitua:

```env
MERCADOPAGO_ACCESS_TOKEN=seu_token_do_mercado_pago_aqui
JWT_SECRET=meu_jwt_secret_super_seguro_de_256_bits_no_minimo_com_pelo_menos_32_caracteres
```

## 🔍 **Principais Unificações Realizadas**

### **🗃️ Bancos de Dados - URLs Docker**
```env
# PostgreSQL Principal (Sitio)
DATABASE_URL=postgresql://sitio_user:sitio_password@postgres:5432/sitio_multitrem

# PostgreSQL Evolution API
DATABASE_CONNECTION_URI=postgresql://evolution:evolution123@evolution-postgres:5432/evolution

# Redis Principal (Sitio) 
REDIS_URL=redis://:sitio_redis_pass@redis:6379

# Redis Evolution API
CACHE_REDIS_URI=redis://evolution-redis:6379/6
```

### **🔗 URLs de Serviços - Comunicação Interna Docker**
```env
EVOLUTION_API_URL=http://evolution-api:8080
WEBHOOK_GLOBAL_URL=http://whatsapp-service:3006/webhooks/whatsapp
AI_SERVICE_URL=http://ai-service:3007
CART_SERVICE_URL=http://cart-service:3002
```

### **🔑 Chaves Configuradas**
```env
# ✅ OpenAI - CONFIGURADA
OPENAI_API_KEY=sk-proj-OyvYreJXs64C82...

# ✅ Evolution API - CONFIGURADA  
EVOLUTION_API_KEY=W7F32PCvoLZdi5nng3pfkEOaD3RN9o...

# ⚠️ FALTA CONFIGURAR
MERCADOPAGO_ACCESS_TOKEN=seu_token_aqui
JWT_SECRET=seu_jwt_secret_aqui
```

## 🚀 **Como Usar**

### **Desenvolvimento**
```powershell
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### **Produção**
```powershell
docker-compose up -d
```

## 🎯 **Compatibilidade**

### **✅ Funcionará com Docker:**
- Todas as URLs usam nomes de containers Docker
- Configurações de rede internas
- Volumes e persistent data configurados
- Health checks configurados

### **✅ Mantém Funcionalidades:**
- WhatsApp via Evolution API
- AI Assistant com OpenAI  
- Google Calendar integration
- Todos os microserviços
- Frontend Next.js

## 📊 **Verificação**

Após aplicar as configurações, verifique se:

1. **Arquivo .env existe** na raiz com todas as configurações
2. **AI Agent tem .env próprio** com OpenAI configurada  
3. **Chaves obrigatórias** foram substituídas
4. **Docker compose** sobe sem erros

## ⚠️ **Importantes Observações**

1. **URLs Docker vs Local:**
   - Docker: `http://postgres:5432` (comunicação interna)  
   - Local: `http://localhost:5432` (acesso externo)

2. **Chaves Sensíveis:**
   - OpenAI: ✅ Já configurada
   - Evolution: ✅ Já configurada  
   - Mercado Pago: ⚠️ Precisa configurar
   - JWT Secret: ⚠️ Precisa configurar

3. **Múltiplos .env:**
   - **Raiz**: Configurações gerais e Docker
   - **AI Agent**: Configurações específicas do Python

## 🎉 **Resultado Final**

Com esta configuração unificada, você terá:

- ✅ **1 arquivo .env principal** com todas as configurações
- ✅ **Compatibilidade total** com Docker  
- ✅ **Todas as integrações** funcionando
- ✅ **Comunicação interna** otimizada entre containers
- ✅ **Facilidade de manutenção** - tudo em um lugar

## 🔧 **Comandos Rápidos**

```powershell
# Aplicar configuração
Copy-Item env.docker.unified .env
cd services\ai-service\agno_agente_horta_multitrem
Copy-Item env.docker .env
cd ..\..\..

# Editar chaves faltantes
notepad .env

# Testar configuração  
docker-compose up -d postgres redis
docker-compose logs postgres redis

# Subir tudo
docker-compose up -d
```

Agora sua aplicação está completamente unificada e pronta para Docker! 🚀