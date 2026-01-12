# 🚀 Guia Completo: Como Rodar Tudo e Fazer o Chat Funcionar

## 📋 O Que Você Precisa Rodar (na ordem)

1. **Evolution API** (WhatsApp + Webhook)
2. **Agno AgentOS** (Inteligência Artificial)
3. **WhatsApp Service** (Ponte entre Evolution e Agno)

---

## 🔧 PASSO 1: Preparar o Ambiente

### 1.1. Corrigir Redis no WhatsApp Service

Abra o PowerShell e execute:

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"

# Remover senha do Redis
$env = Get-Content .env -Raw
$env = $env -replace 'REDIS_PASSWORD=.*', 'REDIS_PASSWORD='
Set-Content .env $env

Write-Host "✅ Redis configurado!" -ForegroundColor Green
```

---

## 🚀 PASSO 2: Iniciar os Serviços

### 2.1. Terminal 1 - Evolution API (Docker)

```powershell
# Ir para a pasta da Evolution API
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"

# Iniciar Evolution API
docker-compose up -d

# Aguardar iniciar
Start-Sleep -Seconds 15

# Configurar webhook
node configure-webhook.js

Write-Host ""
Write-Host "✅ Evolution API rodando!" -ForegroundColor Green
Write-Host "📱 Frontend: http://localhost:3001" -ForegroundColor Cyan
Write-Host "🔌 API: http://localhost:8080" -ForegroundColor Cyan
```

**Resultado esperado**:
```
✅ Webhook configurado com sucesso!
🎉 Pronto! Agora as mensagens do WhatsApp serão enviadas para o WhatsApp Service!
```

---

### 2.2. Terminal 2 - Agno AgentOS (Python)

Abra um **NOVO terminal PowerShell** e execute:

```powershell
# Ir para a pasta do Agno
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\ai-service\agno-agent"

# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Iniciar Agno
python my_os.py
```

**Resultado esperado**:
```
============================================================
SÍTIO MULTITREM - AGENTOS
============================================================
Porta: 7777 (padrão AgentOS)
App Interface: http://localhost:7777
API Docs: http://localhost:7777/docs

Agentes Disponíveis:
  - Vendedor - apresentar produtos, responder dúvidas sobre eles e ajudar a adicionar itens ao carrinho
  - Agendamento - verificar a disponibilidade de datas e horários para entrega e agendar pedidos
  - Pagamento - gerar links de pagamento (Pix, Boleto) e verificar status de pagamentos
  - Suporte - responder a dúvidas gerais, ajudar com problemas, cancelamentos e rastreamento de pedidos
============================================================
```

---

### 2.3. Terminal 3 - WhatsApp Service (Node.js)

Abra um **NOVO terminal PowerShell** e execute:

```powershell
# Ir para a pasta do WhatsApp Service
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"

# Iniciar WhatsApp Service
npm run start:dev
```

**Resultado esperado**:
```
[Nest] INFO [NestApplication] Nest application successfully started
[Nest] INFO WhatsApp Service listening on port 3006
[Nest] INFO ✅ WhatsApp Service conectado ao Redis
[Nest] INFO ✅ Pronto para receber webhooks
```

---

## 📱 PASSO 3: Conectar o WhatsApp

### 3.1. Acessar o Frontend da Evolution API

1. Abra o navegador: **http://localhost:3001**
2. Faça login (se solicitado)
3. Procure pela instância **sitio-multitrem**

### 3.2. Escanear QR Code (se necessário)

Se o WhatsApp não estiver conectado:

1. No frontend, clique em **"Connect"** ou **"QR Code"**
2. Abra o WhatsApp no celular
3. Vá em **Configurações > Aparelhos conectados > Conectar um aparelho**
4. Escaneie o QR Code

**Status esperado**: ✅ **OPEN** ou **CONNECTED**

---

## 🧪 PASSO 4: Testar o Chat

### 4.1. Teste Direto (Verificar se tudo está funcionando)

Em um terminal PowerShell:

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node test-webhook-direct.js
```

**Resultado esperado**:
```
🧪 Testando webhook diretamente...
📤 Enviando payload para: http://localhost:3006/webhooks/whatsapp
📝 Mensagem: Olá! Quero comprar hortaliças
📊 Status: 200 OK
✅ Resposta recebida
```

### 4.2. Teste Real (Enviar mensagem pelo WhatsApp)

1. **No celular**, envie uma mensagem para o número conectado
2. **Exemplo**: "Olá! Quero comprar hortaliças"
3. **Aguarde**: O robô deve responder em alguns segundos

**Mensagens de teste**:
- "Olá, quero comprar hortaliças" → Aciona o **Vendedor**
- "Quero agendar uma entrega" → Aciona o **Agendamento**
- "Como faço para pagar?" → Aciona o **Pagamento**
- "Preciso de ajuda" → Aciona o **Suporte**

---

## 📊 PASSO 5: Verificar os Logs

### Verificar se está funcionando:

**Terminal do WhatsApp Service** (deve aparecer):
```
📥 Webhook recebido de Evolution API
📞 Número: 5562999999999
💬 Mensagem: Olá! Quero comprar hortaliças
🤖 Roteando para agente: Vendedor
✅ Resposta enviada para WhatsApp
```

**Terminal do Agno AgentOS** (deve aparecer):
```
Processando mensagem do usuário: 5562999999999
Mensagem: Olá! Quero comprar hortaliças
Agente selecionado: Vendedor
```

**Logs da Evolution API**:
```powershell
docker logs evolution_api --tail 30 -f
```

---

## ❌ Solução de Problemas

### Problema 1: "Redis WRONGPASS"
**Solução**: Volte ao PASSO 1.1 e remova a senha do Redis

### Problema 2: "Webhook não está sendo recebido"
**Solução**:
```powershell
# Reiniciar Evolution API
docker restart evolution_api
Start-Sleep -Seconds 10

# Reconfigurar webhook
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node configure-webhook.js
```

### Problema 3: "Agno não responde"
**Solução**: Verificar se o Agno está rodando:
```powershell
# Testar se Agno está online
curl http://localhost:7777/health
```

### Problema 4: "WhatsApp desconectou"
**Solução**: Reconectar escaneando o QR Code novamente (PASSO 3.2)

---

## 🎯 Checklist Final

Antes de testar, verifique se todos estão **rodando**:

- [ ] **Evolution API**: `docker ps` deve mostrar `evolution_api` rodando
- [ ] **Agno AgentOS**: Terminal 2 deve estar mostrando logs do Agno
- [ ] **WhatsApp Service**: Terminal 3 deve estar mostrando `Nest application successfully started`
- [ ] **WhatsApp Conectado**: Frontend deve mostrar status **OPEN**
- [ ] **Webhook Configurado**: Comando `configure-webhook.js` executado com sucesso

---

## 🚀 Script de Inicialização Rápida

Salve este script como `iniciar-tudo.ps1` e execute-o:

```powershell
# Script de Inicialização Completa
# Salve como: iniciar-tudo.ps1

$projectPath = "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  INICIANDO SISTEMA COMPLETO" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Corrigir Redis
Write-Host "📝 1/5 - Corrigindo configuração do Redis..." -ForegroundColor Yellow
cd "$projectPath\services\whatsapp-service"
$env = Get-Content .env -Raw
$env = $env -replace 'REDIS_PASSWORD=.*', 'REDIS_PASSWORD='
Set-Content .env $env
Write-Host "   ✅ Redis configurado!" -ForegroundColor Green
Write-Host ""

# 2. Iniciar Evolution API
Write-Host "📦 2/5 - Iniciando Evolution API (Docker)..." -ForegroundColor Yellow
cd "$projectPath\services\evolution-api"
docker-compose up -d
Write-Host "   ⏳ Aguardando inicialização (15s)..." -ForegroundColor Gray
Start-Sleep -Seconds 15
Write-Host "   ✅ Evolution API iniciada!" -ForegroundColor Green
Write-Host ""

# 3. Configurar Webhook
Write-Host "🔗 3/5 - Configurando webhook..." -ForegroundColor Yellow
node configure-webhook.js
Write-Host "   ✅ Webhook configurado!" -ForegroundColor Green
Write-Host ""

# 4. Informar sobre Agno
Write-Host "🤖 4/5 - Agno AgentOS" -ForegroundColor Yellow
Write-Host "   ⚠️  Abra um NOVO terminal e execute:" -ForegroundColor Red
Write-Host "   cd '$projectPath\services\ai-service\agno-agent'" -ForegroundColor White
Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "   python my_os.py" -ForegroundColor White
Write-Host ""

# 5. Informar sobre WhatsApp Service
Write-Host "📱 5/5 - WhatsApp Service" -ForegroundColor Yellow
Write-Host "   ⚠️  Abra um NOVO terminal e execute:" -ForegroundColor Red
Write-Host "   cd '$projectPath\services\whatsapp-service'" -ForegroundColor White
Write-Host "   npm run start:dev" -ForegroundColor White
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ✅ PREPARAÇÃO CONCLUÍDA!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Yellow
Write-Host "   1. Abra 2 novos terminais" -ForegroundColor White
Write-Host "   2. Rode o Agno no primeiro" -ForegroundColor White
Write-Host "   3. Rode o WhatsApp Service no segundo" -ForegroundColor White
Write-Host "   4. Conecte o WhatsApp em http://localhost:3001" -ForegroundColor White
Write-Host "   5. Envie uma mensagem de teste!" -ForegroundColor White
Write-Host ""
Write-Host "🔗 Links úteis:" -ForegroundColor Yellow
Write-Host "   Evolution Frontend: http://localhost:3001" -ForegroundColor Cyan
Write-Host "   Evolution API: http://localhost:8080" -ForegroundColor Cyan
Write-Host "   Agno Docs: http://localhost:7777/docs" -ForegroundColor Cyan
Write-Host ""
```

Para executar:
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02"
.\iniciar-tudo.ps1
```

---

## 📞 Suporte

Se algo não funcionar:

1. **Verificar logs** de cada serviço
2. **Consultar** `DIAGNOSTICO_WEBHOOK.md` para problemas específicos
3. **Reportar** os erros com prints dos logs

**Boa sorte!** 🚀🎉



