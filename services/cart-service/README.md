# Cart Service

Microserviço de carrinho do Sítio Multitrem, responsável por gerenciar carrinhos de compras usando Redis.

## Tecnologias

- NestJS
- Redis (ioredis)
- TypeScript
- Axios (para comunicação com Product Service)

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
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
PRODUCT_SERVICE_URL=http://localhost:3001
PORT=3002
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

## Endpoints

- `GET /cart/:visitorId` - Retorna carrinho completo
- `POST /cart/:visitorId/items` - Adicionar item ao carrinho
- `PUT /cart/:visitorId/items/:productId` - Atualizar quantidade de um item
- `DELETE /cart/:visitorId/items/:productId` - Remover item do carrinho
- `DELETE /cart/:visitorId` - Limpar carrinho

## Porta

O serviço roda na porta **3002** por padrão.

## Redis

O carrinho é armazenado no Redis com:
- Key: `cart:{visitorId}`
- TTL: 24 horas
- Formato: JSON com estrutura do Cart


