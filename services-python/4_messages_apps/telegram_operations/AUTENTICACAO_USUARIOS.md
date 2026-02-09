# 🔐 Autenticação de Usuários do Telegram

## 📋 Visão Geral

O Telegram Service agora verifica se o usuário que fala pelo Telegram já existe na base de dados do e-commerce e obtém as credenciais necessárias (token JWT) para suas solicitações. Isso permite:

- ✅ Verificar se o usuário está cadastrado no e-commerce
- ✅ Obter credenciais (token JWT) para requisições autenticadas
- ✅ Verificar permissões para tarefas específicas
- ✅ Passar informações de autenticação para o Chatbot Service

## 🏗️ Arquitetura

```
Telegram → Telegram Service → Verifica Usuário (User Service/Gateway) → Obtém Credenciais
    ↓
Chatbot Service (com token JWT se autenticado)
```

## 🔄 Fluxo de Autenticação

### 1. **Recebimento de Mensagem**
Quando uma mensagem chega do Telegram:
- O Telegram Service extrai o `telegram_user_id` e `username`
- Chama `telegram_auth_service.get_user_credentials()` para verificar o usuário

### 2. **Verificação do Usuário**
O serviço de autenticação:
- Busca o usuário no e-commerce via Gateway/User Service
- Endpoint: `GET /api/v1/users/telegram/{telegram_user_id}`
- Se encontrado, retorna dados do usuário (id, email, keycloak_id, permissions)

### 3. **Obtenção de Credenciais**
Se o usuário for encontrado:
- Credenciais são cacheadas por 1 hora
- Informações incluem: `user_id`, `email`, `keycloak_id`, `permissions`, `profiles`
- Token JWT pode ser obtido se necessário (requer implementação adicional)

### 4. **Envio para Chatbot Service**
As credenciais são enviadas junto com a mensagem:
- Header `Authorization: Bearer {token}` (se token disponível)
- Payload com informações do usuário autenticado
- Metadata com `is_authenticated: true/false`

## 📝 Implementação

### Serviço de Autenticação (`services/auth_service.py`)

```python
# Verificar se usuário existe
credentials = await telegram_auth_service.get_user_credentials(
    telegram_user_id=user_id,
    username=username
)

# Verificar permissão específica
has_permission = await telegram_auth_service.check_user_permission(
    telegram_user_id=user_id,
    permission="chatbot:use"
)
```

### Integração no Telegram Service

O `telegram_service.py` foi modificado para:
- Chamar o serviço de autenticação antes de processar mensagens
- Incluir credenciais nas requisições ao Chatbot Service
- Adicionar metadata de autenticação

### Cliente do Chatbot (`services/chatbot_client.py`)

O cliente foi atualizado para:
- Aceitar parâmetro `credentials` opcional
- Enviar token JWT no header `Authorization` se disponível
- Incluir informações do usuário autenticado no payload

## ⚙️ Configuração

Adicione ao `.env`:

```env
# User Service / Gateway (para autenticação)
GATEWAY_SERVICE_URL=http://localhost:8000
USER_SERVICE_URL=http://localhost:8001
```

## 🔗 Endpoint Necessário no User Service

O User Service precisa ter um endpoint para buscar usuário por `telegram_id`:

```python
@router.get("/users/telegram/{telegram_user_id}")
async def get_user_by_telegram_id(
    telegram_user_id: str,
    db: Session = Depends(get_db_session)
):
    """Busca usuário pelo ID do Telegram"""
    # Implementar busca no banco de dados
    # Retornar dados do usuário se encontrado
```

**Nota:** Este endpoint ainda precisa ser implementado no User Service. Por enquanto, o Telegram Service tenta buscar via Gateway e faz fallback para User Service direto.

## 🔒 Comportamento

### Usuário Autenticado
- ✅ Credenciais são obtidas e cacheadas
- ✅ Token JWT é enviado nas requisições (se disponível)
- ✅ Permissões são verificadas
- ✅ Informações do usuário são passadas ao Chatbot Service

### Usuário Não Autenticado
- ⚠️ Acesso limitado (sem credenciais)
- ⚠️ `is_authenticated: false` no metadata
- ⚠️ Chatbot Service pode restringir funcionalidades baseado nisso

## 🎯 Próximos Passos

1. **Implementar endpoint no User Service** para buscar usuário por `telegram_id`
2. **Criar mecanismo de vinculação** de conta Telegram com usuário do e-commerce
3. **Implementar obtenção de token JWT** para usuários autenticados
4. **Adicionar verificação de permissões** no Chatbot Service para tarefas específicas
5. **Criar comando no Telegram** para vincular conta (ex: `/vincular email@exemplo.com`)

## 📊 Cache de Credenciais

As credenciais são cacheadas por **1 hora** para evitar chamadas desnecessárias ao User Service. O cache pode ser limpo:

```python
# Limpar cache de um usuário específico
telegram_auth_service.clear_cache(telegram_user_id="123456")

# Limpar todo o cache
telegram_auth_service.clear_cache()
```

## 🔍 Logs

O serviço registra:
- Busca de usuário por telegram_id
- Sucesso/falha na autenticação
- Verificação de permissões
- Uso de cache

Exemplo de log:
```
INFO: Buscando usuário por telegram_id telegram_user_id=123456
INFO: Usuário encontrado no e-commerce user_id=42
INFO: Credenciais obtidas com sucesso telegram_user_id=123456
```
