# 🔄 Mudanças: Webhook → Polling

## ✅ O que foi modificado

A implementação foi alterada de **webhook** para **polling** (getUpdates). Agora o serviço busca mensagens ativamente ao invés de receber via webhook.

## 📝 Arquivos Modificados

### 1. Novo arquivo: `services/polling_service.py`
- Serviço que gerencia o loop de polling
- Busca atualizações periodicamente usando `getUpdates`
- Remove webhooks automaticamente ao iniciar
- Gerencia offset para não processar mensagens duplicadas

### 2. Modificado: `services/telegram_service.py`
- Adicionado método `get_updates()` para buscar atualizações
- Adicionado método `delete_webhook()` para remover webhooks
- Mantidos métodos de envio de mensagens

### 3. Modificado: `app.py`
- Inicia `PollingService` no startup
- Para polling no shutdown
- Injeta serviços nos routers

### 4. Modificado: `routers/telegram_router.py`
- Removidos endpoints de webhook (`/webhook`, `/set-webhook`, `/webhook-info`)
- Adicionado endpoint `/polling-status` para verificar status
- Mantido endpoint `/send-message` para testes

### 5. Atualizado: `README.md`
- Documentação atualizada para polling
- Removidas referências a webhook/ngrok
- Adicionadas instruções de uso com polling

## 🎯 Como Funciona Agora

1. **Serviço inicia** → Remove webhook se existir
2. **Inicia loop de polling** → Busca atualizações a cada segundo
3. **Quando há mensagens** → Processa e encaminha para Chatbot
4. **Envia resposta** → De volta para o Telegram
5. **Repete continuamente**

## 🚀 Vantagens

- ✅ **Não precisa de URL pública**
- ✅ **Não precisa de HTTPS**
- ✅ **Funciona em localhost**
- ✅ **Não precisa ngrok**
- ✅ **Configuração mais simples**

## ⚠️ Importante

- O serviço **remove automaticamente** qualquer webhook ao iniciar
- Polling e webhook **não podem coexistir**
- O serviço busca mensagens **continuamente** (usa recursos)

## 🔄 Reiniciar o Serviço

Após as mudanças, **reinicie o serviço**:

```bash
# Parar o serviço atual (Ctrl+C)
# Depois iniciar novamente:
python main.py
```

Você deve ver nos logs:
```
INFO: Iniciando Telegram Service...
INFO: Removendo webhook existente (polling e webhook não podem coexistir)
INFO: Iniciando loop de polling (intervalo: 1s, timeout: 10s)
INFO: Telegram Service iniciado com sucesso (modo polling)
```

## ✅ Testar

1. Reinicie o serviço
2. Envie uma mensagem no Telegram
3. Verifique os logs - deve aparecer:
   ```
   INFO: Recebidas 1 atualização(ões)
   INFO: Mensagem recebida do Telegram...
   ```

## 📊 Verificar Status

```bash
# Status do polling
curl http://localhost:8021/telegram/polling-status

# Health check
curl http://localhost:8021/health
```
