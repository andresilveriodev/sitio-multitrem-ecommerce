# 🔍 Diagnóstico: WhatsApp não está funcionando

## ❌ PROBLEMAS IDENTIFICADOS

### 1. **WhatsApp Service não está rodando**
- **Status**: Container não existe/parado
- **Erro**: Erros de compilação TypeScript impedem o build
- **Impacto**: Mensagens não são processadas

### 2. **Webhook não configurado na Evolution API**
- **Status**: Evolution API recebe mensagens mas não encaminha
- **Problema**: Webhook não aponta para WhatsApp Service
- **Impacto**: Mensagens ficam presas na Evolution API

### 3. **Erros de TypeScript no WhatsApp Service**
```
- src/agno/agno.service.ts: Property 'default' does not exist on FormData
- src/chatwoot/chatwoot.service.ts: Módulos não exportados corretamente
```

---

## ✅ SOLUÇÕES NECESSÁRIAS

### **Solução 1: Corrigir erros TypeScript do WhatsApp Service**

**Arquivos com problemas:**
- `services/whatsapp-service/src/agno/agno.service.ts`
- `services/whatsapp-service/src/chatwoot/chatwoot.service.ts`
- `services/whatsapp-service/src/chatwoot/dto/chatwoot-webhook.dto.ts`

**Ações:**
1. Corrigir importação de FormData
2. Corrigir exports dos DTOs do Chatwoot
3. Rebuild do container

### **Solução 2: Configurar Webhook na Evolution API**

**Instância atual:**
- **Nome**: "Sitio MultiTrem"
- **ID**: `465d4b7c-3834-401d-b35f-c86cd92c3aa0`
- **Status**: `open` (conectado)

**Webhook necessário:**
```json
{
  "webhook": {
    "enabled": true,
    "url": "http://whatsapp-service:3006/webhooks/whatsapp",
    "webhook_by_events": false,
    "events": [
      "MESSAGES_UPSERT",
      "MESSAGES_UPDATE", 
      "CONNECTION_UPDATE"
    ]
  }
}
```

**Como configurar:**
1. Via Evolution Manager: http://localhost:8081/manager
2. Via API REST (após corrigir nome da instância)
3. Via variáveis de ambiente no docker-compose.yml

### **Solução 3: Subir WhatsApp Service**

Após corrigir erros TypeScript:
```powershell
docker-compose build whatsapp-service
docker-compose up -d whatsapp-service
```

---

## 🔄 FLUXO ESPERADO (quando funcionar)

```
📱 WhatsApp
    │
    │ Mensagem: "Olá"
    ▼
┌─────────────────────────┐
│   Evolution API         │
│   (Port: 8081)          │
│   ✅ Recebe mensagem    │
│   ✅ Webhook configurado│
└─────────────────────────┘
    │
    │ POST http://whatsapp-service:3006/webhooks/whatsapp
    ▼
┌─────────────────────────┐
│   WhatsApp Service      │
│   (Port: 3006)          │
│   ✅ Recebe webhook     │
│   ✅ Processa mensagem │
│   ✅ Chama AI Service   │
└─────────────────────────┘
    │
    │ POST http://ai-service:3007/ai/chat
    ▼
┌─────────────────────────┐
│   AI Service            │
│   (Port: 3007)          │
│   ✅ Gera resposta      │
│   ✅ Retorna para WA    │
└─────────────────────────┘
```

---

## 📊 STATUS ATUAL DOS SERVIÇOS

| Serviço | Status | Porta | Problema |
|---------|--------|-------|----------|
| Evolution API | ✅ Rodando | 8081 | Webhook não configurado |
| WhatsApp Service | ❌ Não rodando | 3006 | Erros TypeScript |
| AI Service | ✅ Rodando | 3007 | Funcional |

---

## 🚀 PRÓXIMOS PASSOS

1. **Corrigir erros TypeScript** no WhatsApp Service
2. **Build e subir** WhatsApp Service
3. **Configurar webhook** na Evolution API (via Manager ou API)
4. **Testar** enviando mensagem no WhatsApp
5. **Verificar logs** em tempo real

---

## 📝 COMANDOS ÚTEIS

```powershell
# Ver logs do Evolution API
docker-compose logs -f evolution-api

# Ver logs do WhatsApp Service (quando estiver rodando)
docker-compose logs -f whatsapp-service

# Verificar status dos containers
docker-compose ps

# Verificar webhook configurado
$headers = @{ 'apikey' = 'W7F32PCvoLZdi5nng3pfkEOaD3RN9o/YDrIuCmH24OA=' }
Invoke-WebRequest -Uri 'http://localhost:8081/webhook/find/Sitio MultiTrem' -Method GET -Headers $headers
```

---

**Data do diagnóstico**: 24/01/2026 18:48
**Instância WhatsApp**: "Sitio MultiTrem" (conectada)
