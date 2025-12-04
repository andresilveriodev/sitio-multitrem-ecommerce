# API Gateway

API Gateway centralizado para roteamento de todos os microserviços do Sítio Multitrem.

## Tecnologias

- NestJS
- http-proxy-middleware (para proxy reverso)
- Helmet (segurança)
- @nestjs/throttler (rate limiting)
- Axios (para health checks)

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
PRODUCT_SERVICE_URL=http://localhost:3001
CART_SERVICE_URL=http://localhost:3002
ORDER_SERVICE_URL=http://localhost:3003
PAYMENT_SERVICE_URL=http://localhost:3004
AUTH_SERVICE_URL=http://localhost:3005
WHATSAPP_SERVICE_URL=http://localhost:3006
AI_SERVICE_URL=http://localhost:3007
PORT=8000
NODE_ENV=development
```

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

## Rotas de Proxy

O gateway roteia as seguintes rotas:

- `/api/products/*` → `product-service:3001`
- `/api/cart/*` → `cart-service:3002`
- `/api/orders/*` → `order-service:3003`
- `/api/delivery/*` → `order-service:3003`
- `/api/payments/*` → `payment-service:3004`
- `/api/webhooks/*` → `payment-service:3004`
- `/api/auth/*` → `auth-service:3005`
- `/api/whatsapp/*` → `whatsapp-service:3006`
- `/api/ai/*` → `ai-service:3007`

## Endpoints do Gateway

- `GET /health` - Status do gateway
- `GET /health/services` - Status de todos os serviços

## Porta

O gateway roda na porta **8000** por padrão.

## Funcionalidades

- **Proxy Reverso**: Roteamento automático para os microserviços corretos
- **CORS**: Habilitado para permitir requisições do frontend
- **Helmet**: Headers de segurança
- **Rate Limiting**: 100 requisições por minuto por IP
- **Health Checks**: Monitoramento do status dos serviços
- **Error Handling**: Tratamento padronizado de erros
- **Timeout**: 30 segundos por requisição

## Exemplo de Uso

### Frontend
```typescript
// Todas as requisições vão para o gateway na porta 8000
const response = await fetch('http://localhost:8000/api/products')
```

### Health Check
```bash
# Status do gateway
curl http://localhost:8000/health

# Status de todos os serviços
curl http://localhost:8000/health/services
```

## Segurança

- Headers de segurança via Helmet
- Rate limiting para prevenir abuso
- Validação de requisições
- Timeout para evitar requisições travadas
- Preservação de headers de autenticação

