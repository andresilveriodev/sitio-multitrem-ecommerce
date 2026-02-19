# 📦 Comandos de Pedidos no Telegram

Este documento descreve os comandos criados para processar pedidos de clientes via Telegram.

## 🎯 Visão Geral

O sistema agora permite processar pedidos de clientes através de comandos no Telegram. Os comandos estão integrados ao sistema de comandos existente e seguem os mesmos padrões de segurança e permissões.

## 📋 Comandos Disponíveis

### 1. **Listar Pedidos** (`list_orders`)

Lista pedidos com filtros opcionais.

**Permissão necessária:** `view_orders`

**Parâmetros:**
- `status` (opcional): Filtrar por status (pending, confirmed, processing, shipped, delivered, cancelled, rejected)
- `customer_id` (opcional): Filtrar por ID do cliente
- `limit` (opcional): Limite de resultados (padrão: 10)

**Exemplos de uso:**
```
Liste os pedidos pendentes
Mostre os pedidos
Pedidos com status pending
list orders status=pending limit=20
```

**Aliases:** `pedidos`, `orders`, `listar pedidos`, `ver pedidos`

---

### 2. **Ver Pedido** (`show_order`)

Exibe detalhes completos de um pedido específico.

**Permissão necessária:** `view_orders`

**Parâmetros:**
- `order_id` (opcional): ID do pedido
- `order_number` (opcional): Número do pedido (ex: ORD-20240101-ABC12)

**Exemplos de uso:**
```
Mostre o pedido 123
Detalhes do pedido ORD-20240101-ABC12
show order 123
```

**Aliases:** `pedido`, `order`, `ver pedido`, `detalhes pedido`

**Resposta inclui:**
- Informações do cliente
- Endereço de entrega
- Itens do pedido com quantidades e preços
- Valores (subtotal, frete, total)
- Status do pedido e pagamento
- Observações

---

### 3. **Aprovar Pedido** (`approve_order`)

Aprova um pedido, mudando seu status para `CONFIRMED`.

**Permissão necessária:** `process_orders`  
**Requer confirmação:** Sim

**Parâmetros:**
- `order_id` (opcional): ID do pedido
- `order_number` (opcional): Número do pedido
- `admin_notes` (opcional): Notas administrativas

**Exemplos de uso:**
```
Aprove o pedido 123
Aprovar pedido ORD-20240101-ABC12
approve order 123
```

**Aliases:** `aprovar`, `approve`, `aprovar pedido`

---

### 4. **Rejeitar Pedido** (`reject_order`)

Rejeita um pedido, mudando seu status para `REJECTED` e devolvendo os produtos ao estoque.

**Permissão necessária:** `process_orders`  
**Requer confirmação:** Sim

**Parâmetros:**
- `order_id` (opcional): ID do pedido
- `order_number` (opcional): Número do pedido
- `admin_notes` (opcional): Motivo da rejeição

**Exemplos de uso:**
```
Rejeite o pedido 123
Rejeitar pedido ORD-20240101-ABC12
reject order 123 motivo='Estoque insuficiente'
```

**Aliases:** `rejeitar`, `reject`, `rejeitar pedido`

**Importante:** Ao rejeitar um pedido, os produtos são automaticamente devolvidos ao estoque.

---

### 5. **Atualizar Status do Pedido** (`update_order_status`)

Atualiza o status de um pedido para qualquer status válido.

**Permissão necessária:** `process_orders`  
**Requer confirmação:** Sim

**Parâmetros:**
- `order_id` (opcional): ID do pedido
- `order_number` (opcional): Número do pedido
- `status` (obrigatório): Novo status (pending, confirmed, processing, shipped, delivered, cancelled, rejected)
- `admin_notes` (opcional): Notas administrativas

**Exemplos de uso:**
```
Atualize o status do pedido 123 para shipped
Mudar status do pedido ORD-20240101-ABC12 para processing
update order status 123 status=shipped
```

**Aliases:** `atualizar status`, `update status`, `mudar status`

**Status disponíveis:**
- `pending`: Aguardando processamento
- `confirmed`: Confirmado
- `processing`: Em processamento
- `shipped`: Enviado
- `delivered`: Entregue
- `cancelled`: Cancelado
- `rejected`: Rejeitado

---

## 🔐 Permissões

### Níveis de Permissão

- **BASIC**: Pode visualizar pedidos (`view_orders`)
- **PREMIUM**: Pode visualizar e processar pedidos (`view_orders`, `process_orders`)
- **TRADER**: Pode visualizar e processar pedidos (`view_orders`, `process_orders`)
- **PROFESSIONAL**: Pode visualizar e processar pedidos (`view_orders`, `process_orders`)
- **ADMIN**: Pode visualizar e processar pedidos (`view_orders`, `process_orders`)

---

## 📊 Estrutura de Dados

### Modelo de Pedido

```python
{
    "id": 1,
    "order_number": "ORD-20240101-ABC12",
    "customer_id": "123456789",
    "customer_name": "João Silva",
    "customer_phone": "(11) 99999-9999",
    "customer_email": "joao@example.com",
    "shipping_address": "Rua Exemplo, 123",
    "shipping_city": "São Paulo",
    "shipping_state": "SP",
    "shipping_zip": "01234-567",
    "subtotal": 199.90,
    "shipping_cost": 15.00,
    "total": 214.90,
    "status": "pending",
    "payment_status": "pending",
    "payment_method": "pix",
    "items": [
        {
            "id": 1,
            "product_id": 1,
            "product_name": "Produto Exemplo",
            "product_sku": "PROD-001",
            "quantity": 2,
            "unit_price": 99.95,
            "total_price": 199.90
        }
    ],
    "created_at": "2024-01-01T10:00:00",
    "updated_at": "2024-01-01T10:00:00"
}
```

---

## 🔄 Fluxo de Processamento

1. **Cliente faz pedido** → Status: `PENDING`
2. **Admin visualiza pedido** → Comando: `show_order`
3. **Admin aprova pedido** → Comando: `approve_order` → Status: `CONFIRMED`
4. **Admin atualiza status** → Comando: `update_order_status` → Status: `PROCESSING` → `SHIPPED` → `DELIVERED`

**Ou:**

1. **Cliente faz pedido** → Status: `PENDING`
2. **Admin visualiza pedido** → Comando: `show_order`
3. **Admin rejeita pedido** → Comando: `reject_order` → Status: `REJECTED` (estoque devolvido)

---

## 🚀 Integração com Telegram

Os comandos estão integrados ao router do Telegram (`routes/telegram_router.py`). Quando uma mensagem é recebida:

1. A mensagem é validada pelo sistema de segurança
2. O sistema tenta detectar se é um comando
3. Se for um comando com confiança > 0.5, o comando é executado
4. Se não for comando, a mensagem é processada no fluxo de produtos

**Endpoint:** `POST /chatbot/process-message-authenticated`

**Headers:**
- `X-Telegram-Bot-Token`: Token do bot do Telegram

---

## 📝 Exemplos de Conversação

### Exemplo 1: Listar Pedidos Pendentes

```
Usuário: Liste os pedidos pendentes
Bot: Encontrados 3 pedido(s) com status 'pending'
     - Pedido ORD-20240101-ABC12 (Cliente: João Silva) - R$ 214.90
     - Pedido ORD-20240101-DEF34 (Cliente: Maria Santos) - R$ 150.00
     - Pedido ORD-20240101-GHI56 (Cliente: Pedro Costa) - R$ 89.90
```

### Exemplo 2: Ver Detalhes de um Pedido

```
Usuário: Mostre o pedido ORD-20240101-ABC12
Bot: 📦 Pedido: ORD-20240101-ABC12
     👤 Cliente: João Silva
     📞 Telefone: (11) 99999-9999
     📧 Email: joao@example.com
     
     📍 Endereço:
     Rua Exemplo, 123
     São Paulo, SP - 01234-567
     
     📋 Itens:
       • Produto Exemplo (Qtd: 2) - R$ 199.90
     
     💰 Valores:
       Subtotal: R$ 199.90
       Frete: R$ 15.00
       Total: R$ 214.90
     
     📊 Status: PENDING
     💳 Pagamento: pending (pix)
```

### Exemplo 3: Aprovar Pedido

```
Usuário: Aprove o pedido 123
Bot: ⚠️ Confirmação necessária
     Deseja aprovar o pedido ORD-20240101-ABC12?
     [Confirmação necessária - comando requer confirmação]
     
Usuário: [Confirma]
Bot: ✅ Pedido ORD-20240101-ABC12 aprovado com sucesso!
```

### Exemplo 4: Rejeitar Pedido

```
Usuário: Rejeite o pedido 123 motivo='Estoque insuficiente'
Bot: ⚠️ Confirmação necessária
     Deseja rejeitar o pedido ORD-20240101-ABC12?
     Motivo: Estoque insuficiente
     [Confirmação necessária - estoque será devolvido]
     
Usuário: [Confirma]
Bot: ✅ Pedido ORD-20240101-ABC12 rejeitado. Estoque devolvido.
```

---

## 🛠️ Arquivos Criados/Modificados

### Novos Arquivos:
- `models/order_models.py` - Modelos de dados para pedidos
- `services/order_service.py` - Serviço de gerenciamento de pedidos
- `ORDER_COMMANDS_TELEGRAM.md` - Esta documentação

### Arquivos Modificados:
- `services/commands/definitions.py` - Adicionados comandos de pedidos
- `services/commands/analyzer.py` - Adicionada extração de parâmetros de pedidos
- `services/commands/executor.py` - Atualizado para passar user_id
- `services/security/permissions.py` - Adicionadas permissões de pedidos
- `services/database_service.py` - Atualizado para criar tabelas de pedidos
- `routes/telegram_router.py` - Integrado sistema de comandos

---

## 🗄️ Estrutura do Banco de Dados

### Tabela: `orders`
- Armazena informações dos pedidos
- Relacionamento com `order_items`
- Status controlado por enum `OrderStatus`

### Tabela: `order_items`
- Armazena itens de cada pedido
- Relacionamento com `orders` e `products`
- Mantém preços históricos

---

## ⚠️ Observações Importantes

1. **Confirmação de Comandos**: Comandos que modificam pedidos (`approve_order`, `reject_order`, `update_order_status`) requerem confirmação do usuário.

2. **Devolução de Estoque**: Ao rejeitar um pedido, os produtos são automaticamente devolvidos ao estoque.

3. **Números de Pedido**: Cada pedido recebe um número único no formato `ORD-YYYYMMDD-XXXXX`.

4. **Permissões**: Certifique-se de que os usuários têm as permissões adequadas antes de executar comandos.

5. **Validação**: O sistema valida estoque, produtos ativos e outros requisitos antes de criar ou processar pedidos.

---

## 🔮 Melhorias Futuras

- [ ] Comando para criar pedidos via Telegram
- [ ] Notificações automáticas de novos pedidos
- [ ] Integração com sistemas de pagamento
- [ ] Rastreamento de envio
- [ ] Relatórios de vendas
- [ ] Dashboard de pedidos

---

**Desenvolvido para o sistema de e-commerce Multitrem** 🚀
