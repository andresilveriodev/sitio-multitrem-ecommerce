# Payment Service

Microserviço de pagamentos do Sítio Multitrem, responsável por processar pagamentos via Mercado Pago (Pix e Boleto).

## Tecnologias

- NestJS
- Mercado Pago SDK
- TypeORM
- PostgreSQL
- Axios (para comunicação com Order Service)

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
MERCADO_PAGO_ACCESS_TOKEN=your_access_token_here
MERCADO_PAGO_PUBLIC_KEY=your_public_key_here
ORDER_SERVICE_URL=http://localhost:3003
DB_HOST=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=postgres
DB_DATABASE=sitio_multitrem
PORT=3004
NODE_ENV=development
```

3. Obtenha suas credenciais do Mercado Pago:
   - Acesse: https://www.mercadopago.com.br/developers
   - Crie uma aplicação
   - Copie o Access Token e Public Key

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

### Payments
- `POST /payments/pix` - Gerar pagamento Pix
- `POST /payments/boleto` - Gerar boleto
- `GET /payments/:id` - Buscar pagamento por ID
- `GET /payments/order/:orderId` - Pagamento do pedido

### Webhooks
- `POST /webhooks/mercadopago` - Receber notificações do Mercado Pago

## Porta

O serviço roda na porta **3004** por padrão.

## Funcionalidades

- Geração de pagamentos Pix com QR Code
- Geração de boletos bancários
- Webhook para receber notificações do Mercado Pago
- Atualização automática do status do pedido quando pagamento é aprovado
- Integração com Order Service

## Webhook

Configure a URL do webhook no painel do Mercado Pago:
```
https://seu-dominio.com/webhooks/mercadopago
```

O webhook processa automaticamente:
- Atualização de status do pagamento
- Notificação de pagamento aprovado
- Atualização do pedido no Order Service


