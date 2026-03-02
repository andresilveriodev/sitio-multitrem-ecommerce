# Prompt Simples: Normalizar Pedidos do Telegram

## Sua Tarefa

Receber texto de pedidos do Telegram, normalizar e enviar para `POST v1/chatbot/orders/bulk`

## Entrada (Texto do Telegram)

```
Dona Dilma: 08 Couve 04 Coentros 04 Cebolinhas 01 palito alface roxa 02 rúcula
```

OU

```
🍽 Dona Dilma — Recanto Verde (R$ 2,50)
08 Couve
04 Coentro
02 Rúcula
```

## Saída (JSON)

```json
{
  "conversation_id": "{uuid}",
  "orders": [
    {
      "contact_name": "Dilma",
      "establishment_name": "Recanto Verde",
      "contact_phone": "+556296208835",
      "price_profile_hint": "R$ 2,50",
      "items": [
        {"product_id": 1, "product_name": "Couve", "qty": 8},
        {"product_id": 2, "product_name": "Coentro", "qty": 4}
      ]
    }
  ]
}
```

## Passos

1. **Remover pronomes**: "Dona Dilma" → "Dilma"
2. **Extrair contato**: texto antes de ":" ou "—"
3. **Extrair estabelecimento**: texto entre "—" e preço
4. **Extrair preço**: padrão "(R$ X,XX)"
5. **Extrair produtos**: "08 Couve" → qty: 8, name: "Couve"
6. **Buscar produtos**: `GET v1/products?search={nome}` para obter `product_id` (OBRIGATÓRIO)
   - Retorna LISTA de produtos
   - Se 1 resultado: usar `product_id`
   - Se múltiplos resultados: tentar matching mais preciso
   - Se não conseguir determinar: deixar `product_id: null` (não mostrar lista para usuário)
7. **Buscar cliente** (OPCIONAL): `GET v1/customers?search={nome}`
   - Pode buscar por: nome do estabelecimento OU nome do contato
   - **SEMPRE retorna LISTA** (mesmo que seja apenas 1 resultado)
   - Pode retornar múltiplos se houver estabelecimentos/contatos com mesmo nome
   - Se múltiplos: tentar matching mais preciso ou deixar sistema identificar
   - Não é obrigatório - sistema identifica/cria automaticamente
8. **Enviar**: `POST v1/chatbot/orders/bulk`

## Regras

- Pronomes a remover: Dona, Don, Senhor, Senhora, Sr, Sra
- Se produto não encontrado: `product_id: null` (não bloqueia)
- Quantidades: números inteiros (08 → 8)
- Telefone: opcional, formato E.164

## Exemplo Completo

**Entrada:**
```
🍽 Dona Dilma — Recanto Verde (R$ 2,50)
08 Couve
04 Coentro
```

**Processamento:**
1. Contato: "Dilma" (removeu "Dona")
2. Estabelecimento: "Recanto Verde"
3. Preço: "R$ 2,50"
4. Produtos: Couve (qty: 8), Coentro (qty: 4)
5. Busca produtos no banco
6. Monta JSON e envia

**Saída:**
```json
{
  "orders": [{
    "contact_name": "Dilma",
    "establishment_name": "Recanto Verde",
    "price_profile_hint": "R$ 2,50",
    "items": [
      {"product_id": 1, "product_name": "Couve", "qty": 8},
      {"product_id": 2, "product_name": "Coentro", "qty": 4}
    ]
  }]
}
```
