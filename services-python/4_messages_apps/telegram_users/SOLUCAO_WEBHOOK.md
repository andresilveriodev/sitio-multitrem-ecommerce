# 🔧 Solução: Mensagens do Telegram Não Chegam ao Serviço

## 🎯 Problema

Você está enviando mensagens pelo Telegram, mas elas não estão chegando no serviço.

## 🔍 Causa Principal

O **webhook não está configurado** ou **não está acessível publicamente**. O Telegram precisa de uma URL pública com HTTPS para enviar mensagens.

## ✅ Solução Passo a Passo

### 1. Verificar Status Atual

Execute o script de verificação:

```bash
cd 4_messages_apps_services/telegram_service
python verificar_webhook.py
```

Este script vai:
- ✅ Verificar se o token está configurado
- ✅ Verificar se o serviço está rodando
- ✅ Mostrar o status do webhook
- ✅ Identificar problemas

### 2. Configurar Webhook (Desenvolvimento Local)

Para desenvolvimento local, você precisa expor o serviço publicamente usando **ngrok**:

#### 2.1. Instalar ngrok

- Windows: `choco install ngrok` ou baixe em https://ngrok.com/download
- Linux/Mac: `brew install ngrok` ou baixe do site

#### 2.2. Iniciar ngrok

Em um terminal separado:

```bash
ngrok http 8021
```

Você verá algo como:
```
Forwarding  https://abc123def456.ngrok-free.app -> http://localhost:8021
```

**Copie a URL HTTPS** (ex: `https://abc123def456.ngrok-free.app`)

#### 2.3. Configurar Webhook

**Opção A: Via Script (Recomendado)**

Execute o script e quando pedir a URL, cole a URL do ngrok:
```bash
python verificar_webhook.py
```

**Opção B: Via API do Serviço**

```bash
curl -X POST http://localhost:8021/telegram/set-webhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://SUA_URL_NGROK.ngrok-free.app/telegram/webhook"}'
```

**Opção C: Manualmente via Telegram API**

```bash
curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://SUA_URL_NGROK.ngrok-free.app/telegram/webhook"}'
```

### 3. Verificar se Funcionou

```bash
# Verificar informações do webhook
python verificar_webhook.py

# OU via API
curl http://localhost:8021/telegram/webhook-info
```

Deve mostrar:
- ✅ URL configurada corretamente
- ✅ 0 updates pendentes (ou baixo)
- ✅ Sem erros

### 4. Testar

1. Envie uma mensagem para o bot no Telegram
2. Verifique os logs do serviço - deve aparecer:
   ```
   INFO: === WEBHOOK RECEBIDO ===
   INFO: Webhook recebido do Telegram update_id=...
   INFO: Mensagem recebida do Telegram...
   ```

## 🐛 Problemas Comuns e Soluções

### Problema 1: "Webhook não configurado"

**Sintoma:** `verificar_webhook.py` mostra "Webhook não está configurado"

**Solução:** Configure o webhook seguindo o passo 2 acima.

### Problema 2: "Webhook aponta para localhost"

**Sintoma:** Webhook configurado como `http://localhost:8021/telegram/webhook`

**Solução:** O Telegram não consegue acessar localhost. Use ngrok ou uma URL pública.

### Problema 3: "Erro: connection refused" ou "timeout"

**Sintoma:** Webhook configurado mas Telegram não consegue acessar

**Soluções:**
- Verifique se o serviço está rodando na porta 8021
- Verifique se o ngrok está rodando
- Verifique se a URL do webhook está correta
- Verifique firewall/antivírus

### Problema 4: "Updates pendentes" alto

**Sintoma:** `pending_update_count` > 0

**Solução:**
- O webhook pode estar configurado mas não está processando
- Verifique logs do serviço
- Teste o webhook manualmente (veja abaixo)

### Problema 5: Webhook recebe mas não processa

**Sintoma:** Logs mostram "WEBHOOK RECEBIDO" mas não processa a mensagem

**Solução:**
- Verifique se o Chatbot Service está rodando (porta 8002)
- Verifique logs para erros
- Teste o endpoint `/telegram/webhook` manualmente

## 🧪 Teste Manual do Webhook

Para testar se o webhook está funcionando, simule uma mensagem:

```bash
python test_simple.py
```

Ou via curl:

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
        "type": "private"
      },
      "date": 1234567890,
      "text": "Teste"
    }
  }'
```

Se funcionar, você verá nos logs:
```
INFO: === WEBHOOK RECEBIDO ===
INFO: Webhook recebido do Telegram update_id=123456
```

## 📋 Checklist de Verificação

Execute este checklist:

- [ ] Token do bot configurado no `.env`
- [ ] Serviço rodando na porta 8021
- [ ] ngrok rodando e expondo a porta 8021
- [ ] Webhook configurado com URL do ngrok
- [ ] URL do webhook termina com `/telegram/webhook`
- [ ] URL do webhook usa HTTPS (não HTTP)
- [ ] `verificar_webhook.py` mostra webhook configurado
- [ ] Teste manual funciona (`test_simple.py`)
- [ ] Mensagem no Telegram aparece nos logs

## 🚀 Comandos Rápidos

```bash
# 1. Verificar tudo
python verificar_webhook.py

# 2. Testar webhook localmente
python test_simple.py

# 3. Ver informações do webhook
curl http://localhost:8021/telegram/webhook-info

# 4. Ver updates pendentes do Telegram
curl "https://api.telegram.org/bot<SEU_TOKEN>/getUpdates"
```

## 💡 Dica Importante

**Para produção**, você precisa:
- URL pública com HTTPS (não ngrok)
- Domínio próprio
- Certificado SSL válido
- Serviço sempre online

**Para desenvolvimento**, ngrok é suficiente, mas:
- URL muda a cada reinício (plano gratuito)
- Pode ter limites de requisições
- Não é recomendado para produção

## 📞 Ainda Não Funciona?

Se após seguir todos os passos ainda não funcionar:

1. Execute `python verificar_webhook.py` e compartilhe a saída
2. Verifique os logs do serviço quando enviar mensagem
3. Verifique os logs do ngrok (se usando)
4. Teste o webhook manualmente com `test_simple.py`
