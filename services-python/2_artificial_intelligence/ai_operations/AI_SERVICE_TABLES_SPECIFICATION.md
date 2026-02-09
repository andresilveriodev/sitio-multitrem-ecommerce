# 📊 ESPECIFICAÇÃO DETALHADA DAS TABELAS DO AI SERVICE

## **🎯 RESUMO EXECUTIVO**

O **AI Service (Porta 8012)** é responsável por **TODAS** as tabelas relacionadas a IA, incluindo transações, conversas, métricas, configurações e cobrança. O Chatbot Service deve **CONSULTAR** estas tabelas, mas **NUNCA** duplicá-las.

---

## **📋 TABELAS E PARÂMETROS QUE O AI SERVICE SALVA**

### **1. 🗣️ CONVERSAS (`conversations`)**

**Responsabilidade**: Agregar métricas de conversas por usuário

**Parâmetros salvos**:
```sql
- id (PK)
- user_id (FK -> public.users.id)
- username (String 50) - Para facilitar consultas
- title (String 200) - Título da conversa
- status (String 20) - 'active', 'archived', 'deleted'
- total_tokens (Integer) - Total de tokens usados
- total_prompt_tokens (Integer) - Tokens de prompt
- total_completion_tokens (Integer) - Tokens de resposta
- total_cost (Float) - Custo total da conversa
- total_messages (Integer) - Número de mensagens
- conversation_metadata (JSON) - Metadados da conversa
- created_at (DateTime)
- updated_at (DateTime)
```

**Por que o AI Service salva**: Relatórios e análise de conversas, rastreamento de custos

---

### **2. 💬 MENSAGENS (`messages`)**

**Responsabilidade**: Armazenar todas as mensagens das conversas

**Parâmetros salvos**:
```sql
- id (PK)
- conversation_id (FK -> conversations.id)
- content (Text) - Conteúdo da mensagem
- role (String 20) - 'user', 'assistant', 'system'
- message_metadata (JSON) - Metadados da mensagem
- created_at (DateTime)
- updated_at (DateTime)
```

**Por que o AI Service salva**: Histórico completo de conversas, análise de conteúdo

---

### **3. 💳 TRANSAÇÕES (`transactions`)**

**Responsabilidade**: Registrar TODAS as chamadas para providers de IA

**Parâmetros salvos**:
```sql
- id (PK)
- transaction_id (String 100, Unique) - ID único da transação
- conversation_id (FK -> conversations.id)
- user_id (FK -> public.users.id)
- username (String 50) - Para facilitar consultas
- provider (String 50) - 'openai', 'deepseek', 'ollama'
- model (String 100) - 'gpt-4o-mini', 'llama3.1', etc.
- endpoint (String 100) - '/ai/generate', '/ai/generate/stream'
- request_data (JSON) - Dados completos da requisição
- response_data (JSON) - Dados completos da resposta
- prompt_tokens (Integer) - Tokens de prompt
- completion_tokens (Integer) - Tokens de resposta
- total_tokens (Integer) - Total de tokens
- prompt_cost (Float) - Custo dos tokens de prompt
- completion_cost (Float) - Custo dos tokens de resposta
- total_cost (Float) - Custo total
- response_time_ms (Integer) - Tempo de resposta em ms
- is_streaming (Boolean) - Se foi streaming
- chunks_count (Integer) - Número de chunks (streaming)
- status (String 20) - 'pending', 'success', 'error'
- error_message (Text) - Mensagem de erro se houver
- ip_address (String 45) - IP do cliente
- user_agent (String 500) - User agent
- session_id (String 100) - ID da sessão
- created_at (DateTime)
- completed_at (DateTime) - Quando foi completada
```

**Por que o AI Service salva**: Rastreamento completo de uso, cobrança, auditoria

---

### **4. 📊 USO AGREGADO (`usage`)**

**Responsabilidade**: Métricas diárias/semanais/mensais de uso

**Parâmetros salvos**:
```sql
- id (PK)
- user_id (Integer) - Temporariamente sem FK
- username (String 50) - Para facilitar consultas
- provider (String 50) - 'openai', 'deepseek', 'ollama'
- model (String 100) - 'gpt-4o-mini', etc.
- date (Date) - Data da agregação
- period_type (String 20) - 'daily', 'weekly', 'monthly'
- total_requests (Integer) - Total de requisições
- successful_requests (Integer) - Requisições bem-sucedidas
- failed_requests (Integer) - Requisições falhadas
- streaming_requests (Integer) - Requisições em streaming
- total_prompt_tokens (Integer) - Total de tokens de prompt
- total_completion_tokens (Integer) - Total de tokens de resposta
- total_tokens (Integer) - Total de tokens
- total_prompt_cost (Float) - Custo total de prompt
- total_completion_cost (Float) - Custo total de resposta
- total_cost (Float) - Custo total
- avg_response_time_ms (Float) - Tempo médio de resposta
- min_response_time_ms (Integer) - Tempo mínimo de resposta
- max_response_time_ms (Integer) - Tempo máximo de resposta
- total_chunks (Integer) - Total de chunks (streaming)
- created_at (DateTime)
- updated_at (DateTime)
```

**Por que o AI Service salva**: Dashboards, relatórios de uso, análise de performance

---

### **5. 🤖 MODELOS DE IA (`ai_models`)**

**Responsabilidade**: Configurações dos modelos disponíveis

**Parâmetros salvos**:
```sql
- id (PK)
- model_id (String 100, Unique) - 'ollama', 'gpt-4o-mini'
- name (String 200) - 'GPT-4o Mini'
- provider (String 100) - 'OpenAI', 'Ollama'
- is_paid (Boolean) - Se é pago
- cost_per_1k_tokens (Float) - Custo por 1k tokens
- max_tokens_per_request (Integer) - Máximo de tokens por requisição
- is_available (Boolean) - Se está disponível
- description (Text) - Descrição do modelo
- features (JSON) - Array de features disponíveis
- rate_limits (JSON) - Limites de rate
- created_at (DateTime)
- updated_at (DateTime)
```

**Por que o AI Service salva**: Seleção automática de modelos, cálculo de custos

---

### **6. 📋 ASSINATURAS DE IA (`ai_subscriptions`)**

**Responsabilidade**: Planos disponíveis para assinatura

**Parâmetros salvos**:
```sql
- id (PK)
- plan_id (String 100, Unique) - 'free', 'premium'
- name (String 200) - 'Plano Gratuito'
- price (Float) - Preço do plano
- currency (String 10) - 'BRL'
- billing_cycle (Enum) - 'monthly', 'yearly'
- is_active (Boolean) - Se o plano está ativo
- features (JSON) - Features incluídas
- limits (JSON) - Limites do plano
- created_at (DateTime)
- updated_at (DateTime)
```

**Por que o AI Service salva**: Controle de planos, cobrança

---

### **7. 👤 ASSINATURAS DE USUÁRIO (`user_subscriptions`)**

**Responsabilidade**: Assinaturas ativas dos usuários

**Parâmetros salvos**:
```sql
- id (PK)
- user_id (FK -> public.users.id)
- username (String 50) - Para facilitar consultas
- subscription_id (FK -> ai_subscriptions.id)
- status (Enum) - 'active', 'cancelled', 'expired', 'pending'
- current_period_start (DateTime) - Início do período atual
- current_period_end (DateTime) - Fim do período atual
- cancel_at_period_end (Boolean) - Cancelar no fim do período
- usage_limits (JSON) - Limites atuais
- current_usage (JSON) - Uso atual
- created_at (DateTime)
- updated_at (DateTime)
```

**Por que o AI Service salva**: Controle de acesso, verificação de limites

---

### **8. ⚙️ CONFIGURAÇÕES DE USUÁRIO (`user_ai_settings`)**

**Responsabilidade**: Preferências de IA por usuário

**Parâmetros salvos**:
```sql
- id (PK)
- user_id (FK -> public.users.id, Unique)
- username (String 50) - Para facilitar consultas
- default_model (String 100) - Modelo padrão
- preferred_models (JSON) - Array de modelos preferidos
- auto_fallback (Boolean) - Fallback automático
- notifications (JSON) - Configurações de notificações
- created_at (DateTime)
- updated_at (DateTime)
```

**Por que o AI Service salva**: Personalização de respostas, configurações por usuário

---

### **9. 🚨 ALERTAS DE USO (`ai_usage_alerts`)**

**Responsabilidade**: Notificações de uso excessivo

**Parâmetros salvos**:
```sql
- id (PK)
- user_id (FK -> public.users.id)
- username (String 50) - Para facilitar consultas
- alert_type (Enum) - 'usage', 'cost', 'rate_limit'
- threshold (Float) - Limite do alerta
- current_value (Float) - Valor atual
- message (Text) - Mensagem do alerta
- is_triggered (Boolean) - Se foi disparado
- is_read (Boolean) - Se foi lido
- created_at (DateTime)
- updated_at (DateTime)
```

**Por que o AI Service salva**: Controle de custos, notificações

---

## **🔄 COMO O CHATBOT SERVICE DEVE INTERAGIR**

### **✅ CONSULTAS PERMITIDAS:**

```python
# 1. Verificar configurações do usuário
GET /ai/user-settings/{user_id}

# 2. Verificar assinatura e limites
GET /ai/user-subscription/{user_id}

# 3. Verificar modelos disponíveis
GET /ai/models

# 4. Criar nova conversa
POST /ai/conversations

# 5. Enviar mensagem para IA
POST /ai/generate

# 6. Obter métricas de uso
GET /ai/usage/{user_id}
```

### **❌ O QUE NÃO FAZER:**

- ❌ **Duplicar** qualquer uma das tabelas acima
- ❌ **Criar** tabelas de conversas próprias
- ❌ **Gerenciar** métricas de tokens e custos
- ❌ **Armazenar** configurações de IA
- ❌ **Controlar** assinaturas e limites
- ❌ **EXCLUIR** dados diretamente no banco de dados
- ❌ **Usar comandos DELETE** em qualquer tabela
- ❌ **Implementar soft delete** sem autorização
- ❌ **Modificar** dados históricos de transações

### **✅ O QUE FAZER:**

- ✅ **Consultar** configurações do usuário no AI Service
- ✅ **Verificar** limites antes de chamar IA
- ✅ **Enviar** conversation_id e user_id para rastreamento
- ✅ **Gerenciar** apenas contexto e cache local
- ✅ **Implementar** filtros para reduzir chamadas à IA
- ✅ **Usar apenas INSERT/UPDATE** para dados operacionais
- ✅ **Manter histórico** de todas as transações
- ✅ **Implementar auditoria** de todas as operações

---

## **📊 RESUMO DAS RESPONSABILIDADES**

| Tabela | AI Service | Chatbot Service |
|--------|------------|-----------------|
| `conversations` | ✅ Cria/gerencia | ❌ Apenas consulta |
| `messages` | ✅ Armazena | ❌ Apenas consulta |
| `transactions` | ✅ Registra tudo | ❌ Apenas consulta |
| `usage` | ✅ Calcula métricas | ❌ Apenas consulta |
| `ai_models` | ✅ Configura | ❌ Apenas consulta |
| `ai_subscriptions` | ✅ Gerencia planos | ❌ Apenas consulta |
| `user_subscriptions` | ✅ Controla acesso | ❌ Apenas consulta |
| `user_ai_settings` | ✅ Armazena prefs | ❌ Apenas consulta |
| `ai_usage_alerts` | ✅ Monitora uso | ❌ Apenas consulta |

---

---

## **🚨 REGRAS CRÍTICAS DE SEGURANÇA**

### **❌ PROIBIÇÕES ABSOLUTAS:**

1. **NENHUM comando DELETE** pode ser usado em qualquer tabela
2. **NENHUMA exclusão direta** de dados no banco de dados
3. **NENHUM soft delete** sem autorização explícita
4. **NENHUMA modificação** de dados históricos de transações
5. **NENHUM truncate** ou drop de tabelas

### **✅ OPERAÇÕES PERMITIDAS:**

1. **INSERT** - Criar novos registros
2. **UPDATE** - Atualizar dados existentes (com auditoria)
3. **SELECT** - Consultar dados
4. **Soft deletes** apenas com flag de status (nunca excluir)

### **🔒 IMPLEMENTAÇÃO DE SEGURANÇA:**

```python
# ❌ NUNCA FAZER:
DELETE FROM transactions WHERE user_id = 123
DELETE FROM conversations WHERE id = 456

# ✅ SEMPRE FAZER:
UPDATE conversations SET status = 'archived' WHERE id = 456
UPDATE transactions SET status = 'cancelled' WHERE id = 789
```

---

**IMPORTANTE**: O Chatbot Service deve ser uma **camada inteligente** que otimiza a comunicação, mas **NUNCA** duplica dados que o AI Service já gerencia! 🚀

**SEGURANÇA**: **NENHUM** dos serviços pode excluir dados diretamente no banco de dados! 🔒
