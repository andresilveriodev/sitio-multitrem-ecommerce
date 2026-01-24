# WhatsApp Service

Microserviço de WhatsApp do Sítio Multitrem, responsável por gerenciar comunicação via WhatsApp usando Evolution API.

## Tecnologias

- NestJS
- Evolution API
- Redis (para histórico de conversas)
- Axios (para comunicação com Evolution API e AI Service)

## Instalação

```bash
npm install
```

## Configuração

1. Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Configure as variáveis de ambiente no `.env`:
```env
EVOLUTION_API_URL=http://localhost:8081
EVOLUTION_API_KEY=sua_chave_api
EVOLUTION_INSTANCE=sitio-multitrem
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
AI_SERVICE_URL=http://localhost:3007
AI_ALLOWED_PHONE_NUMBERS=+5562981062311,+55 62 8141-2139
PORT=3006
NODE_ENV=development
```

**Variáveis importantes:**
- `AI_ALLOWED_PHONE_NUMBERS`: Lista de números permitidos para usar IA (separados por vírgula). Números não autorizados recebem mensagem padrão sem IA. Padrão: `+5562981062311,+55 62 8141-2139`

3. Configure a Evolution API:
   - Instale e configure a Evolution API
   - Crie uma instância chamada `sitio-multitrem`
   - Configure o webhook para apontar para `http://seu-servidor:3006/webhooks/whatsapp`

## Executar

### Desenvolvimento
```bash
npm run start:dev
```

### Produção
```bash
npm run build
npm start
```

## Endpoints

- `POST /whatsapp/send` - Enviar mensagem de texto
- `POST /whatsapp/send-buttons` - Enviar mensagem com botões
- `POST /whatsapp/send-list` - Enviar mensagem com lista
- `GET /whatsapp/status` - Status da conexão WhatsApp
- `POST /webhooks/whatsapp` - Receber mensagens do Evolution (webhook)

## Porta

O serviço roda na porta **3006** por padrão.

## Funcionalidades

- Envio de mensagens de texto
- Envio de mensagens com botões interativos
- Envio de mensagens com listas
- Verificação de status da conexão
- Recebimento de mensagens via webhook
- Histórico de conversas no Redis (últimas 20 mensagens, TTL 24h)
- Integração automática com AI Service para respostas inteligentes
- **Controle de acesso à IA**: Apenas números autorizados podem interagir com a IA. Números não autorizados recebem mensagem padrão

## Fluxo de Mensagens Recebidas

1. Evolution API envia webhook para `/webhooks/whatsapp`
2. Serviço armazena mensagem no Redis
3. Serviço encaminha para AI Service
4. AI Service processa e retorna resposta
5. Serviço envia resposta de volta via WhatsApp

## Histórico de Conversas

O histórico é armazenado no Redis com a chave:
```
whatsapp:conversation:{phoneNumber}
```

Cada conversa mantém até 20 mensagens com TTL de 24 horas.

