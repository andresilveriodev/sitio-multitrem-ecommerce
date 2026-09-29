# Documentação de Implementação - Commerce Service

**Data:** 2024  
**Status:** Em desenvolvimento  
**Última atualização:** Implementação inicial completa

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura do Projeto](#estrutura-do-projeto)
3. [Modelos de Dados](#modelos-de-dados)
4. [Regras de Negócio Implementadas](#regras-de-negócio-implementadas)
5. [Serviços Criados](#serviços-criados)
6. [Endpoints API](#endpoints-api)
7. [Próximos Passos](#próximos-passos)
8. [Notas Técnicas](#notas-técnicas)

---

## 🎯 Visão Geral

O **Commerce Service** é o serviço responsável por processar pedidos do e-commerce do Sítio Multitrem. Ele gerencia todo o ciclo de vida dos pedidos, desde a criação até a entrega, aplicando regras de precificação e cálculo de frete.

**Porta:** 8002  
**Base Path:** `/api/v1`  
**Documentação:** `http://localhost:8002/docs`

---

## 📁 Estrutura do Projeto

```
5_commerce/
├── __init__.py
├── main.py                    # Aplicação FastAPI principal
├── config.py                  # Configurações do serviço
├── db_session.py              # Conexão com banco de dados
├── requirements.txt           # Dependências Python
├── env.example                # Exemplo de variáveis de ambiente
├── README.md                  # Documentação geral
├── IMPLEMENTACAO.md          # Este arquivo
├── create_schemas.py          # Script para criar schemas
├── init_db.py                 # Script para inicializar banco
│
├── models/                    # Modelos SQLAlchemy
│   ├── __init__.py
│   ├── commerce.py           # Modelos do schema commerce
│   └── chatbot.py            # Modelos do schema chatbot
│
├── schemas/                   # Schemas Pydantic (DTOs)
│   ├── __init__.py
│   ├── product.py
│   ├── customer.py
│   ├── order.py
│   ├── payment.py
│   ├── delivery.py
│   └── shipping.py
│
├── services/                  # Serviços de negócio
│   ├── __init__.py
│   ├── product_service.py
│   ├── customer_service.py
│   ├── order_service.py
│   ├── payment_service.py
│   ├── delivery_service.py
│   ├── audit_service.py
│   ├── pricing_service.py    # ⭐ Novo: Regras de precificação
│   └── shipping_service.py    # ⭐ Novo: Cálculo de frete
│
└── routes/                    # Rotas FastAPI
    ├── __init__.py
    ├── products.py
    ├── customers.py
    ├── orders.py
    ├── payments.py
    ├── deliveries.py
    └── shipping.py            # ⭐ Novo: Zonas e preços específicos
```

---

## 🗄️ Modelos de Dados

### Schema: `commerce`

#### Tabelas Principais

1. **product_category**
   - Categorias de produtos (Hortaliças, Ovos, Outros)
   - Campos: `id`, `name`, `sort_order`, `created_at`

2. **product**
   - Produtos cadastrados
   - Campos: `id`, `category_id`, `sku`, `name`, `unit`, `active`, `created_at`
   - ⚠️ **Importante:** Produtos devem ser separados:
     - `ALFACE_UN` - Alface unidade
     - `PALITO_ALFACE` - Palito de alface (3 unidades)

3. **price_list**
   - Listas de preços (Padrão, Restaurantes, Promo feira)
   - Campos: `id`, `name`, `active`, `created_at`

4. **product_price**
   - Preços de produtos por lista de preços
   - Campos: `id`, `product_id`, `price_list_id`, `price`, `valid_from`, `valid_to`

5. **customer** ⭐ **ATUALIZADO**
   - Clientes do sistema
   - Campos: `id`, `name`, `phone_e164`, `document`, `price_profile`, `default_price_list_id`, `notes`, `created_at`
   - **Novo campo:** `price_profile` (enum: RESTAURANTE_HIGH, RESTAURANTE_LOW, VAREJO)

6. **customer_address** ⭐ **ATUALIZADO**
   - Endereços dos clientes
   - Campos: `id`, `customer_id`, `delivery_zone_id`, `label`, `street`, `number`, `district`, `city`, `state`, `zip`, `reference`, `lat`, `lng`, `is_default`, `created_at`
   - **Novo campo:** `delivery_zone_id` (FK para delivery_zone)

7. **delivery_zone** ⭐ **NOVO**
   - Zonas de entrega com valores de frete
   - Campos: `id`, `name`, `fee`, `active`, `created_at`
   - Exemplos: "Centro" (R$ 5), "Setor Jaó" (R$ 7), "Senador Canedo" (R$ 10)

8. **customer_product_price** ⭐ **NOVO**
   - Preços específicos por cliente (exceções comerciais)
   - Campos: `id`, `customer_id`, `product_id`, `price`, `created_at`
   - Índice único: `(customer_id, product_id)`

9. **order**
   - Pedidos
   - Campos: `id` (UUID), `customer_id`, `status`, `channel`, `price_list_id`, `delivery_address_id`, `delivery_fee`, `subtotal`, `total`, `notes`, `created_at`, `confirmed_at`, `delivered_at`

10. **order_item**
    - Itens dos pedidos
    - Campos: `id`, `order_id`, `product_id`, `qty`, `unit_price`, `subtotal`, `notes`, `created_at`
    - ⚠️ **Importante:** `unit_price` é salvo e nunca recalculado após confirmação

11. **payment**
    - Pagamentos
    - Campos: `id`, `order_id`, `method`, `status`, `amount`, `paid_at`, `external_ref`, `created_at`

12. **delivery_route**
    - Rotas de entrega
    - Campos: `id`, `date`, `driver_name`, `status`, `notes`, `created_at`

13. **delivery_stop**
    - Paradas nas rotas
    - Campos: `id`, `route_id`, `order_id`, `sequence`, `status`, `delivered_at`, `proof`, `fee_per_stop`, `created_at`

14. **audit_log**
    - Logs de auditoria
    - Campos: `id`, `entity_type`, `entity_id`, `action`, `data`, `created_at`

### Schema: `chatbot`

1. **channel_account** - Contas de canal (WhatsApp/Telegram)
2. **conversation** - Conversas
3. **message** - Mensagens
4. **intent_rule** - Regras de intenção (whitelist antes de chamar GPT)
5. **outbox** - Fila de mensagens para envio

---

## 📐 Regras de Negócio Implementadas

### 1. Precificação por Perfil

Cada cliente possui um **perfil de preço fixo** que nunca muda automaticamente:

#### RESTAURANTE_HIGH
- Item hortaliça: **R$ 3,00**
- Palito de alface (3 unidades): **R$ 8,00**
- Aplicado a: Restaurantes recorrentes com volume consistente

#### RESTAURANTE_LOW
- Item hortaliça: **R$ 3,50**
- Palito de alface (3 unidades): **R$ 9,00**
- Aplicado a: Restaurantes de baixo ticket / clientes amigos recorrentes

#### VAREJO
- Item hortaliça: **R$ 4,00**
- Palitos normalmente não são utilizados

**Implementação:** Tabela hardcoded em `PricingService.PRICE_TABLE`

### 2. Normalização de Alfaces

**Regra:** 1 palito = 3 alfaces

O sistema converte automaticamente unidades de alface para palitos:

- 10 alfaces → 3 palitos + 1 unidade
- 7 alfaces → 2 palitos + 1 unidade
- 3 alfaces → 1 palito
- 2 alfaces → 2 unidades (não converte)

**Exceção:** Se o cliente pedir explicitamente "palitos", não converte.

**Implementação:** Método `PricingService.normalize_alface_units()`

### 3. Prioridade de Preços

Ordem de aplicação de preços:

1. **Preço específico do cliente** (`customer_product_price`) - Exceções comerciais
2. **Preço do perfil** (`customer.price_profile`) - Tabela de preços por perfil
3. **Preço padrão** - Fallback (retorna 0 se não encontrado)

**Implementação:** Método `PricingService.get_product_price()`

### 4. Cálculo de Frete

O frete é calculado no momento da criação do pedido:

#### 4.1 Frete por Zona
- Cada endereço pertence a uma `delivery_zone`
- Cada zona tem um valor fixo de frete
- Exemplo: Centro → R$ 5, Setor Jaó → R$ 7

#### 4.2 Frete Grátis por Ticket Mínimo
- **Valor mínimo:** R$ 50,00 (configurável)
- Se `subtotal >= valor_minimo` → `frete = 0`
- Pode ser ativado/desativado via configuração

**Implementação:** Método `ShippingService.calculate_shipping()`

### 5. Segurança do Sistema

Regras obrigatórias implementadas:

- ✅ Preço **nunca é recalculado** após confirmação do pedido
- ✅ Perfil de cliente **nunca muda automaticamente**
- ✅ Chatbot **nunca altera perfil de preço**
- ✅ Pedido só é confirmado após resposta explícita do cliente

---

## 🔧 Serviços Criados

### 1. ProductService
- Gerenciamento de produtos, categorias e preços
- Métodos: `get_categories()`, `create_product()`, `set_product_price()`, etc.

### 2. CustomerService
- Gerenciamento de clientes e endereços
- Métodos: `get_customers()`, `create_customer()`, `get_customer_by_phone()`, etc.

### 3. OrderService ⭐ **ATUALIZADO**
- Gerenciamento de pedidos
- **Novo:** Aplica regras de precificação na criação
- **Novo:** Normaliza alfaces automaticamente
- **Novo:** Calcula frete baseado em zona e ticket mínimo
- Métodos: `create_order()`, `confirm_order()`, `cancel_order()`, etc.

### 4. PaymentService
- Gerenciamento de pagamentos
- Métodos: `create_payment()`, `mark_as_paid()`, etc.

### 5. DeliveryService
- Gerenciamento de rotas e entregas
- Métodos: `create_route()`, `update_stop()`, etc.

### 6. AuditService
- Logs de auditoria
- Método: `log()`

### 7. PricingService ⭐ **NOVO**
- Aplica regras de precificação
- **Métodos principais:**
  - `get_product_price()` - Obtém preço com prioridade
  - `normalize_alface_units()` - Normaliza alfaces para palitos
  - `calculate_item_price()` - Calcula preço de item com normalização

### 8. ShippingService ⭐ **NOVO**
- Calcula frete
- **Métodos principais:**
  - `calculate_shipping()` - Calcula frete por zona e ticket mínimo
  - `get_delivery_zones()` - Lista zonas de entrega
  - `get_zone_by_name()` - Busca zona por nome

---

## 🌐 Endpoints API

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
- `GET /api/v1/customers/phone/{phone_e164}` - Busca por telefone
- `GET /api/v1/customers/{customer_id}/addresses` - Lista endereços
- `POST /api/v1/customers/addresses` - Cria endereço

### Pedidos
- `GET /api/v1/orders` - Lista pedidos
- `GET /api/v1/orders/{order_id}` - Busca pedido
- `POST /api/v1/orders` - Cria pedido ⭐ **Aplica regras de negócio**
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

### Frete e Preços Específicos ⭐ **NOVO**
- `GET /api/v1/shipping/zones` - Lista zonas de entrega
- `GET /api/v1/shipping/zones/{zone_id}` - Busca zona
- `POST /api/v1/shipping/zones` - Cria zona
- `PUT /api/v1/shipping/zones/{zone_id}` - Atualiza zona
- `GET /api/v1/shipping/customers/{customer_id}/product-prices` - Lista preços específicos
- `POST /api/v1/shipping/customers/product-prices` - Cria preço específico
- `PUT /api/v1/shipping/customers/product-prices/{price_id}` - Atualiza preço específico
- `DELETE /api/v1/shipping/customers/product-prices/{price_id}` - Remove preço específico

---

## 🚀 Próximos Passos

### 1. Inicialização do Banco de Dados

```bash
# Criar schemas
python create_schemas.py

# Criar tabelas
python init_db.py
```

### 2. Configuração Inicial

#### 2.1 Criar Zonas de Entrega
```sql
INSERT INTO commerce.delivery_zone (name, fee, active) VALUES
('Centro', 5.00, true),
('Setor Jaó', 7.00, true),
('Senador Canedo', 10.00, true);
```

#### 2.2 Criar Produtos Separados
```sql
-- Alface unidade
INSERT INTO commerce.product (category_id, sku, name, unit, active) VALUES
(1, 'ALFACE_UN', 'Alface Unidade', 'un', true);

-- Palito de alface
INSERT INTO commerce.product (category_id, sku, name, unit, active) VALUES
(1, 'PALITO_ALFACE', 'Palito de Alface', 'palito', true);
```

#### 2.3 Atribuir Perfis aos Clientes
```sql
-- Exemplo: Atualizar cliente para RESTAURANTE_HIGH
UPDATE commerce.customer 
SET price_profile = 'RESTAURANTE_HIGH' 
WHERE id = 1;
```

### 3. Integração com Chatbot

O chatbot deve:

1. Identificar o cliente (por telefone)
2. Carregar o perfil de preço (`customer.price_profile`)
3. Interpretar o pedido
4. Normalizar alfaces (se necessário)
5. Aplicar preço correto (via `PricingService`)
6. Calcular frete (via `ShippingService`)
7. Enviar resumo ao cliente
8. Aguardar confirmação explícita

**Exemplo de fluxo:**
```
Cliente: "Quero 10 alfaces"
Sistema: 
  - Normaliza: 3 palitos + 1 unidade
  - Aplica preço do perfil
  - Calcula frete
  - Responde: "Pedido: 3 Palitos de alface + 1 Alface unidade. Subtotal: R$ 27,00. Frete: R$ 5,00. Total: R$ 32,00. Confirmar?"
```

### 4. Melhorias Futuras

- [ ] Configuração de frete grátis via banco/config
- [ ] Histórico de mudanças de perfil de preço
- [ ] Dashboard de vendas por perfil
- [ ] Relatórios de precificação
- [ ] Integração com sistema de estoque
- [ ] Webhook para notificações de mudança de status

---

## 📝 Notas Técnicas

### Configurações

**Frete Grátis:**
- Valor mínimo: `ShippingService.FREE_SHIPPING_MINIMUM = Decimal("50.00")`
- Habilitado: `ShippingService.FREE_SHIPPING_ENABLED = True`
- ⚠️ Pode ser movido para banco/config no futuro

**Tabela de Preços:**
- Hardcoded em `PricingService.PRICE_TABLE`
- ⚠️ Considerar mover para banco/config se precisar de flexibilidade

### Enums

**OrderStatus:**
- `draft`, `confirmed`, `separating`, `ready`, `out_for_delivery`, `delivered`, `canceled`

**OrderChannel:**
- `whatsapp`, `telegram`, `site`, `manual`

**PaymentMethod:**
- `pix`, `cash`, `transfer`, `card`

**PaymentStatus:**
- `pending`, `paid`, `failed`, `refunded`

**PriceProfile:** ⭐ **NOVO**
- `RESTAURANTE_HIGH`, `RESTAURANTE_LOW`, `VAREJO`

### Validações Importantes

1. **Preço nunca é recalculado** após confirmação
2. **Perfil de cliente** só muda manualmente
3. **Normalização de alfaces** ocorre antes do cálculo
4. **Frete grátis** só aplica se subtotal >= mínimo

### Dependências

- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- Pydantic 2.5.0
- PostgreSQL (schemas: commerce, chatbot, ai_management)

---

## 🔍 Checklist de Implementação

- [x] Estrutura base do projeto
- [x] Modelos SQLAlchemy (commerce e chatbot)
- [x] Schemas Pydantic
- [x] Serviços de negócio
- [x] Rotas FastAPI
- [x] Campo `price_profile` em Customer
- [x] Tabela `delivery_zone`
- [x] Tabela `customer_product_price`
- [x] Campo `delivery_zone_id` em CustomerAddress
- [x] Serviço de precificação (PricingService)
- [x] Serviço de frete (ShippingService)
- [x] Aplicação de regras em OrderService
- [x] Normalização de alfaces
- [x] Rotas para zonas e preços específicos
- [x] Documentação

---

## 📞 Contato e Suporte

Para dúvidas ou problemas:
1. Consultar este documento
2. Verificar logs do serviço
3. Consultar documentação Swagger: `http://localhost:8002/docs`

---

**Última atualização:** Implementação inicial completa com regras de negócio de precificação e frete.
