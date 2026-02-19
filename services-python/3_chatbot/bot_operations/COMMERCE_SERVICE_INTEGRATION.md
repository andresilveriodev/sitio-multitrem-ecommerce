# Integração com o Commerce Service

Este documento descreve a integração do Chatbot Service com o Commerce Service.

## Visão Geral

O Chatbot Service foi integrado com o Commerce Service (porta 8002) para gerenciar produtos e pedidos do e-commerce. Todas as operações de CRUD de produtos e pedidos agora são realizadas através do Commerce Service, em vez de acessar o banco de dados diretamente.

## Arquitetura

### Componentes

1. **`services/commerce_client.py`** - Cliente HTTP para comunicação com o Commerce Service
   - Gerencia todas as requisições HTTP para os endpoints do Commerce Service
   - Trata erros e timeouts
   - Suporta todos os endpoints: produtos, pedidos, clientes, pagamentos, entregas

2. **`services/commerce_integration.py`** - Serviço de integração
   - Adapta modelos do chatbot para modelos do Commerce Service
   - Mapeia status entre os dois serviços
   - Fornece interface unificada para os serviços do chatbot

3. **`services/order_service.py`** - Serviço de pedidos (atualizado)
   - Agora usa `commerce_integration` em vez de acessar o banco diretamente
   - Mantém a mesma interface para compatibilidade com código existente

4. **`services/product_service.py`** - Serviço de produtos (atualizado)
   - Agora usa `commerce_integration` em vez de acessar o banco diretamente
   - Mantém a mesma interface para compatibilidade com código existente

## Configuração

### Variáveis de Ambiente

Adicione ao `.env`:

```bash
# Commerce Service (processamento de pedidos do e-commerce)
COMMERCE_SERVICE_URL=http://localhost:8002
COMMERCE_SERVICE_TIMEOUT=30
```

### Configuração no `config.py`

As configurações são carregadas automaticamente via `pydantic-settings`:

```python
COMMERCE_SERVICE_URL: str = "http://localhost:8002"
COMMERCE_SERVICE_TIMEOUT: int = 30
```

## Mapeamento de Status

### Status de Pedidos

O Commerce Service usa status diferentes do chatbot. O mapeamento é feito automaticamente:

| Commerce Service | Chatbot Service |
|-----------------|-----------------|
| `draft` | `pending` |
| `confirmed` | `confirmed` |
| `separating` | `processing` |
| `ready` | `processing` |
| `out_for_delivery` | `shipped` |
| `delivered` | `delivered` |
| `canceled` | `cancelled` |

## Endpoints Utilizados

### Produtos

- `GET /api/v1/products` - Lista produtos
- `GET /api/v1/products/{product_id}` - Busca produto
- `POST /api/v1/products` - Cria produto
- `PUT /api/v1/products/{product_id}` - Atualiza produto
- `GET /api/v1/products/categories` - Lista categorias
- `POST /api/v1/products/categories` - Cria categoria

### Pedidos

- `GET /api/v1/orders` - Lista pedidos
- `GET /api/v1/orders/{order_id}` - Busca pedido
- `POST /api/v1/orders` - Cria pedido
- `PUT /api/v1/orders/{order_id}` - Atualiza pedido
- `POST /api/v1/orders/{order_id}/confirm` - Confirma pedido
- `POST /api/v1/orders/{order_id}/cancel` - Cancela pedido

### Clientes

- `GET /api/v1/customers` - Lista clientes
- `GET /api/v1/customers/{customer_id}` - Busca cliente
- `POST /api/v1/customers` - Cria cliente
- `PUT /api/v1/customers/{customer_id}` - Atualiza cliente
- `GET /api/v1/customers/{customer_id}/addresses` - Lista endereços
- `POST /api/v1/customers/addresses` - Cria endereço

### Pagamentos

- `GET /api/v1/payments` - Lista pagamentos
- `GET /api/v1/payments/{payment_id}` - Busca pagamento
- `POST /api/v1/payments` - Cria pagamento
- `POST /api/v1/payments/{payment_id}/mark-paid` - Marca como pago

### Entregas

- `GET /api/v1/deliveries/routes` - Lista rotas
- `GET /api/v1/deliveries/routes/{route_id}` - Busca rota
- `POST /api/v1/deliveries/routes` - Cria rota
- `PUT /api/v1/deliveries/stops/{stop_id}` - Atualiza parada

## Uso

### Exemplo: Criar Produto

```python
from services.product_service import product_service
from models.product_models import ProductCreate

product_data = ProductCreate(
    name="Alface",
    description="Alface fresca",
    price=4.00,
    stock_quantity=100,
    category="Hortaliças"
)

product = await product_service.create_product(product_data, user_id="123")
```

### Exemplo: Criar Pedido

```python
from services.order_service import order_service
from models.order_models import OrderCreate, OrderItemCreate

order_data = OrderCreate(
    customer_name="João Silva",
    customer_phone="(11) 99999-9999",
    items=[
        OrderItemCreate(product_id=1, quantity=2),
        OrderItemCreate(product_id=3, quantity=1)
    ],
    payment_method="pix"
)

order = await order_service.create_order(order_data, customer_id="456", user_id="123")
```

## Tratamento de Erros

O cliente HTTP trata automaticamente:
- Erros HTTP (404, 500, etc.)
- Erros de conexão
- Timeouts

Todos os erros são logados com `structlog` e propagados para o código chamador.

## Compatibilidade

A integração mantém a mesma interface dos serviços originais (`order_service` e `product_service`), garantindo que o código existente continue funcionando sem modificações.

## Notas Importantes

1. **Filtro por `user_id`**: O Commerce Service pode não suportar filtro direto por `user_id` na listagem de produtos. Nesse caso, o filtro é aplicado localmente após buscar do Commerce Service.

2. **Criação de Clientes**: O Commerce Service gerencia clientes separadamente. O chatbot pode precisar criar ou buscar clientes antes de criar pedidos.

3. **Cálculo de Preços**: O Commerce Service calcula preços automaticamente baseado em:
   - Perfil de preço do cliente (`price_profile`)
   - Preços específicos por cliente
   - Listas de preços (varejo/atacado)

4. **Cálculo de Frete**: O Commerce Service calcula frete baseado em:
   - Zona de entrega do endereço
   - Ticket mínimo (frete grátis acima de R$ 50,00)

5. **Normalização de Alfaces**: O Commerce Service normaliza automaticamente unidades de alface para palitos (1 palito = 3 alfaces).

## Próximos Passos

- [ ] Implementar cache de produtos para reduzir chamadas ao Commerce Service
- [ ] Adicionar retry automático em caso de falhas temporárias
- [ ] Implementar webhooks para notificações do Commerce Service
- [ ] Adicionar métricas de performance da integração
