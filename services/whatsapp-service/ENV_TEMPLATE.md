# 🔧 Configuração do .env - WhatsApp Service

## 📝 Copie e cole no arquivo `.env`

```env
# Evolution API Configuration
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=W7F32PCvoLZdi5nng3pfkEOaD3RN9o/YDrIuCmH24OA=
EVOLUTION_INSTANCE_NAME=sitio-multitrem

# AI Service Configuration (Agno AgentOS)
AI_SERVICE_URL=http://localhost:7777

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Server Configuration
PORT=3006
NODE_ENV=development

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=20
RATE_LIMIT_WINDOW_MS=60000

# Message History
MESSAGE_HISTORY_TTL=86400
```

## 🚀 Como aplicar:

### Opção 1: Criar manualmente
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"
# Copie o conteúdo acima e cole em um arquivo chamado .env
```

### Opção 2: Via PowerShell
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"

# Criar o arquivo .env
@"
# Evolution API Configuration
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=W7F32PCvoLZdi5nng3pfkEOaD3RN9o/YDrIuCmH24OA=
EVOLUTION_INSTANCE_NAME=sitio-multitrem

# AI Service Configuration (Agno AgentOS)
AI_SERVICE_URL=http://localhost:7777

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Server Configuration
PORT=3006
NODE_ENV=development

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=20
RATE_LIMIT_WINDOW_MS=60000

# Message History
MESSAGE_HISTORY_TTL=86400
"@ | Out-File -FilePath .env -Encoding UTF8
```

## ✅ Verificar

```powershell
Get-Content .env
```





