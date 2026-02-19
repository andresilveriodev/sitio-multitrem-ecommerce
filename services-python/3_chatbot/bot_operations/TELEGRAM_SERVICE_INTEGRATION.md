# Integração com Telegram Service

Este documento descreve como o Telegram Service deve processar as respostas do Chatbot Service para enviar mensagens com botões ao Telegram.

## 🎯 Comportamento Profissional

O Chatbot Service retorna flags para controlar o comportamento das mensagens:

- **`edit_message: true`** → Sempre usar `editMessageText` (editar mensagem existente)
- **`edit_message: false`** ou ausente → Usar `sendMessage` (criar nova mensagem)

**IMPORTANTE**: Para manter o chat limpo e profissional, sempre edite a mensagem quando `edit_message: true`. Isso evita criar múltiplas linhas no chat.

### Fluxo de Navegação

```
1. Usuário digita /menu
   → Chatbot retorna: edit_message: false
   → Telegram Service usa: sendMessage
   → Cria nova mensagem com Menu Principal

2. Usuário clica "📦 Pedidos"
   → Chatbot retorna: edit_message: true, message_id: 456
   → Telegram Service usa: editMessageText
   → Edita a mesma mensagem (Menu Principal → Menu Pedidos)

3. Usuário clica "🔙 Voltar"
   → Chatbot retorna: edit_message: true, message_id: 456
   → Telegram Service usa: editMessageText
   → Edita a mesma mensagem (Menu Pedidos → Menu Principal)
```

**Resultado**: Apenas 1 mensagem no chat que vai sendo atualizada. Chat limpo e profissional! ✨

## 📋 Visão Geral

O fluxo de comunicação é:

```
Telegram App → Telegram Service → Chatbot Service → Telegram Service → Telegram App
```

O **Chatbot Service** processa mensagens e retorna respostas JSON que podem incluir botões inline do Telegram. O **Telegram Service** é responsável por:

1. Receber webhooks do Telegram
2. Chamar o Chatbot Service
3. Processar a resposta JSON
4. Enviar mensagem de volta para o Telegram usando a Bot API

## 🔄 Fluxo de Processamento

### 1. Receber Webhook do Telegram

O Telegram Service recebe updates do Telegram no formato:

```json
{
  "update_id": 123,
  "message": {
    "message_id": 456,
    "from": {
      "id": 789,
      "username": "usuario",
      "first_name": "Nome"
    },
    "chat": {
      "id": 789,
      "type": "private"
    },
    "text": "/menu"
  }
}
```

### 2. Chamar Chatbot Service

Enviar requisição para o Chatbot Service:

```python
# Exemplo em Python
import httpx

async def process_telegram_message(update: dict):
    # Extrair dados do Telegram
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    
    # Chamar Chatbot Service
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://chatbot-service:8011/chatbot/process-message-authenticated",
            headers={
                "X-Telegram-Bot-Token": TELEGRAM_BOT_TOKEN,
                "Authorization": f"Bearer {keycloak_token}"  # Token do usuário
            },
            json={
                "message": message,
                "update_id": update.get("update_id")
            }
        )
        
        chatbot_response = response.json()
        return chatbot_response
```

### 3. Processar Resposta do Chatbot Service

A resposta do Chatbot Service pode incluir botões. Verificar as flags:

```python
def process_chatbot_response(chatbot_response: dict, chat_id: int, message_id: Optional[int] = None):
    """
    Processa resposta do Chatbot Service e prepara payload para Telegram
    
    Args:
        chatbot_response: Resposta JSON do Chatbot Service
        chat_id: ID do chat do Telegram
        message_id: ID da mensagem a ser editada (se disponível)
        
    Returns:
        dict: Payload para enviar ao Telegram Bot API e flag de edição
    """
    # Payload base
    payload = {
        "chat_id": chat_id,
        "text": chatbot_response.get("response", "")
    }
    
    # Verificar se tem botões usando flag explícita
    if chatbot_response.get("has_keyboard") and chatbot_response.get("reply_markup"):
        payload["reply_markup"] = chatbot_response["reply_markup"]
        
        # Log para depuração
        keyboard_type = chatbot_response.get("keyboard_type", "inline")
        buttons_count = len(chatbot_response["reply_markup"].get("inline_keyboard", []))
        logger.info(
            f"Adicionando teclado {keyboard_type} com {buttons_count} linhas de botões"
        )
    
    # Verificar se deve editar mensagem
    edit_message = chatbot_response.get("edit_message", False)
    message_id_to_edit = chatbot_response.get("message_id") or message_id
    
    return {
        "payload": payload,
        "edit_message": edit_message and message_id_to_edit is not None,
        "message_id": message_id_to_edit
    }
```

### 4. Enviar ou Editar Mensagem no Telegram

Enviar ou editar mensagem usando a Bot API do Telegram:

```python
async def send_or_edit_telegram_message(processed: dict):
    """
    Envia ou edita mensagem no Telegram usando Bot API
    
    Args:
        processed: Dict retornado por process_chatbot_response
                  com payload, edit_message e message_id
    """
    payload = processed["payload"]
    
    if processed["edit_message"] and processed["message_id"]:
        # Editar mensagem existente (mantém chat limpo)
        payload["message_id"] = processed["message_id"]
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
        logger.info("Editando mensagem", message_id=processed["message_id"])
    else:
        # Enviar nova mensagem
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        logger.info("Enviando nova mensagem")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
```

## 📝 Formato da Resposta do Chatbot Service

### Resposta com Botões

```json
{
  "success": true,
  "response": "Menu Principal - Selecione uma opção:",
  "has_keyboard": true,
  "keyboard_type": "inline",
  "reply_markup": {
    "inline_keyboard": [
      [
        {"text": "📦 Pedidos", "callback_data": "menu_pedidos"},
        {"text": "🚚 Entregas", "callback_data": "menu_entregas"}
      ],
      [
        {"text": "🥬 Estoque", "callback_data": "menu_estoque"},
        {"text": "💰 Financeiro", "callback_data": "menu_financeiro"}
      ],
      [
        {"text": "👤 Clientes", "callback_data": "menu_clientes"},
        {"text": "⚙️ Admin", "callback_data": "menu_admin"}
      ]
    ]
  },
  "metadata": {
    "user_id": "789",
    "username": "usuario",
    "command_id": "show_menu",
    "is_command": true
  }
}
```

### Resposta sem Botões

```json
{
  "success": true,
  "response": "Produto cadastrado com sucesso!",
  "has_keyboard": false,
  "metadata": {
    "user_id": "789",
    "username": "usuario"
  }
}
```

## 🔑 Campos Importantes

### Flags Explícitas

- **`has_keyboard`** (boolean): Indica se a resposta contém botões
  - `true`: Usar `reply_markup` ao enviar mensagem
  - `false` ou ausente: Enviar mensagem sem botões

- **`keyboard_type`** (string): Tipo de teclado
  - `"inline"`: Botões inline (aparecem abaixo da mensagem)
  - `"reply"`: Teclado de resposta (substitui o teclado padrão)

- **`edit_message`** (boolean): Indica se deve editar mensagem existente
  - `true`: Usar `editMessageText` ao invés de `sendMessage`
  - `false` ou ausente: Criar nova mensagem
  - **IMPORTANTE**: Quando `true`, sempre usar `editMessageText` para manter chat limpo

- **`message_id`** (integer): ID da mensagem a ser editada
  - Presente quando `edit_message: true`
  - Obrigatório para `editMessageText`

### Campos de Botões

- **`reply_markup`** (object): Formato direto para Telegram Bot API
  - Deve ser usado diretamente no campo `reply_markup` do `sendMessage`
  - Formato: `{"inline_keyboard": [[{...}, {...}], [...]]}`

- **`telegram_keyboard`** (object): Alias para `reply_markup` (compatibilidade)

## 💻 Exemplo Completo

```python
import httpx
import structlog

logger = structlog.get_logger(__name__)

TELEGRAM_BOT_TOKEN = "seu_token_aqui"
CHATBOT_SERVICE_URL = "http://chatbot-service:8011"

async def handle_telegram_webhook(update: dict, keycloak_token: str):
    """
    Processa webhook do Telegram completo (mensagens e callbacks)
    """
    try:
        # Verificar se é callback_query (clique em botão)
        callback_query = update.get("callback_query")
        if callback_query:
            return await handle_callback_query(callback_query, keycloak_token)
        
        # Processar mensagem normal
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if not text:
            return {"ok": False, "error": "Mensagem vazia"}
        
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
                    "message": message,
                    "update_id": update.get("update_id")
                }
            )
            chatbot_response.raise_for_status()
            chatbot_data = chatbot_response.json()
        
        # Preparar payload para Telegram
        telegram_payload = {
            "chat_id": chat_id,
            "text": chatbot_data.get("response", "Resposta vazia")
        }
        
        # Adicionar botões se existirem
        if chatbot_data.get("has_keyboard") and chatbot_data.get("reply_markup"):
            telegram_payload["reply_markup"] = chatbot_data["reply_markup"]
            logger.info(
                "Enviando mensagem com botões",
                chat_id=chat_id,
                keyboard_type=chatbot_data.get("keyboard_type"),
                buttons_count=len(chatbot_data["reply_markup"].get("inline_keyboard", []))
            )
        
        # Enviar para Telegram
        async with httpx.AsyncClient() as client:
            telegram_response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json=telegram_payload
            )
            telegram_response.raise_for_status()
            return telegram_response.json()
            
    except httpx.HTTPStatusError as e:
        logger.error(
            "Erro HTTP ao processar mensagem",
            status_code=e.response.status_code,
            response_text=e.response.text
        )
        return {"ok": False, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error("Erro ao processar webhook", error=str(e), exc_info=True)
        return {"ok": False, "error": str(e)}


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
        
        # Chamar Chatbot Service com callback_query
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
        
        # Responder ao callback (obrigatório)
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                json={
                    "callback_query_id": callback_id,
                    "text": "",  # Vazio para não mostrar popup
                    "show_alert": False
                }
            )
        
        # Preparar payload para atualizar/enviar mensagem
        telegram_payload = {
            "chat_id": chat_id,
            "text": chatbot_data.get("response", "")
        }
        
        # Adicionar botões se existirem
        if chatbot_data.get("has_keyboard") and chatbot_data.get("reply_markup"):
            telegram_payload["reply_markup"] = chatbot_data["reply_markup"]
        
        # Verificar se deve editar mensagem existente (mantém chat limpo)
        edit_message = chatbot_data.get("edit_message", False)
        message_id_to_edit = chatbot_data.get("message_id") or message_id
        
        if edit_message and message_id_to_edit:
            # Editar mensagem existente (RECOMENDADO - mantém chat limpo)
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

## 🔔 Processar Callback de Botões

Quando o usuário clica em um botão, o Telegram envia um `callback_query`:

```json
{
  "update_id": 124,
  "callback_query": {
    "id": "123456",
    "from": {
      "id": 789,
      "username": "usuario"
    },
    "message": {
      "message_id": 456,
      "chat": {"id": 789}
    },
    "data": "menu_pedidos"
  }
}
```

### Processamento no Telegram Service

O Telegram Service deve:

1. **Enviar `callback_query` para o Chatbot Service** (mesmo endpoint)
2. **Receber resposta com novos botões ou mensagem**
3. **Responder ao callback** usando `answerCallbackQuery`
4. **Enviar nova mensagem** ou **atualizar mensagem existente**

```python
async def handle_callback_query(callback_query: dict, keycloak_token: str):
    """Processa clique em botão"""
    callback_id = callback_query.get("id")
    callback_data = callback_query.get("data")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    
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
                "callback_query": callback_query  # Enviar callback_query completo
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
    
    # 3. Preparar payload para enviar/atualizar mensagem
    telegram_payload = {
        "chat_id": chat_id,
        "text": chatbot_data.get("response", "")
    }
    
    # 4. Adicionar botões se existirem
    if chatbot_data.get("has_keyboard") and chatbot_data.get("reply_markup"):
        telegram_payload["reply_markup"] = chatbot_data["reply_markup"]
    
        # 5. Verificar se deve editar mensagem existente
        if chatbot_data.get("edit_message") and chatbot_data.get("message_id"):
            # Editar mensagem existente (recomendado - mantém chat limpo)
            telegram_payload["message_id"] = chatbot_data["message_id"]
            async with httpx.AsyncClient() as client:
                telegram_response = await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText",
                    json=telegram_payload
                )
                telegram_response.raise_for_status()
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
```

### Callbacks Disponíveis

#### Menu Principal
- `menu_pedidos` - Menu de Pedidos
- `menu_entregas` - Menu de Entregas
- `menu_estoque` - Menu de Estoque
- `menu_financeiro` - Menu Financeiro
- `menu_clientes` - Menu de Clientes
- `menu_admin` - Menu Administrativo
- `menu_voltar` - Voltar ao menu principal

#### Menu de Pedidos
- `pedido_novo` - Criar novo pedido
- `pedido_listar` - Listar pedidos
- `pedido_buscar` - Buscar pedido
- `pedido_editar` - Editar pedido
- `pedido_resumo` - Resumo por data

## ⚠️ Importante

1. **Sempre verificar `has_keyboard`**: Use a flag explícita antes de adicionar `reply_markup`
2. **Usar `reply_markup` diretamente**: O campo já está no formato correto para Telegram Bot API
3. **Tratar erros**: Se o Chatbot Service retornar erro, não enviar mensagem com botões
4. **Logs**: Registrar quando botões são adicionados para depuração

## 🧪 Teste

Para testar se os botões estão sendo enviados corretamente:

1. Enviar `/menu` no Telegram
2. Verificar logs do Telegram Service para ver se `has_keyboard: true`
3. Verificar se `reply_markup` está sendo incluído no payload
4. Verificar resposta da Bot API do Telegram

Se os botões não aparecerem, verificar:
- Se `has_keyboard` está `true` na resposta
- Se `reply_markup` está sendo incluído no payload
- Se o formato do `inline_keyboard` está correto
- Se há erros na resposta da Bot API do Telegram
