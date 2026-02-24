# 📢 Comunicação: Alterações no Telegram Service

**Data:** 2026-02-19  
**Serviço:** Telegram Service  
**Impacto:** Chatbot Service  

---

## 🎯 Resumo Executivo

O Telegram Service foi atualizado para tratar corretamente a flag `delete_message` e interceptar callbacks de "sair" localmente. Isso resolve o problema de mensagens de erro sendo exibidas quando o usuário clica no botão "❌ Sair" dos menus.

---

## ✅ O que mudou no Telegram Service

### 1. Interceptação Local do Callback "sair"

O Telegram Service agora intercepta e trata localmente os callbacks relacionados a "sair" antes de enviar ao Chatbot Service.

**Callbacks interceptados (tratados localmente):**
- `"sair"`
- `"action:sair"`
- `"exit"`
- `"menu_sair"`
- `"action:exit"`
- `"close"`
- `"action:close"`

**Comportamento:**
- Responde ao callback (`answerCallbackQuery`) para remover loading
- Tenta deletar a mensagem do menu usando `deleteMessage`
- Se não conseguir deletar, edita a mensagem removendo os botões
- **NÃO envia ao Chatbot Service** - retorna imediatamente

**Implicação para o Chatbot Service:**
- ❌ **NÃO receberá mais** callbacks com `callback_data` igual a "sair", "menu_sair", "action:close", etc.
- ✅ Esses callbacks são tratados completamente no Telegram Service

---

### 2. Tratamento Correto da Flag `delete_message`

O Telegram Service agora verifica a flag `delete_message` **ANTES** de processar qualquer texto, edição ou envio de mensagem.

**Ordem de processamento (CORRIGIDA):**

```
1. Recebe resposta do Chatbot Service
2. Responde ao callback (answerCallbackQuery) ← Obrigatório
3. ✅ VERIFICA delete_message PRIMEIRO ← NOVA ORDEM
4. Se delete_message = true → Deleta mensagem e RETORNA (não continua)
5. Se delete_message = false → Continua com edit_message ou sendMessage
```

**Campos suportados na resposta:**
- `delete_message` (boolean): Indica se deve deletar a mensagem
- `message_id` (integer): ID da mensagem a ser deletada
- `chat_id` (integer, opcional): ID do chat (usa do callback se não fornecido)

**Comportamento quando `delete_message: true`:**
- ✅ Deleta a mensagem usando `deleteMessage` da API do Telegram
- ✅ Retorna imediatamente (não processa texto, não edita, não envia nova mensagem)
- ✅ Ignora qualquer texto em `response` (mesmo que contenha erro)

---

### 3. Tratamento de `delete_message` em Casos de Erro

Quando o Chatbot Service retorna erro (`success: false`), o Telegram Service verifica se também retornou `delete_message: true`. Se sim, deleta a mensagem mesmo com erro, **sem exibir o texto de erro**.

**Exemplo:**
```json
{
  "success": false,
  "response": "Menu 'sair' não encontrado",  // ← IGNORADO
  "delete_message": true,  // ← RESPEITADO
  "message_id": 12345
}
```

**Resultado:** Mensagem é deletada, texto de erro **não é exibido**.

---

## 📋 O que o Chatbot Service precisa saber

### ✅ 1. Flag `delete_message` é totalmente suportada

Quando você retornar `delete_message: true`, o Telegram Service:
- ✅ Verifica essa flag **ANTES** de qualquer processamento
- ✅ Deleta a mensagem corretamente
- ✅ Não tenta editar ou enviar nova mensagem
- ✅ Ignora qualquer texto em `response`

**Formato esperado:**
```json
{
  "success": true,
  "response": "",  // Vazio ou qualquer texto (será ignorado)
  "delete_message": true,
  "message_id": 12345,  // ID da mensagem a deletar
  "chat_id": 67890,  // Opcional - usa do callback se não fornecido
  "callback_query_id": "...",  // Para callbacks
  "has_keyboard": false
}
```

### ✅ 2. Callbacks de "sair" não chegam mais ao Chatbot Service

Os seguintes callbacks são interceptados e tratados localmente pelo Telegram Service:
- `"sair"`
- `"menu_sair"`
- `"action:close"`
- `"action:sair"`
- `"exit"`
- `"close"`

**Você não precisa processar esses callbacks** - eles nunca chegarão ao Chatbot Service.

### ✅ 3. `chat_id` é opcional na resposta

Se você não retornar `chat_id` na resposta, o Telegram Service usa o `chat_id` do `callback_query` ou `message` original.

**Recomendação:** Retorne `chat_id` quando disponível para maior clareza, mas não é obrigatório.

---

## 🔄 Fluxo Atualizado

### Fluxo para Callback "sair" (interceptado localmente):

```
Usuário clica "❌ Sair"
    ↓
Telegram Service recebe callback_query
    ↓
Verifica se callback_data é "sair", "menu_sair", etc.
    ↓
✅ SIM → Trata localmente:
    - Responde ao callback
    - Deleta mensagem
    - Retorna (NÃO envia ao Chatbot Service)
    ↓
❌ NÃO → Envia ao Chatbot Service normalmente
```

### Fluxo para outros callbacks:

```
Usuário clica em botão
    ↓
Telegram Service recebe callback_query
    ↓
Envia ao Chatbot Service
    ↓
Chatbot Service processa e retorna resposta
    ↓
Telegram Service recebe resposta
    ↓
Responde ao callback (answerCallbackQuery)
    ↓
✅ Verifica delete_message PRIMEIRO
    ↓
Se delete_message = true:
    - Deleta mensagem
    - Retorna (não continua)
    ↓
Se delete_message = false:
    - Verifica edit_message
    - Edita ou envia nova mensagem
```

---

## 📝 Exemplos de Respostas

### Exemplo 1: Deletar mensagem (callback "sair")

**Chatbot Service retorna:**
```json
{
  "success": true,
  "response": "",
  "delete_message": true,
  "message_id": 40759,
  "chat_id": 178999227,
  "callback_query_id": "768795828542639505",
  "has_keyboard": false
}
```

**Telegram Service:**
1. Responde ao callback (`answerCallbackQuery`)
2. Deleta mensagem (`deleteMessage`)
3. Retorna (não processa mais nada)

**Resultado:** Mensagem deletada, chat limpo ✅

---

### Exemplo 2: Editar mensagem (callback normal)

**Chatbot Service retorna:**
```json
{
  "success": true,
  "response": "📦 Menu de Pedidos - Selecione uma opção:",
  "delete_message": false,
  "edit_message": true,
  "message_id": 40759,
  "has_keyboard": true,
  "reply_markup": {
    "inline_keyboard": [[...]]
  }
}
```

**Telegram Service:**
1. Responde ao callback (`answerCallbackQuery`)
2. Verifica `delete_message` (false) → continua
3. Edita mensagem (`editMessageText`)
4. Retorna

**Resultado:** Mensagem editada com novo menu ✅

---

### Exemplo 3: Erro com delete_message

**Chatbot Service retorna:**
```json
{
  "success": false,
  "response": "Menu 'sair' não encontrado",  // ← Será ignorado
  "delete_message": true,  // ← Será respeitado
  "message_id": 40759
}
```

**Telegram Service:**
1. Responde ao callback (`answerCallbackQuery`)
2. Verifica `delete_message` (true) → deleta mensagem
3. Retorna (não exibe texto de erro)

**Resultado:** Mensagem deletada, erro não exibido ✅

---

## ⚠️ Pontos de Atenção

### 1. Ordem de verificação é crítica

O Telegram Service agora verifica `delete_message` **ANTES** de processar texto. Isso significa que mesmo que você retorne um texto de erro, se `delete_message: true`, o texto será ignorado e a mensagem será deletada.

### 2. Callbacks de "sair" não chegam ao Chatbot Service

Não espere receber callbacks com `callback_data` igual a "sair", "menu_sair", etc. Eles são tratados localmente pelo Telegram Service.

### 3. `message_id` deve ser fornecido

Para deletar uma mensagem, o Telegram Service precisa do `message_id`. Você pode:
- Retornar `message_id` na resposta
- O Telegram Service usará o `message_id` do `callback_query` original se você não fornecer

---

## 🧪 Como testar

### Teste 1: Botão "Sair" funciona
1. Abra um menu no Telegram
2. Clique no botão "❌ Sair"
3. ✅ Mensagem deve ser deletada
4. ✅ Nenhuma mensagem de erro deve aparecer

### Teste 2: Flag delete_message funciona
1. Faça o Chatbot Service retornar `delete_message: true`
2. ✅ Mensagem deve ser deletada
3. ✅ Nenhum texto deve ser exibido

### Teste 3: Outros callbacks funcionam normalmente
1. Clique em qualquer outro botão do menu
2. ✅ Menu deve ser atualizado normalmente
3. ✅ Nenhuma mensagem deve ser deletada

---

## 📞 Suporte

Se houver dúvidas sobre essas alterações, consulte:
- `docs/TELEGRAM_SERVICE_DELETE_MESSAGE.md` - Documentação técnica completa
- `TELEGRAM_SERVICE_INTEGRATION.md` - Documentação de integração atualizada

---

## ✅ Checklist para o Chatbot Service

- [x] Telegram Service intercepta callbacks de "sair" localmente
- [x] Telegram Service verifica `delete_message` antes de processar texto
- [x] Telegram Service deleta mensagem quando `delete_message: true`
- [x] Telegram Service ignora texto quando `delete_message: true`
- [x] Telegram Service trata `delete_message` mesmo em caso de erro
- [x] Documentação atualizada

**Status:** ✅ Implementado e testado no Telegram Service

---

**Última atualização:** 2026-02-19
