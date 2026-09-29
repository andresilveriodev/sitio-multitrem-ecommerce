# API para Processar Pedidos do Telegram

## Endpoint

```
POST v1/chatbot/orders/bulk
```

**Autenticação**: Requer token Keycloak no header `Authorization: Bearer {token}`

## Schema de Requisição

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
          "qty": 8,
          "is_palito": false
        }
      ]
    }
  ]
}
```

## Campos

### TelegramBulkOrdersCreate
- `conversation_id` (opcional): UUID da conversa no Telegram
- `orders` (obrigatório): Lista de pedidos normalizados

### TelegramNormalizedOrder
- `contact_name` (opcional): Nome do contato sem pronomes (ex: "Dilma" ao invés de "Dona Dilma")
- `establishment_name` (opcional): Nome do estabelecimento (ex: "Recanto Verde")
- `contact_phone` (opcional): Telefone do contato em formato E.164
- `price_profile_hint` (opcional): Dica de preço para determinar perfil (ex: "R$ 2,50")
- `items` (obrigatório): Lista de itens do pedido

### TelegramNormalizedOrderItem
- `product_id` (opcional): ID do produto no banco. Se `null`, produto não foi identificado
- `product_name` (obrigatório): Nome original do produto
- `qty` (obrigatório): Quantidade

**Nota**: Cada produto (incluindo diferentes embalagens/tamanhos) deve ser um produto diferente no banco. O sistema detecta automaticamente se é palito pelo nome/SKU do produto.

## Comportamento

1. **Identificação de Cliente**:
   - Tenta encontrar por `establishment_name`
   - Se não encontrar, tenta por `contact_phone`
   - Se não encontrar, cria cliente temporário

2. **Criação de Contato**:
   - Se encontrar cliente mas não contato, cria contato automaticamente
   - Se criar cliente temporário e tiver `contact_name`, cria contato também

3. **Produtos**:
   - Apenas itens com `product_id` são incluídos no pedido
   - Produtos sem `product_id` são listados nas observações do pedido

4. **Perfil de Preço**:
   - Se `price_profile_hint` contém "2.50" ou "2,50" → RESTAURANTE_LOW
   - Se contém "3.00" ou "3,00" → RESTAURANTE_HIGH
   - Se contém "3.50" ou "3,50" → RESTAURANTE_LOW
   - Se contém "4.00" ou "4,00" → VAREJO
   - Padrão: RESTAURANTE_LOW

## Exemplo de Requisição

Ver arquivo `telegram_order_example.json`

## Resposta

Retorna lista de `OrderResponse` com os pedidos criados.

## Tratamento de Erros

- Se nenhum pedido for criado (todos os produtos não identificados), retorna 400
- Se algum pedido falhar, continua processando os outros
- Erros são logados mas não interrompem o processamento dos demais pedidos
