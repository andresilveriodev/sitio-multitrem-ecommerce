# Implementação de Autenticação Keycloak para Chatbot

## Resumo

Foi implementada a validação de token Keycloak para os endpoints exclusivos de conversação com o chatbot, além da criação de um prompt completo para o chatbot operations interagir com os serviços.

## Arquivos Criados

### 1. Prompt do Chatbot
- **`CHATBOT_PROMPT.md`** - Documentação completa com:
  - Contexto do negócio e regras de precificação
  - Lista de todos os endpoints disponíveis
  - Fluxos de conversação detalhados
  - Exemplos de respostas
  - Tratamento de erros

### 2. Módulo de Autenticação Keycloak
- **`auth/__init__.py`** - Exporta funções de autenticação
- **`auth/keycloak.py`** - Implementação da validação de tokens:
  - Validação via endpoint de introspection do Keycloak
  - Dependency `verify_keycloak_token` para uso nas rotas
  - Dependency `get_current_user` que retorna dados do usuário autenticado

### 3. Schemas do Chatbot
- **`schemas/chatbot.py`** - Schemas Pydantic para:
  - `ChannelAccountResponse` - Conta de canal
  - `ConversationCreate/Update/Response` - Conversas
  - `MessageCreate/Response` - Mensagens
  - `ConversationWithMessages` - Conversa com mensagens
  - `ChatbotOrderItem` - Item simplificado para criação de pedidos
  - `ChatbotOrderCreate` - Criação de pedido via chatbot

### 4. Serviço do Chatbot
- **`services/chatbot_service.py`** - Serviço para gerenciar:
  - Contas de canal (get_or_create_channel_account)
  - Conversas (get_or_create_conversation, update_conversation)
  - Mensagens (create_message, get_messages)

### 5. Rotas do Chatbot
- **`routes/chatbot.py`** - Endpoints protegidos com autenticação Keycloak:
  - `GET /api/v1/chatbot/conversations/{conversation_id}` - Busca conversa com mensagens
  - `POST /api/v1/chatbot/conversations` - Cria/obtém conversa
  - `PUT /api/v1/chatbot/conversations/{conversation_id}` - Atualiza conversa
  - `POST /api/v1/chatbot/messages` - Cria mensagem
  - `GET /api/v1/chatbot/messages/{conversation_id}` - Lista mensagens
  - `POST /api/v1/chatbot/orders` - Cria pedido via chatbot
  - `GET /api/v1/chatbot/customers/phone/{phone_e164}` - Busca cliente por telefone

## Arquivos Modificados

### 1. Configurações
- **`config.py`** - Adicionadas configurações do Keycloak:
  - `KEYCLOAK_SERVER_URL`
  - `KEYCLOAK_REALM`
  - `KEYCLOAK_CLIENT_ID`
  - `KEYCLOAK_CLIENT_SECRET`
  - `KEYCLOAK_VALIDATE_TOKEN`

- **`env.example`** - Adicionadas variáveis de ambiente do Keycloak

### 2. Rotas Principais
- **`routes/__init__.py`** - Adicionado `chatbot_router`
- **`main.py`** - Incluído router do chatbot com prefixo `/api/v1`

## Como Funciona a Autenticação

### Validação de Token

Todos os endpoints em `/api/v1/chatbot/*` requerem autenticação via token Keycloak no header:

```
Authorization: Bearer {token}
```

### Processo de Validação

1. O token é extraído do header `Authorization`
2. O token é validado via endpoint de introspection do Keycloak:
   ```
   POST {KEYCLOAK_SERVER_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token/introspect
   ```
3. Se o token for válido e ativo, a requisição prossegue
4. Se inválido, retorna `401 Unauthorized`

### Dados do Usuário

Após validação, os dados do usuário ficam disponíveis via dependency `get_current_user`:
- `username`
- `client_id`
- `preferred_username`
- `roles`
- `token_data` (dados completos do token)

## Configuração

### Variáveis de Ambiente

Adicione ao seu `.env`:

```env
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=sitio-multitrem
KEYCLOAK_CLIENT_ID=commerce-service
KEYCLOAK_CLIENT_SECRET=seu-client-secret-aqui
KEYCLOAK_VALIDATE_TOKEN=true
```

### Configuração no Keycloak

1. Criar um client `commerce-service` no realm `sitio-multitrem`
2. Configurar o client como "confidential"
3. Habilitar "Service Accounts Enabled"
4. Configurar o client secret
5. Adicionar roles necessárias ao client (se aplicável)

## Uso dos Endpoints

### Exemplo: Criar Conversa

```bash
curl -X POST "http://localhost:8002/api/v1/chatbot/conversations?channel=whatsapp&external_user_id=+5511999999999" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"
```

### Exemplo: Criar Mensagem

```bash
curl -X POST "http://localhost:8002/api/v1/chatbot/messages" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "uuid-da-conversa",
    "direction": "in",
    "text": "Olá, quero fazer um pedido",
    "intent": "new_order"
  }'
```

### Exemplo: Criar Pedido via Chatbot

```bash
curl -X POST "http://localhost:8002/api/v1/chatbot/orders" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "uuid-da-conversa",
    "customer_id": 1,
    "items": [
      {"product_id": 1, "qty": 5},
      {"product_id": 2, "qty": 3}
    ],
    "delivery_address_id": 1
  }'
```

## Integração com Chatbot Operations

O arquivo `CHATBOT_PROMPT.md` contém todas as informações necessárias para o chatbot operations:

1. **Contexto do negócio** - Regras de precificação, perfis de cliente
2. **Endpoints disponíveis** - Lista completa com descrições
3. **Fluxos de conversação** - Passo a passo para cada cenário
4. **Exemplos práticos** - Respostas e chamadas de API
5. **Tratamento de erros** - Como lidar com diferentes situações

## Segurança

- ✅ Todos os endpoints de chatbot requerem autenticação
- ✅ Validação via introspection endpoint (mais seguro que validação local)
- ✅ Tokens expirados ou inválidos são rejeitados
- ✅ Dados do usuário disponíveis para auditoria

## Próximos Passos

1. Configurar o client no Keycloak
2. Testar autenticação com tokens reais
3. Integrar o prompt com o chatbot operations
4. Adicionar logs de auditoria para ações do chatbot
5. Implementar rate limiting específico para endpoints de chatbot (opcional)
