# 📱 Telegram Service - E-commerce

Serviço de integração com Telegram Bot que recebe mensagens dos usuários via **polling** e as encaminha para o Chatbot Service processar.

## 🎯 Funcionalidades

- ✅ Busca mensagens do Telegram via polling (getUpdates)
- ✅ Não requer URL pública ou webhook
- ✅ Encaminha mensagens para o Chatbot Service
- ✅ Envia respostas do chatbot de volta para o Telegram
- ✅ Suporte a callback queries (botões inline)
- ✅ Indicadores de digitação
- ✅ Tratamento de erros robusto
- ✅ Long polling para eficiência

## 🏗️ Arquitetura

```
Telegram → Telegram Service (Polling) → Chatbot Service (Porta 8002) → AI Service
                ↓
         Resposta para Telegram
```

## 📋 Pré-requisitos

1. **Bot do Telegram criado**
   - Criar bot através do [@BotFather](https://t.me/botfather)
   - Obter o token do bot

2. **Token configurado**
   - Adicionar `TELEGRAM_BOT_TOKEN` no arquivo `.env`

## 🚀 Instalação

### 1. Instalar dependências

```bash
cd 4_messages_apps_services/telegram_service
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp env.example .env
```

Editar `.env` com suas configurações:

```env
# Token do bot do Telegram (OBRIGATÓRIO)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# URL do Chatbot Service
CHATBOT_SERVICE_URL=http://localhost:8002
CHATBOT_SERVICE_TIMEOUT=30
```

### 3. Executar o serviço

```bash
python main.py
```

Ou com uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8021 --reload
```

## 🔄 Como Funciona (Polling)

O serviço usa **polling** ao invés de webhook:

1. **Serviço inicia** e remove qualquer webhook existente
2. **Loop de polling** busca atualizações periodicamente usando `getUpdates`
3. **Quando há mensagens**, processa e encaminha para o Chatbot Service
4. **Envia resposta** de volta para o Telegram

### Vantagens do Polling

- ✅ Não precisa de URL pública
- ✅ Não precisa de HTTPS
- ✅ Funciona em desenvolvimento local
- ✅ Não precisa configurar ngrok ou similar
- ✅ Mais simples de configurar

### Desvantagens

- ⚠️ Usa mais recursos (busca constante)
- ⚠️ Pode ter pequeno delay (até timeout do long polling)

## 📡 Endpoints

### `GET /`
Status do serviço

### `GET /health`
Health check com status do polling

### `GET /telegram/polling-status`
Status detalhado do serviço de polling

### `POST /telegram/send-message`
Envia mensagem via Telegram (uso administrativo/teste)

**Body:**
```json
{
  "chat_id": 123456789,
  "text": "Mensagem de teste"
}
```

## 🔄 Fluxo de Mensagens

1. **Serviço busca atualizações** via `getUpdates` (long polling)
2. **Telegram retorna mensagens** quando há novas
3. **Telegram Service processa** a atualização
4. **Envia indicador de digitação** para o usuário
5. **Chama Chatbot Service** com a mensagem
6. **Recebe resposta** do chatbot
7. **Envia resposta** de volta para o Telegram
8. **Repete o processo** continuamente

## 🧪 Testes

### Verificar se está funcionando

```bash
# Status do serviço
curl http://localhost:8021/

# Status do polling
curl http://localhost:8021/telegram/polling-status
```

### Enviar mensagem de teste

1. Abra o Telegram
2. Procure pelo seu bot
3. Envie uma mensagem
4. Verifique os logs do serviço

Você deve ver:
```
INFO: Recebidas 1 atualização(ões)
INFO: Mensagem recebida do Telegram chat_id=... user_id=... text_preview=...
INFO: Enviando mensagem para chatbot...
INFO: Resposta recebida do chatbot...
```

## 📝 Logs

O serviço usa `structlog` para logging estruturado. Logs incluem:
- Início do polling
- Mensagens recebidas
- Respostas enviadas
- Erros e exceções
- Chamadas ao Chatbot Service

## 🐛 Troubleshooting

### Mensagens não chegam

1. **Verificar token:**
   ```bash
   curl "https://api.telegram.org/bot<SEU_TOKEN>/getMe"
   ```

2. **Verificar status do polling:**
   ```bash
   curl http://localhost:8021/telegram/polling-status
   ```

3. **Verificar logs do serviço** - deve mostrar "Iniciando loop de polling"

4. **Verificar se há webhook configurado:**
   - O serviço remove webhooks automaticamente ao iniciar
   - Se houver webhook, polling não funcionará

### Erro ao enviar mensagem

- Verificar se `TELEGRAM_BOT_TOKEN` está correto
- Verificar se o bot tem permissões para enviar mensagens
- Verificar logs para detalhes do erro

### Chatbot Service não responde

- Verificar se o Chatbot Service está rodando na porta 8002
- Verificar `CHATBOT_SERVICE_URL` no `.env`
- O bot ainda deve receber mensagens, mas não conseguirá responder

## ⚙️ Configurações Avançadas

### Ajustar intervalo de polling

No arquivo `services/polling_service.py`, você pode ajustar:

```python
self.polling_interval = 1  # Segundos entre cada poll
self.timeout = 10  # Timeout para long polling (segundos)
```

**Recomendações:**
- `timeout`: 10-60 segundos (long polling)
- `polling_interval`: 1 segundo (mínimo recomendado)

## 📚 Documentação Adicional

- [Telegram Bot API - getUpdates](https://core.telegram.org/bots/api#getupdates)
- [Chatbot Service README](../../3_chatbot_service/README.md)

## 🎯 Próximos Passos

- [ ] Suporte a mídia (fotos, documentos)
- [ ] Comandos do bot (`/start`, `/help`, etc.)
- [ ] Teclados inline personalizados
- [ ] Rate limiting por usuário
- [ ] Cache de respostas frequentes
