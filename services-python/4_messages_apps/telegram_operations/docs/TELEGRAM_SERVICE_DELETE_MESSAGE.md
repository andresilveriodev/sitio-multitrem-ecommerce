# 🔧 CORREÇÃO CRÍTICA: Tratamento de `delete_message` no Telegram Service

## ⚠️ Problema identificado

O Chatbot Service retorna `delete_message: true` quando o usuário clica no botão "❌ Sair" dos menus, mas o Telegram Service não está tratando essa flag corretamente. Isso causa:

1. Mensagem de erro "Menu 'sair' não encontrado" sendo exibida
2. Mensagem do menu não sendo excluída
3. Tentativa de editar mensagem com texto vazio, gerando erro

## 📋 O que o Chatbot Service retorna

Quando o usuário clica em "❌ Sair", o Chatbot Service retorna:

```json
{
  "success": true,
  "response": "",  // ← Resposta vazia (não exibir nada)
  "callback_query_id": "768795828542639505",
  "delete_message": true,  // ← FLAG CRÍTICA: deve excluir mensagem
  "message_id": 40759,  // ← ID da mensagem a ser deletada
  "chat_id": 178999227,
  "has_keyboard": false,
  "metadata": {
    "user_id": "178999227",
    "callback_data": "menu_sair",
    "is_callback": true
  }
}
```

## ✅ Solução: ordem de verificação

A verificação de `delete_message` deve ser a primeira ação, antes de qualquer processamento de texto, edição ou envio de mensagem.

### Ordem correta de processamento:

```
1. Receber resposta do Chatbot Service
2. Responder ao callback (answerCallbackQuery) ← Obrigatório
3. ✅ VERIFICAR delete_message PRIMEIRO ← CRÍTICO
4. Se delete_message = true → Excluir e RETORNAR (não continuar)
5. Se delete_message = false → Continuar com edit_message ou sendMessage
```

## 💻 Código correto para implementar

### Para callbacks (handle_callback_query):

```python
async def handle_callback_query(callback_query: dict, keycloak_token: str):
    """Processa callback_query (clique em botão)"""
    try:
        callback_id = callback_query.get("id")
        callback_data = callback_query.get("data", "")
        chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
        message_id = callback_query.get("message", {}).get("message_id")
        
        logger.info(
            "Processando callback",
            callback_id=callback_id,
            callback_data=callback_data,
            chat_id=chat_id
        )
        
        # 1. Chamar Chatbot Service com callback_query
        async with httpx.AsyncClient(timeout=30.0) as client:
            chatbot_response = await client.post(
                f"{CHATBOT_SERVICE_URL}/chatbot/process-message-authenticated",
                headers={
                    "X-Telegram-Bot-Token": TELEGRAM_BOT_TOKEN,
                    "Authorization": f"Bearer {keycloak_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "callback_query": callback_query
                }
            )
            chatbot_response.raise_for_status()
            chatbot_data = chatbot_response.json()
        
        # 2. Responder ao callback (obrigatório para remover loading)
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                json={
                    "callback_query_id": callback_id,
                    "text": "",  # Vazio para não mostrar popup
                    "show_alert": False
                }
            )
        
        # 3. ✅ VERIFICAR delete_message PRIMEIRO (ANTES de qualquer outra coisa)
        delete_message = chatbot_data.get("delete_message", False)
        message_id_to_delete = chatbot_data.get("message_id") or message_id
        chat_id_to_delete = chatbot_data.get("chat_id") or chat_id
        
        if delete_message and message_id_to_delete and chat_id_to_delete:
            # Excluir mensagem (NÃO editar ou enviar nova)
            logger.info(
                "Excluindo mensagem do chat",
                message_id=message_id_to_delete,
                chat_id=chat_id_to_delete,
                callback_data=callback_data
            )
            async with httpx.AsyncClient() as client:
                telegram_response = await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage",
                    json={
                        "chat_id": chat_id_to_delete,
                        "message_id": message_id_to_delete
                    }
                )
                telegram_response.raise_for_status()
                logger.info(
                    "Mensagem excluída com sucesso",
                    message_id=message_id_to_delete,
                    chat_id=chat_id_to_delete
                )
                # RETORNAR IMEDIATAMENTE - não processar mais nada
                return telegram_response.json()
        
        # 4. Se não for para excluir, continuar com processamento normal
        # Preparar payload para atualizar/enviar mensagem
        telegram_payload = {
            "chat_id": chat_id,
            "text": chatbot_data.get("response", "")
        }
        
        # 5. Adicionar botões se existirem
        if chatbot_data.get("has_keyboard") and chatbot_data.get("reply_markup"):
            telegram_payload["reply_markup"] = chatbot_data["reply_markup"]
        
        # 6. Verificar se deve editar mensagem existente
        edit_message = chatbot_data.get("edit_message", False)
        message_id_to_edit = chatbot_data.get("message_id") or message_id
        
        if edit_message and message_id_to_edit:
            # Editar mensagem existente (mantém chat limpo)
            telegram_payload["message_id"] = message_id_to_edit
            async with httpx.AsyncClient() as client:
                telegram_response = await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText",
                    json=telegram_payload
                )
                telegram_response.raise_for_status()
                logger.info(
                    "Mensagem editada com sucesso",
                    message_id=message_id_to_edit,
                    chat_id=chat_id
                )
                return telegram_response.json()
        else:
            # Enviar nova mensagem (apenas se não tiver message_id)
            async with httpx.AsyncClient() as client:
                telegram_response = await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json=telegram_payload
                )
                telegram_response.raise_for_status()
                return telegram_response.json()
                
    except httpx.HTTPStatusError as e:
        logger.error(
            "Erro HTTP ao processar callback",
            status_code=e.response.status_code,
            response_text=e.response.text
        )
        return {"ok": False, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error("Erro ao processar callback", error=str(e), exc_info=True)
        return {"ok": False, "error": str(e)}
```

### Para mensagens normais (handle_message):

```python
async def handle_message(message: dict, keycloak_token: str):
    """Processa mensagem normal do Telegram"""
    try:
        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")
        
        # Chamar Chatbot Service
        async with httpx.AsyncClient(timeout=30.0) as client:
            chatbot_response = await client.post(
                f"{CHATBOT_SERVICE_URL}/chatbot/process-message-authenticated",
                headers={
                    "X-Telegram-Bot-Token": TELEGRAM_BOT_TOKEN,
                    "Authorization": f"Bearer {keycloak_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "message": message
                }
            )
            chatbot_response.raise_for_status()
            chatbot_data = chatbot_response.json()
        
        # ✅ VERIFICAR delete_message (mesmo para mensagens normais)
        delete_message = chatbot_data.get("delete_message", False)
        message_id_to_delete = chatbot_data.get("message_id") or message_id
        chat_id_to_delete = chatbot_data.get("chat_id") or chat_id
        
        if delete_message and message_id_to_delete and chat_id_to_delete:
            # Excluir mensagem
            async with httpx.AsyncClient() as client:
                telegram_response = await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage",
                    json={
                        "chat_id": chat_id_to_delete,
                        "message_id": message_id_to_delete
                    }
                )
                telegram_response.raise_for_status()
                return telegram_response.json()
        
        # Continuar com processamento normal...
        # (enviar resposta, etc.)
        
    except Exception as e:
        logger.error("Erro ao processar mensagem", error=str(e), exc_info=True)
        return {"ok": False, "error": str(e)}
```

## 🎯 Pontos críticos

1. ✅ Verificar `delete_message` **ANTES** de qualquer processamento de texto
2. ✅ Se `delete_message: true`, excluir e **RETORNAR IMEDIATAMENTE** (não continuar)
3. ✅ Usar `message_id` do Chatbot Service ou do `callback_query`
4. ✅ Usar `chat_id` do Chatbot Service ou do `callback_query`
5. ✅ Não editar ou enviar mensagem quando `delete_message: true`
6. ✅ Não exibir o texto de `response` quando `delete_message: true` (mesmo que venha com erro)

## 🧪 Teste

1. Clique no botão "❌ Sair" em qualquer menu
2. Verifique nos logs: `"Mensagem do bot deletada (callback)"` ou `"Excluindo mensagem do chat"`
3. Verifique que a mensagem foi excluída (não editada)
4. Verifique que nenhuma mensagem de erro foi exibida

## 📝 Campos retornados pelo Chatbot Service

Quando `delete_message: true`, o Chatbot Service sempre retorna:

```json
{
  "success": true,
  "response": "",  // Sempre vazio
  "delete_message": true,
  "message_id": 12345,  // ID da mensagem a deletar
  "chat_id": 67890,  // ID do chat
  "callback_query_id": "...",  // Para callbacks
  "has_keyboard": false
}
```

## ⚠️ Erro comum a evitar

**Não fazer isso:**

```python
# ❌ ERRADO - Verifica delete_message depois de preparar payload
telegram_payload = {"chat_id": chat_id, "text": chatbot_data.get("response", "")}
if chatbot_data.get("delete_message"):
    # Já preparou o payload, pode ter processado texto de erro
    delete_message(...)
```

**Fazer isso:**

```python
# ✅ CORRETO - Verifica delete_message PRIMEIRO
if chatbot_data.get("delete_message"):
    delete_message(...)
    return  # Retorna imediatamente
# Só prepara payload se não for para deletar
telegram_payload = {"chat_id": chat_id, "text": chatbot_data.get("response", "")}
```

## ✅ Implementação atual

O código atual em `services/telegram_service.py` já implementa essa lógica corretamente:

- ✅ Verifica `delete_message` antes de processar texto
- ✅ Usa `chat_id` do chatbot_response quando disponível
- ✅ Retorna imediatamente após deletar
- ✅ Trata `delete_message` mesmo quando há erro do chatbot
- ✅ Logs detalhados para depuração

## 📍 Localização no código

- **Callbacks**: `_process_callback_query()` - linhas 431-461
- **Mensagens normais**: `process_update()` - linhas 244-271
- **Tratamento de erros**: `_process_callback_with_chatbot()` - linhas 633-664 e `_process_message_with_chatbot()` - linhas 818-835
