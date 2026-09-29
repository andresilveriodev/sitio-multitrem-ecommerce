# Ajustes do AI Service para fluxo de registro de pedido

Documento para o time do **AI Service (Chatbot Middleware)** alinhar o comportamento do endpoint **`POST /ai/chat`** com o **Chatbot Operations**, sem criar novo endpoint.

---

## 1. Contexto

- O **Chatbot Operations** já identifica a intenção "criar pedido" (ex.: "quero registrar o pedido do Adriano") e envia a conversa para o **mesmo** `POST /ai/chat`.
- A mensagem recebida pelo AI Service pode vir **com contexto de pedido** no próprio texto do prompt, no formato descrito abaixo.
- O AI Service deve **responder de forma natural** e, quando extrair dados do pedido, **incluir uma linha estruturada** no final da resposta para o chatbot interpretar e persistir.

**Não é necessário** criar endpoint novo (`/ai/extract-order`). Tudo segue o fluxo natural de chat.

---

## 2. Como o Chatbot chama o AI Service

O Chatbot envia para `POST /ai/chat` um único campo de mensagem (`message`) que contém um **prompt montado**, por exemplo:

```text
[Contexto: você está ajudando a registrar um pedido da horta. Pedido atual (o que já foi extraído): {"customer_name": null, "contact_name": null, "items": []}. Responda de forma natural em português. Se você extrair ou atualizar dados do pedido (nome do cliente, itens com quantidade), termine sua resposta com exatamente uma linha no formato:
ORDER_DATA: {"customer_name": "nome ou null", "items": [{"product_name": "...", "quantity": n}], "can_save_now": true ou false}
Não repita nada além do JSON nessa linha.]

Mensagem do usuário: Quero registrar o pedido do Adriano com 2 alfaces e 1 couve.
```

Ou seja: o AI Service recebe **uma única string** em `message`; dentro dela há o bloco `[Contexto: ...]` e a "Mensagem do usuário: ...".

---

## 3. Comportamento esperado do AI Service

1. **Detectar o contexto de pedido**  
   Quando a mensagem contiver algo como `[Contexto: você está ajudando a registrar um pedido da horta` (ou "Pedido atual", "ORDER_DATA:" nas instruções), tratar como **fluxo de registro de pedido**.

2. **Extrair dados da "Mensagem do usuário"**  
   - Nome do cliente (ex.: "Adriano", "Dona Maria").  
   - Itens e quantidades (ex.: "2 alfaces", "1 couve" → `{"product_name": "alface", "quantity": 2}`, etc.).  
   - Considerar o "Pedido atual" já enviado no prompt para **complementar** (ex.: cliente já preenchido, só faltam itens).

3. **Responder em português de forma natural**  
   Ex.: *"Entendi! Pedido do Adriano: 2 alfaces e 1 couve. Quer que eu salve?"*

4. **Incluir a linha ORDER_DATA quando houver dados extraídos**  
   No **final** da resposta, em **uma única linha**, no formato exato:

   ```text
   ORDER_DATA: {"customer_name": "Adriano", "items": [{"product_name": "alface", "quantity": 2}, {"product_name": "couve", "quantity": 1}], "can_save_now": false}
   ```

   - **customer_name**: string com o nome do cliente ou `null` se não tiver.  
   - **items**: lista de objetos com `product_name` (string) e `quantity` (número inteiro).  
   - **can_save_now**:  
     - `true` quando tiver cliente + pelo menos um item e o usuário confirmou (ex.: "pode salvar", "salva", "registra") ou quando a frase já trouxe tudo.  
     - `false` quando ainda faltar informação ou confirmação.

5. **Não incluir ORDER_DATA** quando a mensagem for só conversa (ex.: "obrigado", "cancelar") ou quando não houver nenhum dado de pedido a extrair. Nesse caso, responder só o texto natural.

---

## 4. Formato exato da linha ORDER_DATA

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

## 5. Regras práticas para o modelo

- **Sempre** responder em português, de forma clara e curta.  
- **Só** incluir a linha `ORDER_DATA:` quando a mensagem for sobre registro de pedido e houver algo a extrair ou atualizar (cliente e/ou itens).  
- **Mesclar** com o "Pedido atual" enviado no prompt: se o cliente já veio em turno anterior, manter; se o usuário disser novos itens, acrescentar aos itens existentes.  
- **can_save_now = true** apenas quando: (1) tiver `customer_name` preenchido, (2) tiver pelo menos um item com quantidade > 0, e (3) o usuário tiver confirmado (ou a frase já trouxer pedido completo e inequívoco).  
- Nomes de produtos: usar termos que o e-commerce reconheça (ex.: "alface", "couve", "rúcula", "coentro"). O Chatbot faz busca por nome no sistema; variações próximas ajudam.

---

## 6. Resumo para implementação

| Item | O que fazer |
|------|-------------|
| Endpoint | Manter só `POST /ai/chat`. Nenhum endpoint novo. |
| Entrada | Receber `message` (string) que pode conter `[Contexto: ... pedido da horta ...]` e `Mensagem do usuário: ...`. |
| Resposta | Texto natural em português. Quando for fluxo de pedido e houver dados extraídos, terminar com uma linha: `ORDER_DATA: <JSON>`. |
| JSON | `{"customer_name": string|null, "items": [{"product_name": string, "quantity": number}], "can_save_now": boolean}`. |
| Uso no Chatbot | O Chatbot interpreta a linha ORDER_DATA, atualiza estado e persiste o pedido quando `can_save_now === true` e há cliente + itens. |

Com esses ajustes, o AI Service fica alinhado ao fluxo de conversa natural e o Chatbot Operations consegue entender a resposta e concluir o registro do pedido.

---

## 7. Implementação no ai_operations

- **Detecção de contexto:** em `services/ai_service.py`, a função `_is_order_registration_context(message)` considera a presença de "contexto:" e de marcadores como "registrar um pedido", "pedido da horta", "Pedido atual", "ORDER_DATA:", "Mensagem do usuário:".
- **Instruções de sistema:** quando o contexto de pedido é detectado, o método `send()` injeta uma mensagem de sistema (`_ORDER_FLOW_SYSTEM_PROMPT`) antes da mensagem do usuário, reforçando o formato ORDER_DATA e as regras (português, mesclar com pedido atual, can_save_now).
- A resposta da IA é devolvida integralmente; o Chatbot é responsável por localizar a linha `ORDER_DATA:`, extrair o JSON e ocultá-la do usuário.
