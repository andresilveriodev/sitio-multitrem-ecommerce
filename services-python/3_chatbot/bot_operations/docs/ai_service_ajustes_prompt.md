# Ajustes do AI Service para fluxo de registro de pedido

Documento para o time do **AI Service (Chatbot Middleware)** alinhar o comportamento do endpoint **`POST /ai/chat`** com o **Chatbot Operations**, sem criar novo endpoint.

---

## 1. Contexto

- O **Chatbot Operations** já identifica a intenção "criar pedido" (ex.: "quero registrar o pedido do Adriano") e envia a conversa para o **mesmo** `POST /ai/chat`.
- A mensagem recebida pelo AI Service pode vir **com contexto de pedido** no próprio texto do prompt, no formato descrito abaixo.
- O AI Service deve **responder de forma natural** e, quando extrair dados do pedido, **incluir uma linha estruturada** no final da resposta para o chatbot interpretar e persistir.

**Não é necessário** criar endpoint novo (`/ai/extract-order`). Tudo segue o fluxo natural de chat.

---

## 2. Payload de chat: mensagem + intents (para aprendizado)

O Chatbot envia para `POST /ai/chat` um JSON com:

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `message` | Sim | Texto do prompt/mensagem (pode conter contexto + mensagem do usuário). |
| `intent` | Não | Intent que o **router do Chatbot** identificou (ex.: `cumprimento`, `criar_pedido`, `conversa`, `pedidos`, `estoque`). |
| `confidence` | Não | Confiança do router (0.0–1.0). |
| `intent_reason` | Não | Motivo da classificação (ex.: `greeting`, `create_order_intent`, `keyword:pedidos`). |
| `user_id` | Não | ID do usuário (Telegram) para anonimizar em logs. |

**O que o AI Service deve fazer com esses campos:**

1. **Persistir para base de intents**  
   Antes ou depois de gerar a resposta, salvar em tabela/banco (ex.: `intent_examples` ou `conversation_logs`):  
   `message` (ou trecho), `intent`, `confidence`, `intent_reason`, `user_id`, `timestamp`.  
   Assim o AI Service constrói um dataset de **conversas reais + intent** e pode:
   - Treinar ou ajustar um classificador de intent.
   - Melhorar prompts ou regras com base em erros (ex.: mensagens em que `confidence` era baixa).
   - Gerar relatórios de intents mais usados ou confusos.

2. **Usar como contexto opcional**  
   Se `intent` e `confidence` vierem preenchidos, o modelo pode usar como hint (ex.: “O router classificou como criar_pedido; priorize extração de cliente e itens”).

3. **Não quebrar se os campos não existirem**  
   Manter compatibilidade: se o request tiver só `message`, seguir comportamento atual.

---

## 3. Como o Chatbot monta a mensagem

O Chatbot monta o campo `message` com um **prompt** que pode incluir contexto. Exemplo (fluxo de pedido):

```text
[Contexto: você está ajudando a registrar um pedido da horta. Pedido atual (o que já foi extraído): {"customer_name": null, "contact_name": null, "items": []}. Responda de forma natural em português. Se você extrair ou atualizar dados do pedido (nome do cliente, itens com quantidade), termine sua resposta com exatamente uma linha no formato:
ORDER_DATA: {"customer_name": "nome ou null", "items": [{"product_name": "...", "quantity": n}], "can_save_now": true ou false}
Não repita nada além do JSON nessa linha.]

Mensagem do usuário: Quero registrar o pedido do Adriano com 2 alfaces e 1 couve.
```

Ou seja: o AI Service recebe **uma única string** em `message`; dentro dela há o bloco `[Contexto: ...]` e a "Mensagem do usuário: ...".

---

## 4. Comportamento esperado do AI Service

1. **Detectar o contexto de pedido**  
   Quando a mensagem contiver algo como `[Contexto: você está ajudando a registrar um pedido da horta` (ou "Pedido atual", "ORDER_DATA:" nas instruções), tratar como **fluxo de registro de pedido**.

2. **Usar o que o Chatbot já envia no prompt**  
   O campo `message` contém:
   - **Estado atual do pedido** (JSON com `customer_name`, `items`, etc.). É a fonte da verdade: se `customer_name` já está preenchido (ex.: "Adriano"), **nunca** pedir o nome do cliente de novo.
   - **HISTÓRICO DA CONVERSA**: mensagens já trocadas (Usuário / Bot). **Não repetir perguntas** sobre o que já está no histórico (ex.: se no histórico já consta "pedido do Adriano" ou "já temos o nome: Adriano", não perguntar "para quem é o pedido?").
   - **Mensagem atual do usuário**: só essa é a nova fala do usuário.

3. **Extrair dados sem inventar ou trocar produtos**  
   - Nome do cliente: usar o que o usuário disse ou o que já está no estado/histórico.  
   - Itens e quantidades: usar **exatamente** o que o usuário informou. Se ele disse "01 Rucula", não escrever "couve" nem outro produto no lugar (nem em exemplos). Ex.: "2 alfaces, 1 rucula" → `{"product_name": "alface", "quantity": 2}`, `{"product_name": "rucula", "quantity": 1}`.

4. **Responder em português de forma natural**  
   Ex.: *"Entendi! Pedido do Adriano: 2 alfaces e 1 rucula. Quer que eu salve?"* (use os produtos que o usuário disse, não troque por outros).

5. **Fluxo obrigatório antes de salvar — NÃO pular**  
   - Coletar: **nome do cliente**, **itens** (produto e quantidade), **data de entrega**.  
   - Mostrar **resumo do pedido** e perguntar: "Confirma o pedido?" / "Está certo?"  
   - Perguntar: **"Deseja acrescentar algo?"**  
   - Só quando o usuário **confirmar** (ex.: "sim", "confirmo", "pode salvar", "está certo") e você já tiver cliente + itens + data de entrega, use `can_save_now: true`.  
   - **Nunca** use `can_save_now: true` só porque leu os itens — espere confirmação e dados completos.

6. **Incluir a linha ORDER_DATA quando houver dados de pedido**  
   No **final** da resposta, em **uma única linha**:

   ```text
   ORDER_DATA: {"customer_name": "Adriano", "items": [...], "delivery_date": "10/03/2026 ou null", "can_save_now": false}
   ```

   - **customer_name**: string ou `null`.  
   - **items**: lista de `{"product_name": string, "quantity": number}`.  
   - **delivery_date** (opcional): data de entrega informada pelo usuário ou `null`.  
   - **can_save_now**: `true` **somente** quando tiver cliente + itens + data de entrega (ou regra do negócio) **e** o usuário tiver confirmado o pedido. Caso contrário, sempre `false`.

7. **Não incluir ORDER_DATA** quando a mensagem for só conversa (ex.: "obrigado", "cancelar") ou quando não houver nenhum dado de pedido a extrair. Nesse caso, responder só o texto natural.

---

## 6. Formato exato da linha ORDER_DATA

- A resposta deve conter **exatamente uma linha** que começa com `ORDER_DATA:` (sem espaço antes).  
- Depois de `ORDER_DATA:` deve vir **um único objeto JSON** válido, na mesma linha.  
- O Chatbot Operations procura essa linha, extrai o JSON e **não** mostra essa linha para o usuário (só usa para atualizar estado e persistir).

Exemplo de resposta completa:

```text
Entendi! Pedido do Adriano com 2 alfaces e 1 couve. Posso salvar?
ORDER_DATA: {"customer_name": "Adriano", "items": [{"product_name": "alface", "quantity": 2}, {"product_name": "couve", "quantity": 1}], "can_save_now": true}
```

Exemplo quando ainda falta confirmação:

```text
Anotado: Adriano, 2 alfaces e 1 couve. Quer que eu registre esse pedido?
ORDER_DATA: {"customer_name": "Adriano", "items": [{"product_name": "alface", "quantity": 2}, {"product_name": "couve", "quantity": 1}], "can_save_now": false}
```

---

## 7. Regras práticas para o modelo

- **Sempre** responder em português, de forma clara e curta.  
- **Só** incluir a linha `ORDER_DATA:` quando a mensagem for sobre registro de pedido e houver algo a extrair ou atualizar (cliente e/ou itens).  
- **Mesclar** com o "Pedido atual" enviado no prompt: se o cliente já veio em turno anterior, manter; se o usuário disser novos itens, acrescentar aos itens existentes.  
- **can_save_now = true** apenas quando: (1) tiver `customer_name` preenchido, (2) tiver pelo menos um item com quantidade > 0, e (3) o usuário tiver confirmado (ou a frase já trouxer pedido completo e inequívoco).  
- Nomes de produtos: usar termos que o e-commerce reconheça (ex.: "alface", "couve", "rúcula", "coentro"). O Chatbot faz busca por nome no sistema; variações próximas ajudam.

---

## 8. Resumo para implementação

| Item | O que fazer |
|------|-------------|
| Endpoint | Manter só `POST /ai/chat`. Nenhum endpoint novo. |
| Entrada | `message` (obrigatório). Opcionais: `intent`, `confidence`, `intent_reason`, `user_id` — usar para persistir e aprender (base de intents). |
| Resposta | Texto natural em português. Quando for fluxo de pedido e houver dados extraídos, terminar com uma linha: `ORDER_DATA: <JSON>`. |
| JSON | `{"customer_name": string|null, "items": [{"product_name": string, "quantity": number}], "can_save_now": boolean}`. |
| Base de intents | Persistir (message, intent, confidence, intent_reason, user_id, timestamp) para treinar/ajustar classificação e reduzir erros. |
| Uso no Chatbot | O Chatbot interpreta a linha ORDER_DATA, atualiza estado e persiste o pedido quando `can_save_now === true` e há cliente + itens. |

Com esses ajustes, o AI Service fica alinhado ao fluxo de conversa natural e o Chatbot Operations consegue entender a resposta e concluir o registro do pedido.
