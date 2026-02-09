# 🗄️ Guia de Integração com Base de Dados - Sistema de Tracking de IA

## 📋 Visão Geral
Este documento descreve a estrutura completa da base de dados criada para armazenar todas as comunicações e métricas do sistema de IA. O sistema foi projetado para capturar, armazenar e analisar todas as interações com modelos de IA de forma automática e eficiente.

## 🔧 Configuração da Base de Dados

### Conexão
- **SGBD:** PostgreSQL 11.7
- **Host:** localhost
- **Porta:** 5434
- **Database:** `sitio_multitrem`
- **Schema:** `chatbot`
- **URI:** `postgresql://postgres:123456@localhost:5434/sitio_multitrem`

### Ambiente
- **Servidor API:** http://localhost:8012
- **Framework:** FastAPI com SQLAlchemy
- **Middleware:** Sistema automático de tracking ativo

## 📊 Estrutura das Tabelas

### 1. **Tabela `chatbot.users`**
Armazena informações dos usuários do sistema.

```sql
CREATE TABLE chatbot.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    total_tokens_used INTEGER DEFAULT 0 NOT NULL,
    total_cost_spent FLOAT DEFAULT 0.0 NOT NULL,
    total_requests INTEGER DEFAULT 0 NOT NULL,
    total_conversations INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Campos importantes para tracking:**
- `total_tokens_used`: Total de tokens consumidos pelo usuário
- `total_cost_spent`: Custo total acumulado
- `total_requests`: Número total de requisições
- `total_conversations`: Número total de conversas

### 2. **Tabela `chatbot.conversations`**
Armazena metadados das conversas.

```sql
CREATE TABLE chatbot.conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES chatbot.users(id),
    title VARCHAR(200),
    total_tokens INTEGER DEFAULT 0,
    total_cost FLOAT DEFAULT 0.0,
    model_used VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Campos importantes:**
- `total_tokens`: Tokens acumulados na conversa
- `total_cost`: Custo acumulado da conversa
- `model_used`: Modelo de IA utilizado
- `status`: Estado da conversa (active, completed, archived)

### 3. **Tabela `chatbot.transactions`** ⭐ **PRINCIPAL**
Esta é a tabela mais importante - armazena CADA interação com modelos de IA.

```sql
CREATE TABLE chatbot.transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES chatbot.users(id),
    conversation_id INTEGER REFERENCES chatbot.conversations(id),
    model_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    request_tokens INTEGER DEFAULT 0,
    response_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost FLOAT DEFAULT 0.0,
    request_data TEXT,
    response_data TEXT,
    processing_time FLOAT,
    status VARCHAR(20) DEFAULT 'completed',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Campos críticos para salvar:**
- `model_name`: Nome do modelo (ex: "gpt-4", "gpt-3.5-turbo", "claude-3")
- `provider`: Provedor (ex: "openai", "anthropic", "deepseek")
- `request_tokens`: Tokens da pergunta/prompt
- `response_tokens`: Tokens da resposta
- `total_tokens`: Total de tokens (request + response)
- `cost`: Custo calculado da transação
- `request_data`: Dados completos da requisição (JSON)
- `response_data`: Dados completos da resposta (JSON)
- `processing_time`: Tempo de processamento em segundos
- `status`: Status da transação (completed, failed, pending)
- `error_message`: Mensagem de erro se houver falha

### 4. **Tabela `chatbot.usage`**
Armazena métricas agregadas por período.

```sql
CREATE TABLE chatbot.usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES chatbot.users(id),
    model_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    total_requests INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost FLOAT DEFAULT 0.0,
    avg_processing_time FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 Como Integrar e Salvar Dados

### Método 1: Via API REST (Recomendado)
O sistema possui endpoints para salvar dados automaticamente:

```python
import requests

# Salvar transação via API
transaction_data = {
    "user_id": 1,
    "conversation_id": 1,
    "model_name": "gpt-4",
    "provider": "openai",
    "request_tokens": 150,
    "response_tokens": 75,
    "total_tokens": 225,
    "cost": 0.0045,
    "request_data": json.dumps({"prompt": "Sua pergunta aqui"}),
    "response_data": json.dumps({"response": "Resposta da IA"}),
    "processing_time": 2.5,
    "status": "completed"
}

response = requests.post(
    "http://localhost:8012/analytics/transaction",
    json=transaction_data
)
```

### Método 2: Inserção Direta no Banco
```python
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:123456@localhost:5434/sitio_multitrem")

with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO chatbot.transactions 
        (user_id, model_name, provider, request_tokens, response_tokens, 
         total_tokens, cost, request_data, response_data, processing_time, status)
        VALUES (:user_id, :model_name, :provider, :request_tokens, :response_tokens,
                :total_tokens, :cost, :request_data, :response_data, :processing_time, :status)
    """), {
        "user_id": 1,
        "model_name": "gpt-4",
        "provider": "openai",
        "request_tokens": 150,
        "response_tokens": 75,
        "total_tokens": 225,
        "cost": 0.0045,
        "request_data": '{"prompt": "Sua pergunta"}',
        "response_data": '{"response": "Resposta da IA"}',
        "processing_time": 2.5,
        "status": "completed"
    })
    conn.commit()
```

## 📈 Endpoints Disponíveis

### Principais Endpoints para Integração:
- `POST /analytics/transaction` - Salvar nova transação
- `GET /analytics/usage-stats` - Consultar estatísticas
- `GET /analytics/cost-analysis` - Análise de custos
- `GET /ai/models` - Listar modelos disponíveis
- `GET /health` - Verificar status do sistema

## 🎯 Dados Essenciais a Serem Salvos

### Para CADA interação com IA, salve:
1. **Identificação:**
   - ID do usuário
   - ID da conversa (se aplicável)
   - Timestamp da interação

2. **Modelo e Provedor:**
   - Nome exato do modelo (ex: "gpt-4-turbo", "claude-3-sonnet")
   - Provedor (openai, anthropic, deepseek, etc.)

3. **Métricas de Tokens:**
   - Tokens do prompt/pergunta
   - Tokens da resposta
   - Total de tokens

4. **Custos:**
   - Custo calculado da transação
   - Moeda (USD por padrão)

5. **Dados Completos:**
   - Prompt/pergunta completa (JSON)
   - Resposta completa (JSON)
   - Parâmetros utilizados (temperature, max_tokens, etc.)

6. **Performance:**
   - Tempo de processamento
   - Status da requisição
   - Mensagens de erro (se houver)

## 🔍 Exemplos de Uso

### Exemplo 1: Salvar Interação com GPT-4
```json
{
    "user_id": 1,
    "conversation_id": 123,
    "model_name": "gpt-4-turbo",
    "provider": "openai",
    "request_tokens": 200,
    "response_tokens": 150,
    "total_tokens": 350,
    "cost": 0.007,
    "request_data": "{\"messages\": [{\"role\": \"user\", \"content\": \"Explique machine learning\"}], \"temperature\": 0.7}",
    "response_data": "{\"choices\": [{\"message\": {\"content\": \"Machine learning é...\"}}]}",
    "processing_time": 3.2,
    "status": "completed"
}
```

### Exemplo 2: Salvar Interação com Claude
```json
{
    "user_id": 1,
    "conversation_id": 124,
    "model_name": "claude-3-sonnet",
    "provider": "anthropic",
    "request_tokens": 180,
    "response_tokens": 220,
    "total_tokens": 400,
    "cost": 0.012,
    "request_data": "{\"prompt\": \"Analise este código Python\", \"max_tokens\": 500}",
    "response_data": "{\"completion\": \"Este código Python...\"}",
    "processing_time": 2.8,
    "status": "completed"
}
```

## ⚠️ Pontos Importantes

1. **Sempre salve dados completos** - Mesmo que pareça redundante, salve tanto os tokens individuais quanto o total
2. **Use JSON para dados complexos** - request_data e response_data devem ser strings JSON válidas
3. **Calcule custos precisamente** - Use as tabelas de preços atualizadas de cada provedor
4. **Trate erros adequadamente** - Salve transações mesmo quando há falhas, marcando o status como "failed"
5. **Mantenha timestamps precisos** - Use UTC para consistência
6. **Valide dados antes de salvar** - Verifique se user_id existe, se tokens são números válidos, etc.

## 🚀 Status do Sistema

✅ **Sistema Operacional:**
- Base de dados criada e funcionando
- Tabelas estruturadas e indexadas
- Middleware de tracking ativo
- APIs funcionais
- Testes de conectividade aprovados

O sistema está **PRONTO** para receber e armazenar dados de comunicação com IAs. Todas as estruturas estão criadas e testadas.

---

**Para dúvidas ou suporte técnico, consulte os logs em `/logs/` ou teste a conectividade com `python test_simple_connection.py`**