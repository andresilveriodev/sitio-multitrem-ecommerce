# 🔗 Integração WhatsApp Service + Evolution API

## 📋 Visão Geral

Este documento detalha como o WhatsApp Service se integra com a Evolution API para fornecer comunicação via WhatsApp no e-commerce do Sítio Multitrem.

---

## 🏗️ Arquitetura

```
┌──────────────────┐
│   WhatsApp Web   │
│  (Usuário Final) │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Evolution API   │
│  (Port: 8080)    │
│  - Baileys       │
│  - PostgreSQL    │
│  - Redis         │
└────────┬─────────┘
         │ Webhook
         ↓
┌──────────────────┐
│ WhatsApp Service │
│  (Port: 3006)    │
│  - NestJS        │
│  - Redis Cache   │
└────────┬─────────┘
         │ API Call
         ↓
┌──────────────────┐
│   AI Service     │
│  (Port: 3007)    │
│  - Agno/OpenAI   │
└──────────────────┘
```

---

## 📂 Estrutura de Arquivos

```
services/whatsapp-service/
├── src/
│   ├── whatsapp/
│   │   ├── whatsapp.controller.ts  # Endpoints REST
│   │   ├── whatsapp.service.ts     # Lógica de negócio
│   │   └── dto/
│   │       └── send-message.dto.ts # DTOs
│   ├── webhooks/
│   │   ├── webhooks.controller.ts  # Recebe webhooks da Evolution
│   │   └── webhooks.service.ts     # Processa mensagens recebidas
│   ├── config/
│   │   ├── evolution.config.ts     # Config Evolution API
│   │   └── redis.config.ts         # Config Redis
│   └── utils/
│       ├── message-formatter.ts    # Formatação de mensagens
│       └── rate-limiter.ts         # Rate limiting
├── .env                            # Variáveis de ambiente
└── README.md
```

---

## ⚙️ Configuração

### 1️⃣ Variáveis de Ambiente

Crie/edite `services/whatsapp-service/.env`:

```bash
# Evolution API
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua_api_key_super_secreta_aqui
EVOLUTION_INSTANCE=sitio-multitrem

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# AI Service
AI_SERVICE_URL=http://localhost:3007

# Porta
PORT=3006
NODE_ENV=development

# Rate Limiting
RATE_LIMIT_TTL=60
RATE_LIMIT_MAX=10
```

### 2️⃣ Instalar Dependências

```bash
cd services/whatsapp-service
npm install
```

### 3️⃣ Iniciar o Serviço

```bash
# Desenvolvimento
npm run start:dev

# Produção
npm run build
npm run start
```

---

## 📡 Endpoints Disponíveis

### 1. **POST /whatsapp/send** - Enviar Mensagem de Texto

**Request:**
```json
{
  "phone": "5562999999999",
  "message": "Olá! Como posso ajudar?"
}
```

**Response:**
```json
{
  "success": true,
  "messageId": "3EB0XXXXX",
  "timestamp": 1704067200
}
```

**Exemplo PowerShell:**
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    phone = "5562999999999"
    message = "Olá! Como posso ajudar?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3006/whatsapp/send" -Method Post -Headers $headers -Body $body
```

---

### 2. **POST /whatsapp/send-buttons** - Enviar Mensagem com Botões

**Request:**
```json
{
  "phone": "5562999999999",
  "message": "Escolha uma opção:",
  "buttons": [
    {
      "id": "1",
      "text": "Ver Produtos"
    },
    {
      "id": "2",
      "text": "Meu Carrinho"
    },
    {
      "id": "3",
      "text": "Falar com Atendente"
    }
  ]
}
```

---

### 3. **POST /whatsapp/send-list** - Enviar Mensagem com Lista

**Request:**
```json
{
  "phone": "5562999999999",
  "title": "Nossos Produtos",
  "description": "Selecione um produto:",
  "buttonText": "Ver Produtos",
  "sections": [
    {
      "title": "Hortaliças",
      "rows": [
        {
          "id": "alface",
          "title": "Alface Orgânica",
          "description": "R$ 3,50/unidade"
        },
        {
          "id": "tomate",
          "title": "Tomate Cereja",
          "description": "R$ 8,00/kg"
        }
      ]
    },
    {
      "title": "Ovos",
      "rows": [
        {
          "id": "ovos",
          "title": "Ovos Caipiras",
          "description": "R$ 12,00/dúzia"
        }
      ]
    }
  ]
}
```

---

### 4. **GET /whatsapp/status** - Verificar Status da Conexão

**Response:**
```json
{
  "instance": "sitio-multitrem",
  "state": "open",
  "connected": true
}
```

---

### 5. **POST /webhooks/whatsapp** - Webhook (Evolution API → WhatsApp Service)

**Este endpoint é chamado automaticamente pela Evolution API quando uma mensagem é recebida.**

**Payload recebido:**
```json
{
  "event": "messages.upsert",
  "instance": "sitio-multitrem",
  "data": {
    "key": {
      "remoteJid": "5562999999999@s.whatsapp.net",
      "fromMe": false,
      "id": "3EB0XXXXX"
    },
    "message": {
      "conversation": "Olá, quero comprar alface"
    },
    "messageTimestamp": 1704067200,
    "pushName": "Cliente"
  }
}
```

---

## 🔄 Fluxo de Mensagens

### 📥 Recebendo Mensagens (Webhook)

1. **Usuário envia mensagem** no WhatsApp
2. **Evolution API recebe** via Baileys
3. **Evolution API chama webhook**: `POST http://localhost:3006/webhooks/whatsapp`
4. **WhatsApp Service processa**:
   - Extrai dados da mensagem
   - Armazena no Redis (histórico)
   - Formata para o AI Service
5. **Chama AI Service**: `POST http://localhost:3007/ai/chat`
6. **AI Service responde** com mensagem inteligente
7. **WhatsApp Service envia resposta** via Evolution API
8. **Usuário recebe resposta** no WhatsApp

### 📤 Enviando Mensagens (API Call)

1. **Sistema chama**: `POST http://localhost:3006/whatsapp/send`
2. **WhatsApp Service valida** e formata
3. **Chama Evolution API**: `POST http://localhost:8080/message/sendText/sitio-multitrem`
4. **Evolution API envia** via Baileys
5. **Usuário recebe** no WhatsApp

---

## 💾 Armazenamento de Histórico (Redis)

### Estrutura de Chaves

```
whatsapp:conversation:{phoneNumber}
```

**Exemplo:**
```
whatsapp:conversation:5562999999999
```

### Estrutura de Dados

```json
[
  {
    "role": "user",
    "content": "Olá, quero comprar alface",
    "timestamp": 1704067200
  },
  {
    "role": "assistant",
    "content": "Olá! Temos alface orgânica fresquinha por R$ 3,50. Quantas você gostaria?",
    "timestamp": 1704067205
  }
]
```

### Configurações

- **Limite**: 20 mensagens por conversa
- **TTL**: 24 horas
- **Formato**: JSON Array

---

## 🔧 Código de Integração

### whatsapp.service.ts (Simplificado)

```typescript
import { Injectable } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom } from 'rxjs';

@Injectable()
export class WhatsAppService {
  private readonly evolutionApiUrl: string;
  private readonly evolutionApiKey: string;
  private readonly evolutionInstance: string;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.evolutionApiUrl = this.configService.get('EVOLUTION_API_URL');
    this.evolutionApiKey = this.configService.get('EVOLUTION_API_KEY');
    this.evolutionInstance = this.configService.get('EVOLUTION_INSTANCE');
  }

  async sendTextMessage(phone: string, message: string) {
    const url = `${this.evolutionApiUrl}/message/sendText/${this.evolutionInstance}`;
    
    const payload = {
      number: phone,
      text: message,
    };

    const headers = {
      'Content-Type': 'application/json',
      'apikey': this.evolutionApiKey,
    };

    try {
      const response = await firstValueFrom(
        this.httpService.post(url, payload, { headers })
      );
      return response.data;
    } catch (error) {
      throw new Error(`Erro ao enviar mensagem: ${error.message}`);
    }
  }

  async getConnectionStatus() {
    const url = `${this.evolutionApiUrl}/instance/connectionState/${this.evolutionInstance}`;
    
    const headers = {
      'apikey': this.evolutionApiKey,
    };

    try {
      const response = await firstValueFrom(
        this.httpService.get(url, { headers })
      );
      return response.data;
    } catch (error) {
      throw new Error(`Erro ao verificar status: ${error.message}`);
    }
  }
}
```

---

## 🧪 Testes

### 1. Testar Envio de Mensagem

**PowerShell:**
```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    phone = "5562999999999"
    message = "Teste de integração! 🌿"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3006/whatsapp/send" -Method Post -Headers $headers -Body $body
```

### 2. Testar Status

```powershell
Invoke-RestMethod -Uri "http://localhost:3006/whatsapp/status"
```

### 3. Simular Webhook

```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    event = "messages.upsert"
    instance = "sitio-multitrem"
    data = @{
        key = @{
            remoteJid = "5562999999999@s.whatsapp.net"
            fromMe = $false
        }
        message = @{
            conversation = "Olá, teste!"
        }
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:3006/webhooks/whatsapp" -Method Post -Headers $headers -Body $body
```

---

## 🔍 Troubleshooting

### ❌ Erro: "Evolution API not reachable"

**Solução:**
```powershell
# Verificar se Evolution API está rodando
Invoke-WebRequest -Uri http://localhost:8080

# Verificar logs
cd services/evolution-api
npm run start
```

### ❌ Erro: "Invalid API Key"

**Solução:**
1. Verifique se a API Key no `.env` do WhatsApp Service é a mesma do Evolution API
2. Regenere a API Key se necessário

### ❌ Erro: "Instance not found"

**Solução:**
```powershell
# Listar instâncias
$headers = @{ "apikey" = "sua_api_key" }
Invoke-RestMethod -Uri "http://localhost:8080/instance/fetchInstances" -Headers $headers

# Criar instância se necessário
```

---

## ✅ Checklist de Integração

- [ ] Evolution API rodando (porta 8080)
- [ ] WhatsApp Service rodando (porta 3006)
- [ ] Variáveis de ambiente configuradas
- [ ] Instância criada e conectada
- [ ] Webhook configurado
- [ ] Redis rodando
- [ ] Teste de envio funcionando
- [ ] Webhook recebendo mensagens
- [ ] Histórico sendo salvo no Redis
- [ ] IA respondendo automaticamente

---

**🎉 Integração completa e funcionando!**

**Data de Criação**: Janeiro 2026  
**Versão**: 1.0.0

---

**Desenvolvido com ❤️ para o Sítio Multitrem** 🌿





