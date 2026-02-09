# 🧪 Guia de Teste - Recebimento de Mensagens do Telegram

## 📋 Pré-requisitos

1. ✅ Token do bot configurado no `.env`
2. ✅ Chatbot Service rodando (porta 8002)
3. ✅ Serviço Telegram iniciado (porta 8021)

## 🚀 Passo a Passo para Testar

### 1. Iniciar o Serviço Telegram

```bash
cd 4_messages_apps_services/telegram_service
python main.py
```

Você deve ver:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8021
```

### 2. Verificar se o Serviço Está Rodando

Abra no navegador ou use curl:
```bash
curl http://localhost:8021/
```

Deve retornar:
```json
{
  "service": "telegram_service",
  "status": "running",
  "version": "1.0.0",
  "message": "Telegram Service - E-commerce"
}
```

### 3. Configurar Webhook (Desenvolvimento Local)

Para desenvolvimento local, você precisa expor o serviço publicamente. Use **ngrok**:

#### 3.1. Instalar ngrok
- Baixe em: https://ngrok.com/download
- Ou via chocolatey: `choco install ngrok`

#### 3.2. Iniciar ngrok
```bash
ngrok http 8021
```

Você verá algo como:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8021
```

#### 3.3. Configurar Webhook com URL do ngrok

```bash
curl -X POST http://localhost:8021/telegram/set-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://abc123.ngrok.io/telegram/webhook"
  }'
```

**OU** edite o `.env` e adicione:
```env
TELEGRAM_WEBHOOK_URL=https://abc123.ngrok.io/telegram/webhook
```

Depois execute:
```bash
curl -X POST http://localhost:8021/telegram/set-webhook
```

### 4. Verificar Webhook Configurado

```bash
curl http://localhost:8021/telegram/webhook-info
```

Deve retornar informações sobre o webhook, incluindo a URL configurada.

### 5. Testar Recebimento de Mensagens

#### 5.1. Enviar Mensagem no Telegram

1. Abra o Telegram
2. Procure pelo seu bot (pelo username que você criou)
3. Envie uma mensagem de teste: `Olá, teste`

#### 5.2. Verificar Logs

No terminal onde o serviço está rodando, você deve ver logs como:

```
INFO: Webhook recebido do Telegram update_id=123456
INFO: Mensagem recebida do Telegram chat_id=123456789 user_id=987654321 username=seu_usuario text_preview=Olá, teste
INFO: Enviando mensagem para chatbot user_id=telegram_987654321_123456789 message_preview=Olá, teste
INFO: Resposta recebida do chatbot user_id=telegram_987654321_123456789 success=True
```

#### 5.3. Verificar Resposta no Telegram

O bot deve responder com a mensagem processada pelo chatbot.

### 6. Teste Alternativo (Sem Chatbot)

Se o Chatbot Service não estiver rodando, você pode testar apenas o recebimento:

1. Envie uma mensagem no Telegram
2. Verifique os logs - deve aparecer "Mensagem recebida"
3. O bot tentará chamar o chatbot e pode dar erro, mas isso confirma que está recebendo

## 🔍 Verificações de Troubleshooting

### Verificar Token do Bot

```bash
# Testar se o token está correto
curl "https://api.telegram.org/bot<SEU_TOKEN>/getMe"
```

Deve retornar informações do seu bot.

### Verificar se Webhook Está Ativo

```bash
curl http://localhost:8021/telegram/webhook-info
```

Verifique se:
- `url` está configurada corretamente
- `pending_update_count` está em 0 (ou baixo)
- Não há erros

### Testar Envio Manual de Mensagem

Para testar se o bot consegue enviar mensagens:

```bash
curl -X POST http://localhost:8021/telegram/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": SEU_CHAT_ID,
    "text": "Mensagem de teste"
  }'
```

**Como obter seu CHAT_ID:**
1. Envie uma mensagem para o bot
2. Acesse: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
3. Procure por `"chat":{"id":123456789}` - esse é seu chat_id

## 📊 Endpoints de Teste

### Status do Serviço
```bash
curl http://localhost:8021/
```

### Health Check
```bash
curl http://localhost:8021/health
```

### Informações do Webhook
```bash
curl http://localhost:8021/telegram/webhook-info
```

### Testar Webhook Manualmente (Simular mensagem do Telegram)

```bash
curl -X POST http://localhost:8021/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 123456,
    "message": {
      "message_id": 1,
      "from": {
        "id": 987654321,
        "is_bot": false,
        "first_name": "Teste",
        "username": "teste_user"
      },
      "chat": {
        "id": 987654321,
        "first_name": "Teste",
        "username": "teste_user",
        "type": "private"
      },
      "date": 1234567890,
      "text": "Mensagem de teste"
    }
  }'
```

## ✅ Checklist de Teste

- [ ] Serviço iniciado sem erros
- [ ] Endpoint `/` retorna status
- [ ] Token do bot configurado corretamente
- [ ] Webhook configurado (via ngrok ou URL pública)
- [ ] Webhook info mostra URL correta
- [ ] Mensagem enviada no Telegram aparece nos logs
- [ ] Bot responde no Telegram (se chatbot estiver rodando)
- [ ] Logs mostram processamento completo

## 🐛 Problemas Comuns

### "TELEGRAM_BOT_TOKEN não configurado"
- Verifique se o arquivo `.env` existe
- Verifique se `TELEGRAM_BOT_TOKEN` está no `.env`
- Reinicie o serviço após editar `.env`

### "Webhook não recebe mensagens"
- Verifique se o ngrok está rodando
- Verifique se a URL do webhook está correta
- Verifique se o serviço está acessível publicamente
- Verifique logs do ngrok para ver requisições recebidas

### "Erro ao enviar mensagem"
- Verifique se o token está correto
- Verifique se o chat_id está correto
- Verifique logs para detalhes do erro

### "Chatbot Service não responde"
- Verifique se o Chatbot Service está rodando na porta 8002
- Verifique `CHATBOT_SERVICE_URL` no `.env`
- O bot ainda deve receber mensagens, mas não conseguirá responder

## 📝 Logs Esperados

Quando tudo estiver funcionando, você verá:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Iniciando Telegram Service...
INFO:     Chatbot Service URL: http://localhost:8002
INFO:     Telegram Service iniciado com sucesso
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8021

# Quando receber uma mensagem:
INFO:     Webhook recebido do Telegram update_id=123456
INFO:     Mensagem recebida do Telegram chat_id=123456789 user_id=987654321 username=usuario text_preview=Olá
INFO:     Enviando mensagem para chatbot user_id=telegram_987654321_123456789 message_preview=Olá
INFO:     Resposta recebida do chatbot user_id=telegram_987654321_123456789 success=True
```

## 🎯 Próximo Passo

Após confirmar que está recebendo mensagens, você pode:
1. Integrar com o Chatbot Service
2. Adicionar comandos do bot (`/start`, `/help`)
3. Melhorar tratamento de erros
4. Adicionar suporte a mídia
