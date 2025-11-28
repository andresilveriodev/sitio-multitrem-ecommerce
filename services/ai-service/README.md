# AI Service

Microserviço de Inteligência Artificial do Sítio Multitrem, responsável por gerenciar o assistente de vendas usando OpenAI.

## Tecnologias

- NestJS
- OpenAI (GPT-4o-mini)
- Redis (para histórico de conversas)
- Axios (para comunicação com outros serviços)

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
OPENAI_API_KEY=sua_chave_openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=500
PRODUCT_SERVICE_URL=http://localhost:3001
CART_SERVICE_URL=http://localhost:3002
ORDER_SERVICE_URL=http://localhost:3003
PAYMENT_SERVICE_URL=http://localhost:3004
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
PORT=3007
NODE_ENV=development
```

3. Obtenha uma chave da OpenAI:
   - Acesse https://platform.openai.com/api-keys
   - Crie uma nova chave de API
   - Cole no `.env`

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

- `POST /ai/chat` - Processar mensagem e retornar resposta
- `GET /ai/conversation/:visitorId` - Histórico de conversa

## Porta

O serviço roda na porta **3007** por padrão.

## Funcionalidades

- **Assistente de Vendas**: Responde perguntas sobre produtos, preços e pedidos
- **Function Calling**: Executa ações como adicionar ao carrinho, criar pedidos, gerar pagamentos
- **Histórico de Conversas**: Armazena últimas 20 mensagens no Redis (TTL 24h)
- **Integração com Serviços**: Comunica-se com Product, Cart, Order e Payment services

## Funções Disponíveis

O assistente pode executar as seguintes funções:

1. **list_products** - Lista produtos disponíveis
2. **add_to_cart** - Adiciona produto ao carrinho
3. **remove_from_cart** - Remove produto do carrinho
4. **view_cart** - Mostra carrinho atual
5. **check_delivery_slots** - Verifica dias disponíveis para entrega
6. **create_order** - Cria pedido com dados do cliente
7. **generate_payment_link** - Gera link/QR de pagamento (Pix ou Boleto)

## Exemplo de Uso

```bash
# Enviar mensagem
curl -X POST http://localhost:3007/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "visitorId": "user123",
    "message": "Quais produtos vocês têm?",
    "source": "web"
  }'

# Ver histórico
curl http://localhost:3007/ai/conversation/user123
```

## System Prompt

O assistente é configurado com um system prompt que define:
- Personalidade: simpático, prestativo, conhecedor dos produtos
- Contexto: informações sobre o Sítio Multitrem
- Produtos: lista dinâmica carregada do banco de dados
- Restrições: não responde sobre assuntos não relacionados a vendas
- Comportamento: sempre confirma antes de finalizar pedido

## Histórico de Conversas

O histórico é armazenado no Redis com a chave:
```
ai:conversation:{visitorId}
```

Cada conversa mantém até 20 mensagens com TTL de 24 horas.

