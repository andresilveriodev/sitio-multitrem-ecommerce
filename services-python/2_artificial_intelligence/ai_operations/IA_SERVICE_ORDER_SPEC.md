# Especificação do ia_service – Pedidos e Conversas

Documento único para alinhar o **ia_service** (ai_operations), o **chatbot/router** e o **commerce**: contrato, parâmetros obrigatórios, mapeamento e regras de persistência.

---

## 1. Objetivo do ia_service

O **ia_service** atua no chat interno entre **usuário ↔ chatbot ↔ ia_service**:

- **Interpretar** mensagens ambíguas e linguagem natural
- **Extrair** dados estruturados (cliente, itens, quantidades, pagamento)
- **Completar** o que o funcionário quis dizer
- **Sugerir** upsell e próxima pergunta curta
- **Resolver** casos fora do padrão rígido

**Regra prática:** O **chatbot decide o caminho** (roteamento, intenção óbvia, estado). A **IA entende o conteúdo** (extração, contexto, sugestões).

---

## 2. Contrato com o consumidor

### Entrada

- **message** (obrigatório): texto do funcionário
- **task** (opcional): ex. `extract_order`, `general_assistant`
- **context** (opcional):
  - **current_order**: pedido em construção (quando há fluxo ativo)
  - **conversation_id**: identificador da conversa

Exemplo:

```json
{
  "task": "extract_order",
  "message": "quero registrar o pedido do Adriano com 2 alfaces e 1 couve",
  "current_order": {}
}
```

### Saída (sempre JSON)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `intent` | string | create_order, update_order, add_item, remove_item, change_payment, ask_human, smalltalk_or_other, unknown |
| `confidence` | number | 0–1 |
| `reply_mode` | string | `"structured"` quando há order_data / intents de pedido; outro valor para smalltalk etc. |
| `message_for_employee` | string | Mensagem curta para exibir ao funcionário |
| `order_data` | object | Dados extraídos (ver seção 4). Para edição: incluir `order_id` ou `current_order_id` quando conhecido |
| `missing_required_fields` | array | Campos obrigatórios ainda faltando para poder salvar |
| `missing_optional_fields` | array | Campos opcionais não preenchidos |
| `can_save_now` | boolean | Se já dá para persistir o pedido |
| `save_status_if_saved_now` | string | draft / pending / complete |
| `suggested_next_question` | string | Próxima pergunta curta sugerida |
| `upsell_suggestions` | array | Sugestões de upsell |
| `human_handoff` | boolean | Se deve passar para atendente humano |

---

## 3. Parâmetros obrigatórios para criar um pedido

Com base no **commerce** (payload que realmente cria pedido – `TelegramNormalizedOrder`):

### Cliente (pelo menos um)

| Campo | Obrigatório para salvar? | Descrição | Exemplo |
|-------|---------------------------|-----------|---------|
| **contact_name** | Sim* | Nome do contato (sem pronomes) | "Dilma", "Adriano" |
| **establishment_name** | Sim* | Nome do estabelecimento | "Recanto Verde" |

\* Pelo menos um dos dois. Se nenhum vier, o commerce usa `"Cliente Temporário"` (ver `chatbot.py` ~282).

### Itens

| Campo | Obrigatório | Descrição | Exemplo |
|-------|-------------|-----------|---------|
| **items** | Sim | Lista com ≥ 1 item | — |
| **items[].product_name** | Sim | Nome do produto | "alface", "couve" |
| **items[].qty** | Sim | Quantidade (> 0) | 2 |
| **items[].product_id** | Não | ID do produto; se omitido, commerce faz matching por nome | 42 |

**Resumo:** O mínimo para **poder salvar** é: **cliente** (contact_name ou establishment_name) + **pelo menos um item** com `product_name` e `qty`.

---

## 4. Campos opcionais

- **contact_phone**
- **payment_method** (valores do enum: `pix`, `cash`, `card`, `transfer`)
- **delivery_date** / **notes** / **order_channel** (se o fluxo usar)
- **price_profile_hint** (ex.: dica de perfil de preço)

---

## 5. Mapeamento AI → Commerce

### order_data (ia_service) → TelegramNormalizedOrder (commerce)

| AI (order_data) | Commerce (TelegramNormalizedOrder) | Notas |
|-----------------|-------------------------------------|--------|
| **contact_name** | contact_name | Nome do contato sem pronomes |
| **establishment_name** | establishment_name | Nome do estabelecimento |
| **customer_name** (único) | contact_name e/ou establishment_name | Se o AI devolver só um nome, preencher **contact_name**; establishment_name null. Se houver “estabelecimento X” e “contato Y”, preencher os dois |
| **quantity** (AI) | **qty** (commerce) | O schema do commerce usa **qty**. Documentar: o consumidor (chatbot) mapeia quantity → qty ao montar o payload |
| **payment_method** | PaymentMethod | Valores do enum em **minúsculo**: `pix`, `cash`, `transfer`, `card`. Se o prompt usar "PIX", "DINHEIRO", "CARTAO", o doc deve descrever o mapeamento (ex.: DINHEIRO → cash, CARTAO → card) |
| **order_id** / **current_order_id** | — | Para intents de edição; usado pelo consumidor para saber qual pedido alterar |

### PaymentMethod (commerce)

- `pix` – PIX  
- `cash` – Dinheiro  
- `transfer` – Transferência  
- `card` – Cartão  

---

## 6. Intents e comportamento

| Intent | Descrição | order_id / current_order_id |
|--------|-----------|-----------------------------|
| **create_order** | Novo pedido | Não necessário |
| **update_order** | Alterar pedido existente | Preencher quando o contexto tiver pedido atual ou o funcionário mencionar qual pedido |
| **add_item** | Adicionar item ao pedido | Idem |
| **remove_item** | Remover item | Idem |
| **change_payment** | Alterar forma de pagamento | Idem |
| **ask_human** | Passar para atendente | — |
| **smalltalk_or_other** | Conversa geral | — |
| **unknown** | Não identificado | — |

Para intents de edição, o **consumidor** deve passar no contexto o pedido atual; o AI devolve **order_id** (ou **current_order_id**) no `order_data` quando aplicável.

---

## 7. Regras de persistência

- **can_save_now = true**: dados obrigatórios preenchidos (cliente + ≥ 1 item com product_name e qty); o chatbot pode persistir.
- **save_status_if_saved_now**: status sugerido ao salvar agora (`draft`, `pending`, `complete`); o backend usa conforme regra de negócio.
- Quando **can_save_now = true**, o chatbot persiste e conduz o fluxo (ex.: confirmação, próximo passo).

---

## 8. reply_mode

- **"structured"**: sempre que houver `order_data` ou intents de pedido; o consumidor deve fazer parse do JSON e usar order_data + flags.
- Outro valor (ex.: para smalltalk): resposta mais livre; o consumidor pode exibir apenas `message_for_employee` sem parse de pedido.

---

## 9. Versão do prompt / histórico

| Versão | Data | Resumo |
|--------|------|--------|
| v1 | — | JSON estruturado (intent, order_data, can_save_now, etc.) |
| v2 | — | contact_name + establishment_name em vez de só customer_name |
| v3 | — | order_id / current_order_id para intents de edição |

*(Atualizar esta tabela ao mudar o system prompt.)*

---

## 10. Exemplos de entrada/saída

### Exemplo 1 – Criar pedido (um nome só → contact_name)

**Entrada:**

```json
{
  "task": "extract_order",
  "message": "pedido da Dona Dilma, 2 alfaces e 1 couve",
  "current_order": {}
}
```

**Saída:**

```json
{
  "intent": "create_order",
  "confidence": 0.95,
  "reply_mode": "structured",
  "message_for_employee": "Pedido da Dilma: 2 alfaces, 1 couve. Salvar?",
  "order_data": {
    "contact_name": "Dilma",
    "establishment_name": null,
    "items": [
      {"product_name": "alface", "qty": 2},
      {"product_name": "couve", "qty": 1}
    ]
  },
  "missing_required_fields": [],
  "missing_optional_fields": ["contact_phone", "payment_method"],
  "can_save_now": true,
  "save_status_if_saved_now": "pending",
  "suggested_next_question": "Forma de pagamento?",
  "upsell_suggestions": [],
  "human_handoff": false
}
```

### Exemplo 2 – Estabelecimento + contato

**Mensagem:** "Recanto Verde, falar com a Dilma – 3 alfaces, 1 cartela de ovos, deixa no PIX depois."

**order_data esperado:**

- **establishment_name**: "Recanto Verde"  
- **contact_name**: "Dilma"  
- **items**: alface (3), cartela de ovos (1)  
- **payment_method**: "pix" (ou indicar “pagamento depois”)  
- **can_save_now**: true (se cliente + itens ok)

### Exemplo 3 – Edição (add_item com order_id)

**Entrada:**

```json
{
  "task": "extract_order",
  "message": "no mesmo pedido adiciona 2 couves",
  "current_order": {"id": "uuid-do-pedido-atual"}
}
```

**Saída:** intent `add_item`, `order_data` com **order_id** = "uuid-do-pedido-atual" e **items** = [{ "product_name": "couve", "qty": 2 }].

---

## Padronização no prompt

- **Produto:** Padronizar exemplos (ex.: sempre "cartela de ovos" ou sempre "cartela de 30 ovos") para não confundir o modelo.
- **Nomes:** Sempre remover pronomes em **contact_name** (ex.: "Dona Dilma" → "Dilma").

---

---

## 11. Fluxo via POST /ai/chat (conversa natural)

O **Chatbot Operations** usa o **mesmo** endpoint `POST /ai/chat` para o fluxo de registro de pedido. Não há endpoint separado (`/ai/extract-order`).

- **Entrada:** um único campo `message` (string) contendo um **prompt montado** pelo Chatbot, por exemplo:
  - Bloco `[Contexto: você está ajudando a registrar um pedido da horta. Pedido atual: {...}. Responda de forma natural... Se extrair dados, termine com: ORDER_DATA: {...}]`
  - Em seguida: `Mensagem do usuário: <texto do funcionário>`
- **Comportamento do AI Service:**
  - Quando detecta contexto de pedido (ex.: "registrar um pedido", "Pedido atual", "ORDER_DATA:" nas instruções), injeta instruções de sistema que reforçam: responder em português; ao extrair dados, terminar com **exatamente uma linha** `ORDER_DATA: <JSON>`.
  - JSON esperado nessa linha: `{"customer_name": string|null, "items": [{"product_name": string, "quantity": number}], "can_save_now": boolean}`.
  - O Chatbot procura a linha `ORDER_DATA:`, extrai o JSON e não exibe essa linha ao usuário; usa para atualizar estado e persistir quando `can_save_now === true`.
- Detalhes de implementação e exemplos: ver **AI_CHAT_ORDER_FLOW.md**.

---

*Este documento é a referência para o ia_service e para quem consome suas respostas (chatbot, commerce). Ao alterar regras ou campos, atualizar tanto o prompt do ia_service quanto este spec.*
