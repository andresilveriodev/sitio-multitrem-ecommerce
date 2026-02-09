# 🔑 Como Configurar o Token do Telegram Bot

## 📋 Passo a Passo

### 1. Obter o Token do Bot

1. Abra o Telegram e procure por **@BotFather**
2. Envie o comando `/newbot`
3. Siga as instruções:
   - Escolha um nome para o bot (ex: "Meu E-commerce Bot")
   - Escolha um username (deve terminar com `bot`, ex: `meu_ecommerce_bot`)
4. Ao final, o BotFather enviará uma mensagem com o **token**:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
5. **Copie esse token** - você precisará dele!

### 2. Criar o Arquivo .env

No diretório do serviço, crie o arquivo `.env`:

```bash
cd 4_messages_apps_services/telegram_service
cp env.example .env
```

### 3. Editar o Arquivo .env

Abra o arquivo `.env` e substitua `your_telegram_bot_token_here` pelo token que você copiou:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**Exemplo completo do .env:**

```env
# Configurações básicas
DEBUG=false
HOST=0.0.0.0
PORT=8021
LOG_LEVEL=INFO

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_WEBHOOK_URL=https://seu-dominio.com/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=seu_token_secreto_aqui

# Chatbot Service
CHATBOT_SERVICE_URL=http://localhost:8002
CHATBOT_SERVICE_TIMEOUT=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Redis (opcional)
REDIS_URL=redis://localhost:6379/10
```

### 4. Verificar se Está Funcionando

Após iniciar o serviço, você pode testar se o token está correto:

```bash
# Iniciar o serviço
python main.py

# Em outro terminal, testar envio de mensagem
curl -X POST http://localhost:8021/telegram/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": SEU_CHAT_ID,
    "text": "Teste"
  }'
```

## ⚠️ Importante

- **NUNCA compartilhe seu token** publicamente
- **NÃO faça commit** do arquivo `.env` no Git (já está no .gitignore)
- Se o token for exposto, revogue-o no BotFather com `/revoke` e crie um novo

## 🔒 Segurança

O arquivo `.env` já está configurado no `.gitignore` para não ser versionado. Mantenha o token seguro!

## 📝 Localização do Arquivo

```
4_messages_apps_services/telegram_service/
├── .env                    ← AQUI você coloca o token
├── env.example            ← Arquivo de exemplo (não contém token real)
└── config.py              ← Lê o token do .env automaticamente
```
