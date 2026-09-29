# Base de intents: aprendizado com conversas reais

O **Chatbot Operations** envia **todas** as intents identificadas pelo router para o **AI Service** em cada chamada a `POST /ai/chat`. O AI Service pode persistir esses dados e usar para:

- Construir uma base de exemplos (mensagem real → intent)
- Treinar ou refinar um classificador de intents
- Reduzir erros de identificação ao longo do tempo

---

## 1. Intents enviadas pelo Chatbot (vocabulário)

O router do Chatbot usa as seguintes intents. Todas podem aparecer no campo `intent` do payload:

| Intent | Descrição típica |
|--------|-------------------|
| `menu` | Abrir menu principal, início, home |
| `pedidos` | Listar/consultar pedidos, encomendas |
| `criar_pedido` | Registrar novo pedido, "quero registrar o pedido do X" |
| `estoque` | Consultar estoque, inventário, disponibilidade |
| `financeiro` | Resumo financeiro, dinheiro, faturamento |
| `hoje` | Resumo do dia, resumo operacional |
| `cliente` | Buscar/cadastrar cliente |
| `produto` | Cadastrar/listar produto |
| `cadastro` | Cadastros em geral |
| `cumprimento` | Oi, olá, bom dia, tudo bem |
| `conversa` | Conversa natural (quero, preciso, como, obrigado) |
| `duvida` | Intent não clara; router pede ajuda ao AI para classificar |
| `unknown` | Fluxo ativo (ex.: formulário) ou não identificado |

O campo `intent_reason` traz o motivo da classificação, por exemplo:

- `command:/menu`, `greeting`, `create_order_intent`, `order_text_pattern`
- `keyword:pedidos`, `conversation_pattern`, `unclear_intent`, `active_flow:pedido_inline`

---

## 2. Contrato do request (resumo)

```json
{
  "message": "string (obrigatório)",
  "intent": "string (opcional)",
  "confidence": 0.0 a 1.0 (opcional),
  "intent_reason": "string (opcional)",
  "user_id": "string (opcional)"
}
```

- **message**: prompt completo (pode incluir contexto + mensagem do usuário).
- **intent**: uma das intents da tabela acima.
- **confidence**: confiança do router (alta = decisão mais segura).
- **intent_reason**: motivo (comando, keyword, padrão, etc.).
- **user_id**: identificador do usuário (ex.: Telegram); útil para anonimizar em logs.

---

## 3. O que persistir no AI Service (sugestão)

Criar uma tabela ou coleção (ex.: `intent_examples` ou `chat_logs`) com:

- `message` (ou hash/trecho para privacidade)
- `intent`
- `confidence`
- `intent_reason`
- `user_id` (ou anonimizado)
- `timestamp`
- Opcional: `reply_length`, `model_used`, se houve ORDER_DATA, etc.

Com isso dá para:

1. **Treinar/ajustar classificador**: exemplos reais (mensagem → intent) com confiança.
2. **Analisar erros**: filtrar por `confidence` baixa ou por intents que geraram reclamações.
3. **Evoluir a base**: adicionar novos padrões ou intents quando aparecerem nas conversas.

---

## 4. Compatibilidade

- Se o request **não** tiver `intent`, `confidence`, `intent_reason` ou `user_id`, o AI Service deve continuar funcionando normalmente (só `message` obrigatório).
- Os campos extras são **opcionais** e para uso em aprendizado e contexto.

Com isso, o AI Service passa a receber todas as intents do Chatbot e pode ir construindo a base de dados de intents e aprendendo com as conversas reais.
