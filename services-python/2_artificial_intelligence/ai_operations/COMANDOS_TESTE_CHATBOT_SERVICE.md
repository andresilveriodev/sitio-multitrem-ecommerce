# 🧪 Comandos para Testar GPT-4.1-nano via Chatbot Service

## 📋 Pré-requisitos

1. Aplicação rodando na porta **8012**
2. Banco de dados configurado e funcionando

## 🚀 Comandos de Teste

### Opção 1: Script Python (Recomendado)

```bash
python test_chatbot_service_gpt41nano.py
```

### Opção 2: Comando HTTP Direto (PowerShell)

```powershell
# Passo 1: Criar conversa
$createConv = Invoke-RestMethod -Uri "http://localhost:8012/chatbot/conversations" -Method POST -ContentType "application/json" -Body '{"user_id": 1, "username": "test_user", "title": "Teste GPT-4.1-nano"}'
$conversationId = $createConv.id
Write-Host "Conversa criada: ID $conversationId"

# Passo 2: Enviar mensagem com GPT-4.1-nano
$chatBody = @{
    conversation_id = $conversationId
    message = "Olá! Você está funcionando com GPT-4.1-nano?"
    provider = "openai"
    model = "gpt-4.1-nano"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8012/chatbot/chat" -Method POST -ContentType "application/json" -Body $chatBody
Write-Host "Resposta da IA: $($response.ai_response)"
```

### Opção 3: Comando cURL

```bash
# Passo 1: Criar conversa
CONV_ID=$(curl -X POST http://localhost:8012/chatbot/conversations \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "username": "test_user", "title": "Teste GPT-4.1-nano"}' \
  | jq -r '.id')

echo "Conversa criada: ID $CONV_ID"

# Passo 2: Enviar mensagem com GPT-4.1-nano
curl -X POST http://localhost:8012/chatbot/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"conversation_id\": $CONV_ID,
    \"message\": \"Olá! Você está funcionando com GPT-4.1-nano?\",
    \"provider\": \"openai\",
    \"model\": \"gpt-4.1-nano\"
  }"
```

### Opção 4: Python One-Liner

```python
import httpx
import json

# Criar conversa
conv = httpx.post("http://localhost:8012/chatbot/conversations", json={"user_id": 1, "username": "test", "title": "Teste"}).json()
conv_id = conv["id"]

# Enviar mensagem
response = httpx.post("http://localhost:8012/chatbot/chat", json={
    "conversation_id": conv_id,
    "message": "Olá! Você está funcionando?",
    "provider": "openai",
    "model": "gpt-4.1-nano"
}).json()

print(f"Resposta: {response['ai_response']}")
```

## 📝 Endpoints Utilizados

### 1. Criar Conversa
```
POST http://localhost:8012/chatbot/conversations
Content-Type: application/json

{
  "user_id": 1,
  "username": "test_user",
  "title": "Teste GPT-4.1-nano"
}
```

**Resposta:**
```json
{
  "id": 123,
  "user_id": 1,
  "title": "Teste GPT-4.1-nano",
  "status": "active"
}
```

### 2. Enviar Mensagem com GPT-4.1-nano
```
POST http://localhost:8012/chatbot/chat
Content-Type: application/json

{
  "conversation_id": 123,
  "message": "Olá! Você está funcionando?",
  "provider": "openai",
  "model": "gpt-4.1-nano"
}
```

**Resposta esperada:**
```json
{
  "user_message": "Olá! Você está funcionando?",
  "ai_response": "Olá! Sim, estou funcionando perfeitamente...",
  "conversation_id": 123
}
```

## ✅ Verificação Rápida

Antes de testar, verifique se a aplicação está rodando:

```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8012/health" -UseBasicParsing

# Ou
curl http://localhost:8012/health
```

## 🔍 Troubleshooting

- **Erro 404 na conversa**: Certifique-se de criar a conversa primeiro
- **Erro 500**: Verifique os logs da aplicação
- **Timeout**: A aplicação pode não estar rodando ou está muito lenta

---

**Use o script `test_chatbot_service_gpt41nano.py` para teste automatizado!**





