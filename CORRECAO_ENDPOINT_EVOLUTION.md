# 🔧 CORREÇÃO: Endpoint Evolution API

## ❌ PROBLEMA ENCONTRADO

O WhatsApp Service estava usando o endpoint **ERRADO** para enviar mensagens via Evolution API:

### ❌ Endpoint Antigo (Errado)
```
POST /instance/{instanceName}/send-text
```

### ✅ Endpoint Correto
```
POST /message/sendText/{instanceName}
```

---

## 🔍 DETALHES DA CORREÇÃO

**Arquivo**: `services/whatsapp-service/src/whatsapp/whatsapp.service.ts`

### Antes (Errado):
```typescript
this.axiosInstance = axios.create({
  baseURL: `${this.baseUrl}/instance/${this.instanceName}`,  // ❌ ERRADO
  headers: {
    'Content-Type': 'application/json',
    apikey: this.apiKey,
  },
})

async sendText(to: string, message: string) {
  const response = await this.axiosInstance.post('/send-text', {  // ❌ ERRADO
    number: to,
    text: message,
  })
}
```

**Resultado**: `POST http://localhost:8080/instance/sitio-multitrem/send-text` → **404 Not Found**

### Depois (Correto):
```typescript
this.axiosInstance = axios.create({
  baseURL: this.baseUrl,  // ✅ CORRETO (http://localhost:8080)
  headers: {
    'Content-Type': 'application/json',
    apikey: this.apiKey,
  },
})

async sendText(to: string, message: string) {
  const response = await this.axiosInstance.post(`/message/sendText/${this.instanceName}`, {  // ✅ CORRETO
    number: to,
    text: message,
  })
}
```

**Resultado**: `POST http://localhost:8080/message/sendText/sitio-multitrem` → **✅ 200 OK**

---

## 🚀 COMO APLICAR A CORREÇÃO

### 1. Reiniciar o WhatsApp Service

Se o WhatsApp Service já estiver rodando, você precisa **reiniciá-lo** para aplicar a mudança:

```powershell
# No terminal onde o WhatsApp Service está rodando:
# Pressione Ctrl+C para parar

# Depois reinicie:
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"
npm run start:dev
```

### 2. Aguardar Inicialização

Aguarde ver no terminal:
```
✅ Redis conectado com sucesso
🚀 Redis pronto para uso
[NestApplication] Nest application successfully started
```

---

## 🧪 TESTAR NOVAMENTE

### Opção 1: Teste Manual via Script

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node test-webhook-direct.js
```

**Resultado esperado**:
```
📊 Status: 200 OK
✅ Teste bem-sucedido!
```

### Opção 2: Teste Real via WhatsApp

1. Envie uma mensagem no WhatsApp conectado
2. Aguarde a resposta do robô da IA
3. Verifique os logs do WhatsApp Service

---

## 📊 ENDPOINTS CORRETOS DA EVOLUTION API

Para referência futura, os endpoints corretos são:

### Enviar Mensagem de Texto
```
POST /message/sendText/{instanceName}
Body: {
  "number": "5511999999999",
  "text": "Mensagem"
}
```

### Enviar Mídia
```
POST /message/sendMedia/{instanceName}
Body: {
  "number": "5511999999999",
  "mediatype": "image",
  "media": "base64...",
  "caption": "Legenda"
}
```

### Enviar Botões
```
POST /message/sendButtons/{instanceName}
Body: {
  "number": "5511999999999",
  "title": "Título",
  "description": "Descrição",
  "buttons": [...]
}
```

### Enviar Lista
```
POST /message/sendList/{instanceName}
Body: {
  "number": "5511999999999",
  "title": "Título",
  "description": "Descrição",
  "sections": [...]
}
```

---

## 🔍 COMO VERIFICAR SE ESTÁ FUNCIONANDO

### 1. Ver Logs do WhatsApp Service

Quando uma mensagem chegar, você deve ver:
```
📥 Webhook recebido
📤 Mensagem extraída: "Olá, quero comprar hortaliças"
💾 Salvo no Redis
🤖 Roteando para agente: Vendedor
📤 Enviando para Agno...
✅ Resposta recebida do Agno
📤 Enviando mensagem via Evolution API...
✅ Mensagem enviada com sucesso!
```

### 2. Ver Logs da Evolution API

```powershell
docker logs -f evolution_api --tail 50
```

Você deve ver requests como:
```
POST /message/sendText/sitio-multitrem 200
```

### 3. Ver Logs do Agno

No terminal do Agno, você deve ver:
```
Recebendo mensagem...
Agent: Vendedor
Processando com GPT-4...
Resposta gerada
```

---

## ⚠️ OBSERVAÇÕES IMPORTANTES

1. **Sempre use o endpoint completo** `/message/sendText/{instanceName}`
2. **Não use** `/instance/{instanceName}/send-text` (não existe)
3. **A baseURL deve ser apenas** `http://localhost:8080`
4. **O instanceName vai no path** do endpoint, não na baseURL
5. **O apiKey vai no header**, não no body

---

## 📚 DOCUMENTAÇÃO EVOLUTION API

Para mais informações sobre os endpoints corretos:
- Swagger UI: `http://localhost:8080/docs`
- Documentação oficial: `https://doc.evolution-api.com`

---

**Data da correção**: 08/01/2026
**Status**: ✅ **CORRIGIDO**

🎉 **Agora o WhatsApp Service pode enviar mensagens corretamente via Evolution API!**



