# Guia: Chatbot → E-commerce (Criar Pedido)

## Endpoint Principal

```
POST v1/chatbot/orders/bulk
Headers: Authorization: Bearer {token_keycloak}
Content-Type: application/json
```

## Fluxo Básico

### 1. Receber Texto do Telegram
```
Dona Dilma: 08 Couve 04 Coentros 04 Cebolinhas
```

### 2. Normalizar Dados
- Remover pronomes: "Dona Dilma" → "Dilma"
- Extrair produtos: "08 Couve" → qty: 8, name: "Couve"
- Extrair estabelecimento (se houver)
- Extrair contato (se houver)

### 3. Buscar Produtos (OBRIGATÓRIO)
```
GET v1/products?search=Couve
Headers: Authorization: Bearer {token_keycloak}
```

**Resposta:**
```json
[
  {
    "id": 1,
    "name": "Couve",
    "sku": "COUVE"
  }
]
```

**Decisão:**
- Se 1 resultado → usar `product_id: 1`
- Se múltiplos → tentar matching mais preciso
- Se não encontrar → `product_id: null`

### 4. Enviar Pedido
```
POST v1/chatbot/orders/bulk
Headers: Authorization: Bearer {token_keycloak}
```

**Body:**
```json
{
  "conversation_id": "{uuid_da_conversa}",
  "orders": [
    {
      "contact_name": "Dilma",
      "establishment_name": null,
      "contact_phone": null,
      "price_profile_hint": null,
      "items": [
        {
          "product_id": 1,
          "product_name": "Couve",
          "qty": 8
        },
        {
          "product_id": 2,
          "product_name": "Coentro",
          "qty": 4
        },
        {
          "product_id": 3,
          "product_name": "Cebolinha",
          "qty": 4
        }
      ]
    }
  ]
}
```

## Schema Completo

### TelegramBulkOrdersCreate
```json
{
  "conversation_id": "uuid-opcional",
  "orders": [
    {
      "contact_name": "Nome do contato (sem pronomes)",
      "establishment_name": "Nome do estabelecimento",
      "contact_phone": "+5562999999999",
      "price_profile_hint": "R$ 2,50",
      "items": [
        {
          "product_id": 1,
          "product_name": "Nome do produto",
          "qty": 8
        }
      ]
    }
  ]
}
```

### Campos

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `conversation_id` | UUID | Não | ID da conversa no Telegram |
| `orders` | Array | **SIM** | Lista de pedidos |
| `contact_name` | String | Não | Nome do contato (sem pronomes) |
| `establishment_name` | String | Não | Nome do estabelecimento |
| `contact_phone` | String | Não | Telefone E.164 (+5562...) |
| `price_profile_hint` | String | Não | Dica de preço (ex: "R$ 2,50") |
| `items` | Array | **SIM** | Lista de itens (mínimo 1) |
| `product_id` | Integer | Não | ID do produto (null se não identificado) |
| `product_name` | String | **SIM** | Nome original do produto |
| `qty` | Number | **SIM** | Quantidade |

## Regras Importantes

### 1. Produtos
- **SEMPRE buscar** produtos antes de enviar: `GET v1/products?search={nome}`
- Retorna **LISTA** (pode ter múltiplos resultados)
- Se não encontrar ou ambíguo: `product_id: null` (não bloqueia pedido)
- Produtos não identificados ficam nas observações

### 2. Clientes
- Busca é **OPCIONAL**: `GET v1/customers?search={nome}`
- Retorna **LISTA** de clientes
- Se não encontrar: sistema cria temporário automaticamente
- Pode buscar por: nome do estabelecimento OU nome do contato

### 3. Remover Pronomes
- "Dona Dilma" → "Dilma"
- "Senhor João" → "João"
- Pronomes: Dona, Don, Senhor, Senhora, Sr, Sra, Sr., Sra.

### 4. Quantidades
- "08 Couve" → qty: 8
- "04 Coentros" → qty: 4
- Sempre número inteiro

## Exemplo Completo

### Entrada (Telegram)
```
🍽 Dona Dilma — Recanto Verde (R$ 2,50)

08 Couve
04 Coentro
04 Cebolinha
```

### Processamento

**1. Extrair dados:**
- Contato: "Dilma"
- Estabelecimento: "Recanto Verde"
- Preço: "R$ 2,50"
- Produtos: Couve (8), Coentro (4), Cebolinha (4)

**2. Buscar produtos:**
```
GET v1/products?search=Couve → [{id: 1, name: "Couve"}]
GET v1/products?search=Coentro → [{id: 2, name: "Coentro"}]
GET v1/products?search=Cebolinha → [{id: 3, name: "Cebolinha"}]
```

**3. Enviar pedido:**
```json
{
  "orders": [
    {
      "contact_name": "Dilma",
      "establishment_name": "Recanto Verde",
      "contact_phone": null,
      "price_profile_hint": "R$ 2,50",
      "items": [
        {"product_id": 1, "product_name": "Couve", "qty": 8},
        {"product_id": 2, "product_name": "Coentro", "qty": 4},
        {"product_id": 3, "product_name": "Cebolinha", "qty": 4}
      ]
    }
  ]
}
```

## Endpoints Utilizados

### 1. Buscar Produtos
```
GET v1/products?search={nome}
Headers: Authorization: Bearer {token}
```
- **Obrigatório** antes de enviar pedido
- Retorna LISTA de produtos
- Usar para obter `product_id`

### 2. Buscar Clientes (Opcional)
```
GET v1/customers?search={nome}
Headers: Authorization: Bearer {token}
```
- **Opcional** - sistema identifica automaticamente
- Retorna LISTA de clientes
- Pode buscar por estabelecimento OU contato

### 3. Criar Pedidos
```
POST v1/chatbot/orders/bulk
Headers: Authorization: Bearer {token}
Content-Type: application/json
```
- **Endpoint principal** para criar pedidos
- Aceita múltiplos pedidos em uma requisição
- Sistema identifica/cria clientes automaticamente

## Resposta do Endpoint

**Sucesso (201):**
```json
[
  {
    "id": "uuid-do-pedido",
    "customer_id": 1,
    "status": "draft",
    "items": [...],
    "subtotal": 50.00,
    "delivery_fee": 5.00,
    "total": 55.00
  }
]
```

**Erro (400):**
```json
{
  "detail": "Nenhum pedido foi criado. Verifique se os produtos foram identificados corretamente."
}
```

## Tratamento de Erros

- Se nenhum produto identificado: retorna 400
- Se produto não encontrado: `product_id: null` (não bloqueia)
- Se cliente não encontrado: sistema cria temporário
- Se múltiplos produtos/clientes: tentar matching mais preciso

## Checklist

Antes de enviar pedido:
- [ ] Remover pronomes do nome do contato
- [ ] Extrair produtos e quantidades
- [ ] Buscar produtos no banco (`GET v1/products?search={nome}`)
- [ ] Tentar identificar `product_id` para cada produto
- [ ] Extrair `establishment_name` (se houver)
- [ ] Extrair `contact_name` (se houver)
- [ ] Extrair `price_profile_hint` (se houver)
- [ ] Montar JSON com estrutura correta
- [ ] Enviar para `POST v1/chatbot/orders/bulk`

## Exemplo Mínimo

**Entrada:**
```
08 Couve
```

**Processamento:**
1. Buscar: `GET v1/products?search=Couve`
2. Encontrar: `product_id: 1`
3. Enviar:
```json
{
  "orders": [{
    "items": [
      {"product_id": 1, "product_name": "Couve", "qty": 8}
    ]
  }]
}
```

**Pronto!** O sistema cria o pedido automaticamente.
