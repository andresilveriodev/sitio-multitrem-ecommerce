# 🔧 Como Configurar Webhook da Evolution API

## ❌ PROBLEMA IDENTIFICADO

O webhook está configurado mas **DESABILITADO**:
- ✅ URL: `http://whatsapp-service:3006/webhooks/whatsapp` (correta)
- ❌ **Enabled**: `false` (precisa ser `true`)
- ❌ **Events**: `[]` (vazio, precisa ter eventos)

---

## ✅ SOLUÇÃO: Configurar via Evolution Manager (RECOMENDADO)

### **Passo 1: Acessar Evolution Manager**

1. Abra o navegador
2. Acesse: **http://localhost:8081/manager**
3. Faça login com:
   - **Server URL**: `http://localhost:8081`
   - **API Key Global**: `W7F32PCvoLZdi5nng3pfkEOaD3RN9o/YDrIuCmH24OA=`

### **Passo 2: Configurar Webhook**

1. Na lista de instâncias, clique em **"Sitio MultiTrem"**
2. Vá na aba **"Webhooks"** ou **"Configurações"**
3. Configure:
   - **URL**: `http://whatsapp-service:3006/webhooks/whatsapp`
   - **Enabled**: ✅ **Marcar como habilitado**
   - **Events**: Selecionar:
     - ✅ `MESSAGES_UPSERT` (novas mensagens)
     - ✅ `MESSAGES_UPDATE` (atualizações de mensagens)
     - ✅ `CONNECTION_UPDATE` (status da conexão)
4. **Salvar** as configurações

---

## 🔄 ALTERNATIVA: Configurar via API (se Manager não funcionar)

### **Opção 1: Usar nome da instância sem espaços**

Se a instância tiver um nome alternativo sem espaços, use:

```powershell
$headers = @{ 
    'apikey' = 'W7F32PCvoLZdi5nng3pfkEOaD3RN9o/YDrIuCmH24OA='
    'Content-Type' = 'application/json' 
}

$body = @{
    webhook = @{
        enabled = $true
        url = 'http://whatsapp-service:3006/webhooks/whatsapp'
        webhook_by_events = $false
        events = @('MESSAGES_UPSERT', 'MESSAGES_UPDATE', 'CONNECTION_UPDATE')
    }
} | ConvertTo-Json -Depth 10

# Tentar com nome sem espaços
$instanceName = 'sitio-multitrem'  # ou outro nome alternativo
Invoke-WebRequest -Uri "http://localhost:8081/webhook/set/$instanceName" -Method POST -Headers $headers -Body $body
```

### **Opção 2: Renomear a instância**

Se possível, renomeie a instância para um nome sem espaços (ex: `sitio-multitrem`) e então configure o webhook.

---

## 🧪 TESTE APÓS CONFIGURAR

1. **Configure o webhook** (via Manager ou API)
2. **Envie uma mensagem** no WhatsApp
3. **Verifique os logs**:

```powershell
# Terminal 1: Logs do Evolution API
docker-compose logs -f evolution-api | Select-String "webhook|MESSAGES"

# Terminal 2: Logs do WhatsApp Service  
docker-compose logs -f whatsapp-service | Select-String "webhook|POST|message"
```

4. **O que você deve ver:**
   - Evolution API: `webhook sent to http://whatsapp-service:3006/webhooks/whatsapp`
   - WhatsApp Service: `POST /webhooks/whatsapp` recebido
   - WhatsApp Service: Processando mensagem e chamando AI

---

## 📊 VERIFICAR CONFIGURAÇÃO ATUAL

```powershell
$headers = @{ 'apikey' = 'W7F32PCvoLZdi5nng3pfkEOaD3RN9o/YDrIuCmH24OA=' }
$response = Invoke-WebRequest -Uri 'http://localhost:8081/webhook/find/Sitio MultiTrem' -Method GET -Headers $headers
$webhook = $response.Content | ConvertFrom-Json

Write-Host "URL: $($webhook.url)"
Write-Host "Enabled: $($webhook.enabled)"  # Deve ser TRUE
Write-Host "Events: $($webhook.events.Count)"  # Deve ser > 0
```

---

## ⚠️ PROBLEMA CONHECIDO

A Evolution API não aceita nomes de instância com **espaços** na URL da API REST. Por isso, a configuração via **Evolution Manager (interface web)** é a forma mais confiável.

---

## ✅ APÓS CONFIGURAR

Quando o webhook estiver habilitado e com eventos configurados:

1. ✅ Evolution API receberá mensagens
2. ✅ Evolution API enviará webhook para WhatsApp Service
3. ✅ WhatsApp Service processará e chamará AI Service
4. ✅ AI Service responderá
5. ✅ WhatsApp Service enviará resposta via Evolution API

---

**Status Atual**: Webhook configurado mas desabilitado
**Ação Necessária**: Habilitar webhook e configurar eventos via Evolution Manager
