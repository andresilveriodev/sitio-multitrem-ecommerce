# Order Service

Microserviço de pedidos e entregas do Sítio Multitrem, responsável por gerenciar pedidos e slots de entrega usando PostgreSQL.

## Tecnologias

- NestJS
- TypeORM
- PostgreSQL
- Axios (para comunicação com Cart Service)

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
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_DATABASE=sitio_multitrem
CART_SERVICE_URL=http://localhost:3002
PORT=3003
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

### Orders
- `POST /orders` - Criar pedido
- `GET /orders/:id` - Buscar pedido por ID
- `GET /orders/visitor/:visitorId` - Pedidos do visitante
- `PUT /orders/:id/status` - Atualizar status do pedido
- `PUT /orders/:id/payment-status` - Atualizar status de pagamento

### Delivery
- `GET /delivery/slots` - Slots disponíveis (próximos 14 dias)
- `GET /delivery/slots/:date` - Verificar disponibilidade de data

## Porta

O serviço roda na porta **3003** por padrão.

## Entidades

- **Order**: Pedido com informações do cliente e entrega
- **OrderItem**: Itens do pedido
- **DeliverySlot**: Slots de entrega (qua, qui, sex, sab - manhã/tarde)

## Funcionalidades

- Criação de pedidos a partir do carrinho
- Gerenciamento de slots de entrega
- Validação de disponibilidade
- Integração com Cart Service
- Limpeza automática do carrinho após criação do pedido


