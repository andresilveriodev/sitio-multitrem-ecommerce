# Commerce Service

Serviço de processamento de pedidos do e-commerce Sítio Multitrem.

## Objetivo

Este serviço gerencia todo o ciclo de vida dos pedidos do e-commerce:
- Cadastro de produtos (hortaliças e ovos)
- Catálogo e preços (varejo/atacado)
- Recebimento de pedidos (WhatsApp/Telegram/Site)
- Processamento de pedidos (separação → rota → entrega → confirmação)
- Registro de pagamentos (Pix/dinheiro)
- Histórico e auditoria

## Porta

**8002** - Commerce Service

## Estrutura do Banco de Dados

O serviço utiliza 3 schemas no PostgreSQL:

### 1. `commerce` - Domínio do negócio
- `product_category` - Categorias de produtos
- `product` - Produtos
- `price_list` - Listas de preços
- `product_price` - Preços de produtos por lista
- `customer` - Clientes (com campo `price_profile`)
- `customer_address` - Endereços dos clientes (com `delivery_zone_id`)
- `customer_product_price` - Preços específicos por cliente (exceções comerciais)
- `delivery_zone` - Zonas de entrega com valores de frete
- `order` - Pedidos
- `order_item` - Itens dos pedidos
- `payment` - Pagamentos
- `delivery_route` - Rotas de entrega
- `delivery_stop` - Paradas nas rotas
- `audit_log` - Logs de auditoria

### 2. `chatbot` - Conversas e filas
- `channel_account` - Contas de canal (WhatsApp/Telegram)
- `conversation` - Conversas
- `message` - Mensagens
- `intent_rule` - Regras de intenção (whitelist antes de chamar GPT)
- `outbox` - Fila de mensagens para envio

### 3. `ai_management` - Gerenciamento de IA
- Schema já existente (não criado por este serviço)

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente:
```bash
cp env.example .env
# Edite o .env conforme necessário
```

3. Inicialize o banco de dados:
```bash
# Criar schemas
python create_schemas.py

# Criar tabelas
python init_db.py
```

## Execução

```bash
python main.py
```

Ou com uvicorn diretamente:
```bash
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## Endpoints

### Produtos
- `GET /api/v1/products` - Lista produtos
- `GET /api/v1/products/{product_id}` - Busca produto
- `POST /api/v1/products` - Cria produto
- `PUT /api/v1/products/{product_id}` - Atualiza produto
- `GET /api/v1/products/categories` - Lista categorias
- `POST /api/v1/products/categories` - Cria categoria
- `GET /api/v1/products/price-lists` - Lista listas de preços
- `POST /api/v1/products/prices` - Define preço de produto

### Clientes
- `GET /api/v1/customers` - Lista clientes
- `GET /api/v1/customers/{customer_id}` - Busca cliente
- `POST /api/v1/customers` - Cria cliente
- `PUT /api/v1/customers/{customer_id}` - Atualiza cliente
- `GET /api/v1/customers/{customer_id}/addresses` - Lista endereços
- `POST /api/v1/customers/addresses` - Cria endereço

### Pedidos
- `GET /api/v1/orders` - Lista pedidos
- `GET /api/v1/orders/{order_id}` - Busca pedido
- `POST /api/v1/orders` - Cria pedido
- `PUT /api/v1/orders/{order_id}` - Atualiza pedido
- `POST /api/v1/orders/{order_id}/confirm` - Confirma pedido
- `POST /api/v1/orders/{order_id}/cancel` - Cancela pedido

### Pagamentos
- `GET /api/v1/payments` - Lista pagamentos
- `GET /api/v1/payments/{payment_id}` - Busca pagamento
- `POST /api/v1/payments` - Cria pagamento
- `PUT /api/v1/payments/{payment_id}` - Atualiza pagamento
- `POST /api/v1/payments/{payment_id}/mark-paid` - Marca como pago

### Entregas
- `GET /api/v1/deliveries/routes` - Lista rotas
- `GET /api/v1/deliveries/routes/{route_id}` - Busca rota
- `POST /api/v1/deliveries/routes` - Cria rota
- `PUT /api/v1/deliveries/routes/{route_id}` - Atualiza rota
- `PUT /api/v1/deliveries/stops/{stop_id}` - Atualiza parada

## Documentação

A documentação interativa está disponível em:
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`

## Regras de Negócio

### Precificação por Perfil

Cada cliente possui um perfil de preço fixo:
- `RESTAURANTE_HIGH` - Restaurantes recorrentes com volume consistente
  - Item hortaliça: R$ 3,00
  - Palito de alface (3 unidades): R$ 8,00
- `RESTAURANTE_LOW` - Restaurantes de baixo ticket / clientes amigos recorrentes
  - Item hortaliça: R$ 3,50
  - Palito de alface (3 unidades): R$ 9,00
- `VAREJO` - Clientes varejo
  - Item hortaliça: R$ 4,00

### Normalização de Alfaces

O sistema normaliza automaticamente unidades de alface para palitos:
- 1 palito = 3 alfaces
- Exemplo: 10 alfaces → 3 palitos + 1 unidade

### Cálculo de Frete

O frete é calculado baseado em:
1. **Zona de entrega** - Cada endereço pertence a uma zona com valor fixo
2. **Ticket mínimo** - Frete grátis acima de R$ 50,00 (configurável)

### Prioridade de Preços

1. Preço específico do cliente (`customer_product_price`)
2. Preço do perfil (`price_profile`)
3. Preço padrão

## Status dos Pedidos

- `draft` - Rascunho
- `confirmed` - Confirmado
- `separating` - Em separação
- `ready` - Pronto
- `out_for_delivery` - Saindo para entrega
- `delivered` - Entregue
- `canceled` - Cancelado

## Canais de Pedido

- `whatsapp` - WhatsApp
- `telegram` - Telegram
- `site` - Site
- `manual` - Manual

## Métodos de Pagamento

- `pix` - PIX
- `cash` - Dinheiro
- `transfer` - Transferência
- `card` - Cartão

## Status de Pagamento

- `pending` - Pendente
- `paid` - Pago
- `failed` - Falhou
- `refunded` - Reembolsado
