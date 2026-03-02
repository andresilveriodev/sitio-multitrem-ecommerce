# Exemplo: Busca de Clientes/Estabelecimentos

## Cenário 1: Buscar por Nome do Estabelecimento

### Passo 1: Buscar no Banco (Opcional)
```
GET v1/customers?search=Recanto Verde
```

### Resposta (exemplo):
```json
[
  {
    "id": 1,
    "name": "Recanto Verde",
    "phone_e164": "+556296208835",
    "price_profile": "RESTAURANTE_LOW"
  }
]
```

### Decisão

**Se retornar 1 cliente:**
- Cliente encontrado! Mas você não precisa fazer nada especial
- Apenas envie `establishment_name: "Recanto Verde"` no JSON
- O sistema identificará automaticamente pelo nome

**Se retornar múltiplos clientes:**
- **SEMPRE retorna uma LISTA**, mesmo que seja apenas 1 resultado
- Exemplo: `GET v1/customers?search=João` pode retornar:
  ```json
  [
    {
      "id": 1,
      "name": "Restaurante A",
      "contacts": [{"name": "João"}]
    },
    {
      "id": 2,
      "name": "Restaurante B",
      "contacts": [{"name": "João"}]
    }
  ]
  ```
- Tentar matching mais preciso usando outros dados (telefone, estabelecimento)
- Se não conseguir determinar: apenas envie `establishment_name` e `contact_name`
- O sistema tentará identificar ou criará temporário

**Se retornar 0 clientes:**
- Envie `establishment_name: "Recanto Verde"` mesmo assim
- O sistema criará cliente temporário automaticamente

### Importante

**Você NÃO precisa enviar `customer_id` no JSON**. Apenas envie:
- `establishment_name`: "Recanto Verde"
- `contact_name`: "Dilma" (se houver)
- `contact_phone`: "+556296208835" (se houver)

O sistema faz a identificação/criação automaticamente no endpoint `/orders/bulk`.

## Cenário 2: Buscar por Nome do Contato

### Passo 1: Buscar no Banco (Opcional)
```
GET v1/customers?search=Dilma
```

### Resposta (exemplo):
```json
[
  {
    "id": 1,
    "name": "Recanto Verde",
    "phone_e164": "+556296208835",
    "price_profile": "RESTAURANTE_LOW",
    "contacts": [
      {
        "id": 1,
        "name": "Dilma",
        "customer_id": 1
      },
      {
        "id": 2,
        "name": "João",
        "customer_id": 1
      }
    ]
  }
]
```

### Decisão

**Se retornar cliente(s):**
- Cliente encontrado! Mesmo que tenha buscado pelo nome do contato
- Apenas envie `establishment_name: "Recanto Verde"` e `contact_name: "Dilma"` no JSON
- O sistema identificará automaticamente

**Importante**: Um estabelecimento pode ter múltiplos contatos. A busca retorna o cliente mesmo se você pesquisar pelo nome de um contato específico.

## Resumo

A busca `GET v1/customers?search={nome}` funciona para:
- ✅ Nome do estabelecimento: "Recanto Verde"
- ✅ Nome do contato: "Dilma"
- ✅ Telefone: "+556296208835"
- ✅ Documento: "12345678900"

E retorna o **cliente** (estabelecimento), mesmo que tenha buscado pelo nome de um contato.

## Cenário 3: Múltiplos Estabelecimentos/Contatos com Mesmo Nome

### Exemplo: Múltiplos Contatos "João"

**Busca:**
```
GET v1/customers?search=João
```

**Resposta (LISTA):**
```json
[
  {
    "id": 1,
    "name": "Restaurante A",
    "phone_e164": "+5562991111111",
    "contacts": [
      {"id": 1, "name": "João", "customer_id": 1}
    ]
  },
  {
    "id": 2,
    "name": "Restaurante B",
    "phone_e164": "+5562992222222",
    "contacts": [
      {"id": 2, "name": "João", "customer_id": 2}
    ]
  }
]
```

### Decisão do Chatbot

**Se retornar múltiplos clientes:**
1. Tentar usar outros dados para identificar:
   - Telefone do contato (`contact_phone`)
   - Nome do estabelecimento (`establishment_name`)
   - Contexto da conversa
2. Se conseguir identificar: usar dados para matching mais preciso
3. Se não conseguir: enviar `establishment_name` e `contact_name` mesmo assim
4. O sistema `/orders/bulk` tentará identificar ou criará temporário

### Exemplo: Múltiplos Estabelecimentos "Recanto Verde"

**Busca:**
```
GET v1/customers?search=Recanto Verde
```

**Resposta (LISTA):**
```json
[
  {
    "id": 1,
    "name": "Recanto Verde",
    "phone_e164": "+5562991111111",
    "addresses": [{"city": "Goiânia"}]
  },
  {
    "id": 2,
    "name": "Recanto Verde",
    "phone_e164": "+5562992222222",
    "addresses": [{"city": "Aparecida"}]
  }
]
```

**Estratégia:**
- Se tiver telefone: usar para matching mais preciso
- Se não tiver: enviar `establishment_name` e deixar sistema identificar

## Comparação: Produtos vs Clientes

| Aspecto | Produtos | Clientes |
|---------|----------|----------|
| Busca | `GET v1/products?search={nome}` | `GET v1/customers?search={nome}` |
| Retorna | LISTA | LISTA |
| Obrigatório? | **SIM** - precisa `product_id` | **NÃO** - sistema identifica automaticamente |
| Se não encontrar | `product_id: null` | Sistema cria temporário |
| Se múltiplos | Tentar matching ou `product_id: null` | Sistema tenta identificar ou cria temporário |

## Estratégia Recomendada

1. **Para Produtos**: SEMPRE buscar e tentar identificar `product_id`
2. **Para Clientes**: Busca é OPCIONAL. Apenas extrair e enviar `establishment_name` e `contact_name`
3. **Deixar o sistema fazer**: O endpoint `/orders/bulk` já tem lógica para identificar/criar clientes
