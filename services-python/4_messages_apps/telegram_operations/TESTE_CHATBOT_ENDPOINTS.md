# Teste de Endpoints do Chatbot Service

Este documento descreve os resultados dos testes dos endpoints disponíveis no Chatbot Service.

## Script de Teste

O script `test_chatbot_endpoints.py` testa todos os endpoints disponíveis no Chatbot Service.

### Como Executar

#### 1. Teste Básico (sem autenticação)

```bash
python test_chatbot_endpoints.py
```

Este comando testa apenas os endpoints públicos (health check e root).

#### 2. Teste Completo (com autenticação)

Para testar todos os endpoints, você precisa de um token JWT válido:

**Opção A: Usando variável de ambiente**
```bash
# Windows PowerShell
$env:JWT_TOKEN="seu_token_jwt_aqui"
python test_chatbot_endpoints.py

# Linux/Mac
export JWT_TOKEN="seu_token_jwt_aqui"
python test_chatbot_endpoints.py
```

**Opção B: Obtendo token do Keycloak**
```bash
# Windows PowerShell
$env:KEYCLOAK_USERNAME="seu_usuario"
$env:KEYCLOAK_PASSWORD="sua_senha"
python test_chatbot_endpoints.py

# Linux/Mac
export KEYCLOAK_USERNAME="seu_usuario"
export KEYCLOAK_PASSWORD="sua_senha"
python test_chatbot_endpoints.py
```

## Endpoints Testados

### ✅ Endpoints Públicos (Sem Autenticação)

1. **GET /health**
   - Status esperado: 200
   - Descrição: Health check do serviço
   - ✅ Funcionando

2. **GET /**
   - Status esperado: 200
   - Descrição: Endpoint raiz com informações do serviço
   - ✅ Funcionando

### 🔒 Endpoints de Chat (Requerem Autenticação JWT)

Todos os endpoints abaixo requerem token JWT válido com role `colaborador`:

1. **POST /chatbot/process-message**
   - Descrição: Processa mensagem do usuário
   - Body: `{ "user_id": "...", "message": "...", "session_id": "...", "content_type": "text/plain" }`
   - ⚠️ Requer autenticação

2. **POST /chatbot/process-message/stream**
   - Descrição: Processa mensagem em streaming (SSE)
   - ⚠️ Requer autenticação
   - ⚠️ Teste manual recomendado (streaming)

3. **POST /chatbot/validate-input**
   - Descrição: Valida entrada sem processar
   - Body: `{ "user_id": "...", "message": "...", "content_type": "text/plain" }`
   - ⚠️ Requer autenticação

4. **GET /chatbot/conversation/{user_id}**
   - Descrição: Busca contexto da conversa do usuário
   - ⚠️ Requer autenticação

5. **POST /chatbot/update-context**
   - Descrição: Atualiza contexto da conversa
   - Body: `{ "user_id": "...", "summary": "..." }`
   - ⚠️ Requer autenticação

6. **POST /chatbot/chat**
   - Descrição: Endpoint simplificado para chat
   - Body: `{ "conversation_id": 1, "message": "...", "user_id": "...", "provider": "...", "model": "..." }`
   - ⚠️ Requer autenticação

### 📊 Endpoints de Analytics (Requerem Autenticação JWT)

1. **GET /chatbot/analytics/{user_id}**
   - Descrição: Busca analytics do usuário
   - ⚠️ Requer autenticação

2. **GET /chatbot/cost-tracking/{user_id}**
   - Descrição: Busca informações de custos do usuário
   - ⚠️ Requer autenticação

3. **GET /chatbot/cache-stats**
   - Descrição: Busca estatísticas do cache
   - ⚠️ Requer autenticação

4. **POST /chatbot/clear-cache**
   - Descrição: Limpa todo o cache
   - ⚠️ Requer autenticação

5. **POST /chatbot/invalidate-user-cache/{user_id}**
   - Descrição: Invalida cache de um usuário específico
   - ⚠️ Requer autenticação

6. **GET /chatbot/system-health**
   - Descrição: Verifica saúde geral do sistema
   - ⚠️ Requer autenticação

7. **GET /chatbot/performance-metrics**
   - Descrição: Busca métricas de performance do sistema
   - ⚠️ Requer autenticação

### 🤖 Endpoints de AI (Requerem Autenticação JWT)

1. **POST /ai/chat**
   - Descrição: Endpoint simplificado para chat com IA
   - Body: `{ "message": "..." }`
   - ⚠️ Requer autenticação

2. **GET /ai/providers**
   - Descrição: Lista provedores disponíveis
   - ⚠️ Requer autenticação

## ❌ Endpoint Ausente

### POST /chatbot/process-message-authenticated

**Status:** ❌ **NÃO EXISTE**

Este endpoint é chamado pelo `telegram_operations` (em `services/chatbot_client.py`, linha 155), mas **não está implementado** no Chatbot Service.

**Impacto:**
- Quando o `telegram_service.py` chama `process_message_authenticated()`, ocorre erro 404
- O endpoint `/chatbot/process-message` já requer autenticação JWT com `require_colaborador_role`
- A rota `/chatbot/process-message-authenticated` pode ser redundante ou ter sido planejada para um comportamento diferente

**Solução:**
1. Implementar o endpoint `/chatbot/process-message-authenticated` no `chat_router.py`, OU
2. Atualizar o `chatbot_client.py` para usar `/chatbot/process-message` (que já requer autenticação)

## Resultados dos Testes

### Teste Básico (sem token)

```
✓ Passou: 2
✗ Falhou: 0
⚠ Pulado: 20
Total: 22
```

### Endpoints Públicos
- ✅ GET /health - Funcionando
- ✅ GET / - Funcionando

### Endpoints com Autenticação
- ⚠️ Todos os 18 endpoints restantes requerem token JWT válido
- ⚠️ Para testá-los, forneça um token via variável de ambiente `JWT_TOKEN`

## Observações

1. **Autenticação:** Todos os endpoints (exceto `/health` e `/`) requerem token JWT válido com role `colaborador`
2. **Porta:** O Chatbot Service roda na porta **8011** (não 8002 como mencionado em alguns documentos)
3. **Endpoint Ausente:** O endpoint `/chatbot/process-message-authenticated` não existe e precisa ser implementado ou o cliente precisa ser atualizado

## Próximos Passos

1. ✅ Testes básicos concluídos
2. ⚠️ Testes com autenticação pendentes (requer token JWT)
3. ❌ Implementar ou corrigir endpoint `/chatbot/process-message-authenticated`
