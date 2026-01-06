# 📱 Guia Completo: WhatsApp (Evolution API) + Chatwoot

Este guia mostra passo a passo como conectar o WhatsApp na Evolution API e instalar/configurar o Chatwoot visualmente.

---

## 🚀 PARTE 1: Instalar e Rodar Evolution API

> **📚 Guia Completo**: Consulte `GUIA_EVOLUTION_API.md` para instruções detalhadas de instalação.

### Opção Rápida: Script Automático

**Windows:**
```powershell
.\scripts\instalar-evolution-api.ps1
```

**Linux/Mac:**
```bash
./scripts/instalar-evolution-api.sh
```

### Ou Instalação Manual via Docker

1. Crie uma pasta `evolution-api`
2. Crie um `docker-compose.yml` (veja `GUIA_EVOLUTION_API.md`)
3. Execute: `docker-compose up -d`

---

## 🔌 PARTE 2: Conectar WhatsApp na Evolution API

### Pré-requisitos

1. ✅ Evolution API instalada e rodando (porta 8081)
2. WhatsApp Service do projeto rodando (porta 3006)
3. Acesso à interface web da Evolution API

---

### Passo 1: Acessar a Evolution API

1. Abra seu navegador e acesse:
   ```
   http://localhost:8081
   ```
   (ou a URL onde sua Evolution API está rodando)

2. Você verá a interface da Evolution API

---

### Passo 2: Criar uma Instância

1. Na interface da Evolution API, procure por **"Create Instance"** ou **"Nova Instância"**

2. Preencha os dados:
   - **Nome da Instância**: `sitio-multitrem` (ou o nome configurado no seu `.env`)
   - **API Key**: Anote a chave gerada (você precisará dela)

3. Clique em **"Create"** ou **"Criar"**

---

### Passo 3: Conectar WhatsApp

1. Após criar a instância, você verá um **QR Code** na tela

2. Abra o **WhatsApp** no seu celular

3. Vá em **Configurações** → **Aparelhos conectados** → **Conectar um aparelho**

4. Escaneie o **QR Code** exibido na Evolution API

5. Aguarde a conexão ser estabelecida (status mudará para "connected" ou "conectado")

---

### Passo 4: Configurar Webhook

1. Na interface da Evolution API, vá em **"Webhooks"** ou **"Configurações"**

2. Configure o webhook para apontar para seu WhatsApp Service:
   ```
   http://seu-servidor:3006/webhooks/whatsapp
   ```
   
   **Exemplo local:**
   ```
   http://localhost:3006/webhooks/whatsapp
   ```

3. Salve as configurações

---

### Passo 5: Configurar Variáveis de Ambiente

1. Abra o arquivo `.env` do **whatsapp-service**:
   ```
   services/whatsapp-service/.env
   ```

2. Configure as variáveis:
   ```env
   EVOLUTION_API_URL=http://localhost:8081
   EVOLUTION_API_KEY=sua_chave_api_aqui
   EVOLUTION_INSTANCE=sitio-multitrem
   REDIS_HOST=localhost
   REDIS_PORT=6379
   AI_SERVICE_URL=http://localhost:3007
   PORT=3006
   ```

3. Salve o arquivo

4. Reinicie o WhatsApp Service:
   ```bash
   cd services/whatsapp-service
   npm run start:dev
   ```

---

### Passo 6: Testar a Conexão

1. Envie uma mensagem de teste para o número conectado no WhatsApp

2. Verifique os logs do WhatsApp Service para confirmar que a mensagem foi recebida

3. A IA deve responder automaticamente

---

## 🎯 PARTE 2: Instalar e Configurar Chatwoot

### Opção A: Instalação via Docker (Recomendado)

#### Passo 1: Instalar Docker

1. Baixe e instale o Docker Desktop:
   - Windows: https://www.docker.com/products/docker-desktop
   - Mac: https://www.docker.com/products/docker-desktop
   - Linux: Siga as instruções para sua distribuição

2. Verifique a instalação:
   ```bash
   docker --version
   docker-compose --version
   ```

---

#### Passo 2: Criar docker-compose.yml

1. Crie um arquivo `docker-compose.yml` em uma pasta (ex: `chatwoot`):

```yaml
version: '3'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: chatwoot
      POSTGRES_PASSWORD: chatwoot
      POSTGRES_DB: chatwoot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:alpine
    restart: always

  rails:
    image: chatwoot/chatwoot:latest
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_USERNAME: chatwoot
      POSTGRES_PASSWORD: chatwoot
      POSTGRES_DATABASE: chatwoot
      REDIS_HOST: redis
      REDIS_PORT: 6379
      RAILS_ENV: production
      SECRET_KEY_BASE: seu_secret_key_aqui
      FRONTEND_URL: http://localhost:3000
      FORCE_SSL: 'false'
    ports:
      - "3000:3000"
    depends_on:
      - postgres
      - redis
    restart: always

volumes:
  postgres_data:
```

2. **IMPORTANTE**: Gere um SECRET_KEY_BASE:
   ```bash
   docker run --rm chatwoot/chatwoot:latest bundle exec rails secret
   ```
   Copie o resultado e substitua `seu_secret_key_aqui` no docker-compose.yml

---

#### Passo 3: Iniciar o Chatwoot

1. Abra o terminal na pasta onde está o `docker-compose.yml`

2. Execute:
   ```bash
   docker-compose up -d
   ```

3. Aguarde alguns minutos para os containers iniciarem

4. Verifique se está rodando:
   ```bash
   docker-compose ps
   ```

---

#### Passo 4: Acessar o Chatwoot

1. Abra o navegador e acesse:
   ```
   http://localhost:3000
   ```

2. Você verá a tela de **"Sign Up"** (Primeiro acesso)

3. Crie sua conta de administrador:
   - Nome
   - Email
   - Senha

4. Faça login

---

### Opção B: Instalação Manual (Self-hosted)

Se preferir instalação manual, siga o guia oficial:
https://www.chatwoot.com/docs/self-hosted/deployment/docker

---

## ⚙️ PARTE 3: Configurar Chatwoot para WhatsApp

### Passo 1: Criar uma Inbox do Tipo API

1. No Chatwoot, vá em **Settings** (Configurações) → **Inboxes**

2. Clique em **"Add Inbox"** ou **"Adicionar Caixa de Entrada"**

3. Selecione **"API"** como tipo

4. Preencha:
   - **Name**: `WhatsApp - Sítio Multitrem`
   - **Description**: `Inbox para WhatsApp via Evolution API`

5. Clique em **"Create"**

6. **ANOTE** o **Inbox ID** que será exibido (você precisará dele)

---

### Passo 2: Obter Access Token

1. No Chatwoot, vá em **Settings** → **Applications** → **Access Tokens**

2. Clique em **"Add Token"** ou **"Adicionar Token"**

3. Preencha:
   - **Name**: `WhatsApp Integration`
   - **Permission**: Selecione **"Full Access"**

4. Clique em **"Create"**

5. **COPIE E SALVE** o token gerado (ele só aparece uma vez!)

---

### Passo 3: Obter Account ID

1. No Chatwoot, vá em **Settings** → **Accounts**

2. Você verá o **Account ID** (geralmente é `1` para a primeira conta)

3. **ANOTE** este ID

---

### Passo 4: Configurar Webhook no Chatwoot

1. No Chatwoot, vá em **Settings** → **Applications** → **Webhooks**

2. Clique em **"Add Webhook"**

3. Configure:
   - **URL**: `http://seu-servidor:3006/webhooks/chatwoot`
   
   **Exemplo local:**
   ```
   http://localhost:3006/webhooks/chatwoot
   ```

   - **Events**: Selecione:
     - ✅ `message_created`
     - ✅ `message_updated`

4. Clique em **"Create"**

---

### Passo 5: Configurar Variáveis de Ambiente no WhatsApp Service

1. Abra o arquivo `.env` do **whatsapp-service**:
   ```
   services/whatsapp-service/.env
   ```

2. Adicione/atualize as variáveis do Chatwoot:
   ```env
   # Chatwoot (opcional - para controle e monitoramento)
   CHATWOOT_URL=http://localhost:3000
   CHATWOOT_ACCOUNT_ID=1
   CHATWOOT_ACCESS_TOKEN=seu_token_aqui
   CHATWOOT_INBOX_ID=1
   CHATWOOT_AUTO_ASSIGN=false
   CHATWOOT_AI_ENABLED=true
   ```

3. Substitua:
   - `CHATWOOT_ACCOUNT_ID`: O Account ID que você anotou
   - `CHATWOOT_ACCESS_TOKEN`: O token que você copiou
   - `CHATWOOT_INBOX_ID`: O Inbox ID que você anotou

4. Salve o arquivo

5. Reinicie o WhatsApp Service:
   ```bash
   cd services/whatsapp-service
   npm run start:dev
   ```

---

## ✅ PARTE 4: Testar a Integração Completa

### Teste 1: Mensagem Recebida no WhatsApp

1. Envie uma mensagem para o número conectado no WhatsApp

2. Verifique no Chatwoot:
   - A mensagem deve aparecer na inbox
   - Um contato deve ser criado automaticamente
   - Uma conversa deve ser iniciada

3. Se `CHATWOOT_AI_ENABLED=true`:
   - A IA deve responder automaticamente
   - A resposta da IA também aparecerá no Chatwoot

---

### Teste 2: Resposta Manual do Agente

1. No Chatwoot, encontre a conversa recebida

2. **Atribua a conversa a você** (ou a um agente):
   - Clique na conversa
   - Clique em **"Assign"** ou **"Atribuir"**
   - Selecione você mesmo

3. Digite uma resposta no Chatwoot

4. A mensagem deve ser enviada automaticamente para o WhatsApp

---

### Teste 3: Sincronização Bidirecional

1. Envie uma mensagem do WhatsApp → Deve aparecer no Chatwoot
2. Responda no Chatwoot → Deve aparecer no WhatsApp
3. Envie outra mensagem do WhatsApp → Deve aparecer no Chatwoot

---

## 🔧 Troubleshooting (Solução de Problemas)

### Problema: WhatsApp não conecta na Evolution API

**Soluções:**
1. Verifique se o QR Code não expirou (gere um novo)
2. Verifique se o WhatsApp Service está rodando
3. Verifique as variáveis de ambiente (`EVOLUTION_API_URL`, `EVOLUTION_API_KEY`)
4. Verifique os logs do WhatsApp Service

---

### Problema: Mensagens não chegam no Chatwoot

**Soluções:**
1. Verifique se o webhook está configurado corretamente
2. Verifique se `CHATWOOT_ACCESS_TOKEN` está correto
3. Verifique se `CHATWOOT_INBOX_ID` está correto
4. Verifique os logs do WhatsApp Service
5. Teste o endpoint manualmente:
   ```bash
   curl -X GET http://localhost:3006/chatwoot/sync/5511999999999
   ```

---

### Problema: Chatwoot não envia mensagens para WhatsApp

**Soluções:**
1. Verifique se o webhook do Chatwoot está configurado
2. Verifique se a URL do webhook está acessível
3. Verifique os logs do Chatwoot
4. Verifique os logs do WhatsApp Service

---

### Problema: IA não responde quando conversa não está atribuída

**Soluções:**
1. Verifique se `CHATWOOT_AI_ENABLED=true`
2. Verifique se o AI Service está rodando
3. Verifique se `AI_SERVICE_URL` está correto
4. Verifique os logs do WhatsApp Service

---

## 📊 Resumo das Portas

| Serviço | Porta | URL |
|---------|-------|-----|
| Evolution API | 8081 | http://localhost:8081 |
| WhatsApp Service | 3006 | http://localhost:3006 |
| Chatwoot | 3000 | http://localhost:3000 |
| AI Service | 3007 | http://localhost:3007 |

---

## 📝 Checklist Final

- [ ] Evolution API instalada e rodando
- [ ] Instância criada na Evolution API
- [ ] WhatsApp conectado (QR Code escaneado)
- [ ] Webhook configurado na Evolution API
- [ ] Variáveis de ambiente do WhatsApp Service configuradas
- [ ] Chatwoot instalado e rodando
- [ ] Conta de administrador criada no Chatwoot
- [ ] Inbox do tipo API criada no Chatwoot
- [ ] Access Token gerado no Chatwoot
- [ ] Webhook configurado no Chatwoot
- [ ] Variáveis de ambiente do Chatwoot configuradas
- [ ] Teste de mensagem recebida funcionando
- [ ] Teste de resposta manual funcionando
- [ ] Sincronização bidirecional funcionando

---

## 🎉 Pronto!

Agora você tem:
- ✅ WhatsApp conectado via Evolution API
- ✅ Chatwoot instalado e configurado
- ✅ Integração completa entre WhatsApp ↔ Chatwoot ↔ IA
- ✅ Controle visual de todas as conversas
- ✅ Resposta automática da IA quando não há agente
- ✅ Intervenção manual de agentes quando necessário

---

## 📚 Referências

- **Evolution API**: https://doc.evolution-api.com/
- **Chatwoot Docs**: https://www.chatwoot.com/docs
- **Chatwoot Docker**: https://www.chatwoot.com/docs/self-hosted/deployment/docker

---

**Dúvidas?** Verifique os logs dos serviços ou consulte a documentação oficial.

