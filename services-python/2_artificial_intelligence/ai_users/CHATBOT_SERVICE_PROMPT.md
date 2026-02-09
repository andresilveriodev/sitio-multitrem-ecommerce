# 🤖 PROMPT PARA O CHATBOT_SERVICE

## **Objetivo Principal**
Você é o **Chatbot Service Integrador** - um middleware inteligente que atua como o cérebro central entre o frontend e o serviço de IA. Sua função é otimizar a experiência do usuário, reduzir custos de IA e garantir contextos adequados.

---

## **🏗️ ARQUITETURA DOS SERVIÇOS**

### **Chatbot Service** (Você - Novo Serviço)
- **Porta**: 8008 (sugerido)
- **Função**: Cérebro operacional e gestão de contexto
- **Responsável por**: Decisões inteligentes, filtros, otimização de custos

### **AI Service** (Serviço Atual - Porta 8012)
- **Porta**: 8012 (já rodando)
- **Função**: Comunicação direta com providers de IA
- **Responsável por**: Chamadas para OpenAI, DeepSeek, Ollama, etc.

---

## **📋 RESPONSABILIDADES DO CHATBOT_SERVICE**

### **1. Gestão de Contexto Inteligente**
- **Manter histórico contextual** de cada conversa por usuário
- **Identificar mudanças de tópico** e criar novos contextos quando necessário
- **Enriquecer prompts** com informações relevantes do histórico
- **Detectar intenções** do usuário (pergunta, comando, confirmação, etc.)
- **Gerenciar sessões** e persistir estado entre interações

### **2. Filtros e Validações Pré-IA**
- **Responder automaticamente** a perguntas frequentes e óbvias:
  - "Como você está?"
  - "Qual é o seu nome?"
  - "Que horas são?"
  - "Obrigado", "Tchau", "Adeus"
  - "Você pode me ajudar?"
  - Perguntas sobre o sistema ou funcionalidades básicas
- **Validar inputs** antes de enviar para IA:
  - Verificar se a mensagem não está vazia
  - Detectar spam ou conteúdo inadequado
  - Validar formato de dados quando necessário
  - Verificar limites de caracteres

### **3. Otimização de Custos**
- **Classificar urgência** das mensagens (baixa, média, alta)
- **Implementar cache inteligente** para respostas similares
- **Agrupar mensagens** quando apropriado para reduzir chamadas à IA
- **Usar modelos mais baratos** para tarefas simples
- **Implementar rate limiting** inteligente
- **Monitorar custos** por usuário e conversa

### **4. Integração com AI Service**
- **Selecionar o provider de IA** mais adequado para cada tipo de pergunta
- **Formatar prompts** de acordo com o contexto e histórico
- **Processar respostas** da IA antes de enviar ao frontend
- **Implementar fallbacks** quando um provider falha
- **Gerenciar timeouts** e retry logic
- **Consultar configurações** do usuário (user_ai_settings)
- **Verificar limites** de assinatura antes de chamar IA
- **Enviar metadados** para rastreamento (conversation_id, user_id)

### **5. Gestão de Estado e Sessões**
- **Manter sessões ativas** por usuário
- **Sincronizar estado** entre frontend e backend
- **Gerenciar timeouts** e reconexões
- **Armazenar preferências** do usuário
- **Persistir contexto** entre reinicializações

---

## **🔧 O QUE O AI SERVICE JÁ FAZ (Porta 8012)**

### **Endpoints Disponíveis:**
- `POST /ai/generate` - Gerar resposta da IA
- `POST /ai/generate/stream` - Gerar resposta em streaming
- `GET /ai/models` - Listar modelos disponíveis
- `POST /ai/validate` - Validar conexão com OpenAI
- `POST /chatbot/chat` - Enviar mensagem e receber resposta da IA

### **Providers Suportados:**
- **OpenAI** (GPT-4, GPT-3.5, GPT-4o-mini)
- **DeepSeek** (DeepSeek Chat)
- **Ollama** (Modelos locais)

### **Tabelas e Dados que o AI Service Gerencia:**

#### **1. Transações de IA (`transactions`)**
- **Responsabilidade**: Registrar TODAS as chamadas para providers de IA
- **Dados**: Request/response, tokens, custos, performance, status
- **Por que**: Rastreamento completo de uso e cobrança

#### **2. Conversas (`conversations`)**
- **Responsabilidade**: Agregar métricas de conversas
- **Dados**: Total de tokens, custos, mensagens por conversa
- **Por que**: Relatórios e análise de conversas

#### **3. Uso Agregado (`usage`)**
- **Responsabilidade**: Métricas diárias/semanais/mensais
- **Dados**: Estatísticas por período, modelo, usuário
- **Por que**: Dashboards e relatórios de uso

#### **4. Modelos de IA (`ai_models`)**
- **Responsabilidade**: Configurações dos modelos disponíveis
- **Dados**: Preços, limites, configurações
- **Por que**: Seleção automática de modelos

#### **5. Assinaturas (`ai_subscriptions`, `user_subscriptions`)**
- **Responsabilidade**: Planos e limites de usuários
- **Dados**: Limites de uso, cobrança, status
- **Por que**: Controle de acesso e cobrança

#### **6. Configurações de Usuário (`user_ai_settings`)**
- **Responsabilidade**: Preferências de IA por usuário
- **Dados**: Provider preferido, configurações
- **Por que**: Personalização de respostas

#### **7. Alertas (`ai_usage_alerts`)**
- **Responsabilidade**: Notificações de uso excessivo
- **Dados**: Limites, alertas, notificações
- **Por que**: Controle de custos

### **Funcionalidades:**
- Comunicação direta com APIs de IA
- Gerenciamento de tokens e limites
- Streaming de respostas
- Validação de conectividade
- Logs de uso e métricas
- **Controle de cobrança e assinaturas**
- **Relatórios de uso e performance**

---

## **🔄 FLUXO DE TRABALHO**

```
Frontend → Chatbot Service → [Filtros/Validações] → AI Service → [Processamento] → Frontend
```

### **Decisões que VOCÊ deve tomar:**

1. **Responder diretamente** (sem IA):
   - Saudações básicas
   - Perguntas sobre o sistema
   - Confirmações simples
   - Comandos de sistema

2. **Enriquecer contexto** antes de enviar para IA:
   - Adicionar histórico relevante
   - Incluir preferências do usuário
   - Contextualizar com dados do sistema
   - Adicionar metadados úteis

3. **Selecionar provider de IA**:
   - OpenAI para questões complexas
   - DeepSeek para análises técnicas
   - Ollama para tarefas locais simples

4. **Processar resposta da IA**:
   - Formatar para o frontend
   - Adicionar metadados úteis
   - Atualizar contexto
   - Implementar cache se apropriado

---

## **📊 ESTRUTURA DE DADOS SUGERIDA**

### **Dados que VOCÊ deve gerenciar (Chatbot Service):**

```python
class ConversationContext:
    user_id: str
    session_id: str
    current_topic: str
    message_history: List[Message]
    context_summary: str  # Resumo do contexto atual
    conversation_metadata: Dict
    cache_hits: int
    last_interaction: datetime

class Message:
    id: str
    user_id: str
    content: str
    timestamp: datetime
    message_type: str  # 'user', 'bot', 'system'
    requires_ai: bool
    ai_provider_used: Optional[str]
    context_added: Dict
    response_time: float
    conversation_id: Optional[int]  # ID da conversa no AI Service

class UserPreferences:
    user_id: str
    language: str
    response_style: str  # 'concise', 'detailed', 'technical'
    auto_cache: bool
    max_context_length: int
    conversation_preferences: Dict
```

### **Dados que o AI SERVICE já gerencia (NÃO duplicar):**

```python
# TABELAS EXISTENTES NO AI SERVICE - NÃO CRIAR NOVO:
# - conversations (métricas agregadas)
# - messages (mensagens da conversa)
# - transactions (todas as chamadas de IA)
# - usage (métricas de uso)
# - ai_models (configurações de modelos)
# - ai_subscriptions (planos disponíveis)
# - user_subscriptions (assinaturas dos usuários)
# - user_ai_settings (preferências de IA)
# - ai_usage_alerts (alertas de uso)
```

---

## **🌐 ENDPOINTS PRINCIPAIS**

```python
# Gestão de Mensagens
POST /chatbot/process-message
GET /chatbot/conversation/{user_id}
POST /chatbot/update-context

# Gestão de Usuários
GET /chatbot/user-preferences/{user_id}
POST /chatbot/set-preferences
POST /chatbot/create-session
DELETE /chatbot/end-session/{session_id}

# Analytics e Métricas
GET /chatbot/analytics/{user_id}
GET /chatbot/cost-tracking/{user_id}
GET /chatbot/cache-stats

# Health Check
GET /chatbot/health
GET /chatbot/status
```

---

## **✅ O QUE VOCÊ DEVE FAZER**

### **Inteligência de Contexto:**
- ✅ Manter histórico rico de conversas
- ✅ Detectar mudanças de tópico
- ✅ Enriquecer prompts com contexto relevante
- ✅ Gerenciar sessões e estado

### **Otimização de Custos:**
- ✅ Responder automaticamente a perguntas simples
- ✅ Implementar cache inteligente
- ✅ Selecionar provider mais adequado
- ✅ Monitorar e controlar custos

### **Experiência do Usuário:**
- ✅ Garantir respostas rápidas
- ✅ Manter contexto entre interações
- ✅ Implementar fallbacks inteligentes
- ✅ Personalizar respostas por usuário

### **Integração:**
- ✅ Comunicar com AI Service (porta 8012)
- ✅ Processar respostas da IA
- ✅ Gerenciar erros e timeouts
- ✅ Sincronizar com frontend
- ✅ **Consultar configurações** do usuário no AI Service
- ✅ **Verificar limites** de assinatura antes de chamar IA
- ✅ **Enviar metadados** para rastreamento correto
- ✅ **Usar apenas INSERT/UPDATE** para dados operacionais
- ✅ **Manter auditoria** de todas as operações

---

## **❌ O QUE VOCÊ NÃO DEVE FAZER**

- ❌ Gerar respostas de IA (responsabilidade do AI Service)
- ❌ Gerenciar banco de dados diretamente
- ❌ Implementar autenticação complexa
- ❌ Processar pagamentos ou assinaturas
- ❌ Gerenciar arquivos ou uploads
- ❌ Implementar WebSocket diretamente
- ❌ **Duplicar tabelas** que já existem no AI Service
- ❌ **Gerenciar métricas** de tokens e custos (AI Service faz isso)
- ❌ **Criar conversas** diretamente (consultar AI Service)
- ❌ **Armazenar configurações** de IA (user_ai_settings já existe)
- ❌ **EXCLUIR dados** diretamente no banco de dados
- ❌ **Usar comandos DELETE** em qualquer tabela
- ❌ **Modificar dados históricos** de transações

---

## **📈 MÉTRICAS IMPORTANTES**

### **Performance:**
- Taxa de respostas diretas (sem IA)
- Tempo médio de resposta
- Taxa de cache hit
- Uptime e disponibilidade

### **Custos:**
- Custo por conversa (consultar AI Service)
- Custo por usuário (consultar AI Service)
- Economia com cache
- Distribuição por provider (consultar AI Service)

### **Qualidade:**
- Satisfação do usuário
- Taxa de sucesso das chamadas à IA
- Taxa de fallback
- Contexto mantido vs perdido

### **Técnicas:**
- Latência de resposta
- Taxa de erro
- Uso de memória
- Número de sessões ativas

---

## **🚀 IMPLEMENTAÇÃO SUGERIDA**

### **Tecnologias Recomendadas:**
- **FastAPI** (como o AI Service)
- **Redis** (para cache e sessões)
- **PostgreSQL** (para persistência de contexto - APENAS dados de contexto)
- **Pydantic** (para validação de dados)
- **Logging estruturado**
- **HTTP Client** (para comunicação com AI Service)

### **Estrutura de Pastas:**
```
chatbot_service/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py          # APENAS para contexto
│   ├── cache.py
│   ├── context_manager.py
│   ├── filters/
│   │   ├── __init__.py
│   │   ├── message_filters.py
│   │   └── cost_optimizer.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat_router.py
│   │   └── analytics_router.py
│   └── services/
│       ├── __init__.py
│       ├── ai_integration.py    # Comunicação com AI Service
│       ├── context_service.py
│       └── cache_service.py
├── models/
│   ├── __init__.py
│   ├── conversation_context.py  # APENAS contexto
│   ├── user_preferences.py      # APENAS preferências de contexto
│   └── message.py              # APENAS metadados de contexto
├── main.py
└── requirements.txt
```

---

## **🎯 OBJETIVOS DE SUCESSO**

1. **Reduzir custos de IA em 40-60%** através de filtros inteligentes
2. **Melhorar tempo de resposta** para perguntas simples em 80%
3. **Manter contexto** em 95% das conversas
4. **Alta disponibilidade** (99.9% uptime)
5. **Experiência fluida** para o usuário final

---

---

## **🎯 SEPARAÇÃO CLARA DE RESPONSABILIDADES**

### **AI SERVICE (Porta 8012) - O que JÁ FAZ:**
- ✅ **Gerencia TODAS as tabelas** de IA (conversations, messages, transactions, usage, etc.)
- ✅ **Faz chamadas** para providers de IA (OpenAI, DeepSeek, Ollama)
- ✅ **Calcula custos** e tokens de cada transação
- ✅ **Controla assinaturas** e limites de usuários
- ✅ **Gera relatórios** de uso e performance
- ✅ **Armazena configurações** de IA dos usuários

### **CHATBOT SERVICE (Porta 8013) - O que VOCÊ deve fazer:**
- ✅ **Gerencia APENAS contexto** de conversas (não duplica dados)
- ✅ **Filtra mensagens** antes de enviar para AI Service
- ✅ **Implementa cache** para respostas similares
- ✅ **Consulta AI Service** para dados de usuário e configurações
- ✅ **Envia metadados** corretos para rastreamento
- ✅ **Otimiza custos** evitando chamadas desnecessárias

### **FLUXO CORRETO:**
```
Frontend → Chatbot Service → [Filtros/Cache] → AI Service → [IA + Dados] → Frontend
```

**IMPORTANTE**: O Chatbot Service NÃO duplica dados, apenas consulta o AI Service quando necessário!

---

## **🚨 REGRAS CRÍTICAS DE SEGURANÇA**

### **❌ PROIBIÇÕES ABSOLUTAS:**
- **NENHUM comando DELETE** em qualquer tabela
- **NENHUMA exclusão direta** de dados no banco
- **NENHUMA modificação** de dados históricos de transações
- **NENHUM truncate** ou drop de tabelas

### **✅ OPERAÇÕES PERMITIDAS:**
- **INSERT** - Criar novos registros
- **UPDATE** - Atualizar dados existentes (com auditoria)
- **SELECT** - Consultar dados
- **Soft deletes** apenas com flag de status

---

**Este serviço será o CÉREBRO OPERACIONAL que garante que cada interação seja eficiente, contextualizada e custo-efetiva! 🧠✨**

**SEGURANÇA**: **NENHUM** dos serviços pode excluir dados diretamente no banco de dados! 🔒
