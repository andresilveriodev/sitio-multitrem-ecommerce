# Exemplo: Busca de Produtos com Múltiplos Resultados

## Cenário: "Quero uma alface"

### Passo 1: Buscar no Banco
```
GET v1/products?search=alface
```

### Resposta (exemplo):
```json
[
  {
    "id": 1,
    "name": "Alface Crespa",
    "sku": "ALFACE_CRESPA",
    "unit": "un"
  },
  {
    "id": 2,
    "name": "Alface Roxa",
    "sku": "ALFACE_ROXA",
    "unit": "un"
  },
  {
    "id": 3,
    "name": "Palito Alface",
    "sku": "PALITO_ALFACE",
    "unit": "palito"
  },
  {
    "id": 4,
    "name": "Palito Alface Roxa",
    "sku": "PALITO_ALFACE_ROXA",
    "unit": "palito"
  }
]
```

### Passo 2: Decisão

**Se o texto original for:**
- "alface" → Múltiplos resultados, deixar `product_id: null`
- "alface crespa" → Matching exato com ID 1, usar `product_id: 1`
- "palito alface" → Matching com ID 3, usar `product_id: 3`
- "palito alface roxa" → Matching exato com ID 4, usar `product_id: 4`

**Regra**: Se não conseguir determinar qual produto específico, deixar `product_id: null`

### Passo 3: Enviar Pedido
```json
{
  "items": [
    {
      "product_id": null,  // Não identificado
      "product_name": "alface",
      "qty": 1
    }
  ]
}
```

O pedido será criado e "alface" ficará nas observações para escolha manual posterior.

## Estratégia de Matching

1. **Busca exata**: "alface crespa" → encontra "Alface Crespa" → usar `product_id`
2. **Busca parcial precisa**: "palito" + "roxa" → encontra "Palito Alface Roxa" → usar `product_id`
3. **Busca ambígua**: "alface" → múltiplos resultados → `product_id: null`

**NÃO mostrar lista para o usuário escolher**. Se houver ambiguidade, deixe `product_id: null` e o pedido será criado mesmo assim.
