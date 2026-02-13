# 🤖 B3-Trader Chatbot Service

```powershell
# Ativar virtual env
.\.venv\Scripts\Activate.ps1
```

## **Visão Geral**

O **Chatbot Service** é um middleware inteligente que atua como o cérebro central entre o frontend e o AI Service. Sua função principal é otimizar a experiência do usuário, reduzir custos de IA e garantir contextos adequados para cada interação.

## **🏗️ Arquitetura**

```
Frontend → Chatbot Service (Porta 8008) → AI Service (Porta 8012) → Providers de IA
```

### **Responsabilidades do Chatbot Service:**

- ✅ **Gestão de Contexto Inteligente** - Mantém histórico e contexto de conversas
- ✅ **Filtros e Validações** - Responde automaticamente a perguntas simples
- ✅ **Otimização de Custos** - Cache inteligente e redução de chamadas à IA
- ✅ **Integração com AI Service** - Comunicação eficiente com providers de IA
- ✅ **Gestão de Sessões** - Controle de estado e persistência
- ✅ **🔒 Gateway de Segurança** - Validação completa de entrada e conformidade

### **O que o AI Service já faz:**

- ✅ Gerencia TODAS as tabelas de IA (conversations, messages, transactions, etc.)
- ✅ Faz chamadas para providers de IA (OpenAI, DeepSeek, Ollama)
- ✅ Calcula custos e tokens de cada transação
- ✅ Controla assinaturas e limites de usuários

## **🔒 Sistema de Segurança e Validação**

O Chatbot Service implementa um **gateway de segurança robusto** que valida todas as entradas antes de repassá-las para a IA:

### **1. Validações Básicas (Gate 0)**
- ✅ Mensagem vazia ou apenas espaços → **400 Bad Request**
- ✅ Comprimento mínimo (2 chars) e máximo (8.000 chars)
- ✅ Tipos MIME suportados
- ✅ Encoding UTF-8 válido

### **2. Higiene e Normalização**
- ✅ Trim e normalização de quebras de linha
- ✅ Remoção de bytes não imprimíveis
- ✅ Remoção de ZWJ/ZWSP (Zero Width Joiner/Space)
- ✅ Canonização de whitespace

### **3. Anti-Spam e Abuso**
- ✅ Detecção de padrões de spam
- ✅ Repetição excessiva de caracteres/palavras
- ✅ URLs suspeitas
- ✅ Rate limiting por usuário (30 req/min)

### **4. Segurança de Prompt**
- ✅ Detecção de prompt injection
- ✅ Palavras proibidas (hack, system, internal, etc.)
- ✅ Template markers ({{system}}, <tool>, etc.)
- ✅ Tentativas de roleplay/bypass

### **5. Moderação de Conteúdo**
- ✅ Discurso de ódio
- ✅ Conteúdo inadequado
- ✅ Políticas de uso
- ✅ Conformidade LGPD

### **6. Sanitização de PII**
- ✅ **CPF**: Mascaramento automático (***.***.***-**)
- ✅ **CNPJ**: Mascaramento automático (**.***.***/****-**)
- ✅ **Telefone**: Mascaramento automático (***-****-****)
- ✅ **Email**: Mascaramento parcial (***@dominio.com)

### **7. Validação de Formatos**
- ✅ **JSON**: Validação de sintaxe
- ✅ **CSV**: Estrutura e cabeçalhos
- ✅ **Datas**: Formato ISO 8601
- ✅ **Números**: Faixas e precisão

### **8. Validação de Anexos**
- ✅ Tamanho máximo (10MB)
- ✅ Extensões bloqueadas (.exe, .bat, .js, etc.)
- ✅ Tipos MIME permitidos
- ✅ Sanitização de metadados

### **9. Validadores Brasileiros**
- ✅ **CPF**: Validação com dígitos verificadores
- ✅ **CNPJ**: Validação com dígitos verificadores
- ✅ **Telefone**: Formato brasileiro com DDD
- ✅ **CEP**: Formato brasileiro
- ✅ **Datas**: Padrões brasileiros (DD/MM/YYYY)

## **🚀 Instalação e Configuração**

### **Pré-requisitos:**

- Python 3.11+
- Redis
- AI Service rodando na porta 8012

### **Instalação:**

```bash
# Clone o repositório
git clone <repository-url>
cd chatbot_service

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### **Variáveis de Ambiente:**

```env
# Configurações básicas
DEBUG=false
HOST=0.0.0.0
PORT=8008
LOG_LEVEL=INFO

# AI Service
AI_SERVICE_URL=http://localhost:8012
AI_SERVICE_TIMEOUT=30

# Redis
REDIS_URL=redis://localhost:6379/9

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### **Execução:**

```bash
# Desenvolvimento
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8008

# Produção
python main.py
```

## **📋 Endpoints Principais**

### **Processamento de Mensagens:**

#### **POST /chatbot/process-message**
Processa uma mensagem do usuário com validação de segurança completa.

**Request:**
```json
{
  "user_id": "123",
  "message": "Como está o preço da Petrobras hoje?",
  "session_id": "optional-session-id",
  "content_type": "text/plain"
}
```

**Response:**
```json
{
  "success": true,
  "response": {
    "response": "A Petrobras (PETR4) está cotada a R$ 38,50...",
    "provider": "openai",
    "conversation_id": 456,
    "tokens_used": 150
  },
  "metadata": {
    "processing_time": 0.85,
    "requires_ai": true,
    "cache_hit": false,
    "urgency": "medium",
    "keywords": ["ação", "preço", "petrobras"],
    "security_validation": {
      "original_length": 45,
      "sanitized_length": 45,
      "content_type": "text/plain",
      "validation_steps": "all_passed"
    }
  }
}
```

#### **POST /chatbot/validate-input**
Valida entrada sem processar (apenas validação de segurança).

**Request:**
```json
{
  "user_id": "123",
  "message": "Meu CPF é 123.456.789-00",
  "content_type": "text/plain"
}
```

**Response:**
```json
{
  "success": true,
  "validation": {
    "is_valid": true,
    "level": "pass",
    "message": "Mensagem validada com sucesso",
    "details": {
      "original_length": 25,
      "sanitized_length": 25,
      "content_type": "text/plain"
    },
    "sanitized_content": "Meu CPF é ***.***.***-**"
  }
}
```

#### **POST /chatbot/process-message/stream**
Processa mensagem em streaming para respostas em tempo real.

### **Gestão de Contexto:**

#### **GET /chatbot/conversation/{user_id}**
Busca contexto da conversa do usuário.

#### **POST /chatbot/update-context**
Atualiza resumo do contexto da conversa.

### **Analytics e Métricas:**

#### **GET /chatbot/analytics/{user_id}**
Busca analytics completos do usuário.

#### **GET /chatbot/cost-tracking/{user_id}**
Busca informações de custos e economia.

#### **GET /chatbot/cache-stats**
Estatísticas do cache.

#### **GET /chatbot/system-health**
Verifica saúde geral do sistema.

## **🔧 Funcionalidades Principais**

### **1. Filtros Inteligentes**

O serviço responde automaticamente a perguntas frequentes:

- **Saudações**: "Oi", "Olá", "Como você está?"
- **Perguntas sobre o sistema**: "Qual é o seu nome?", "Como funciona?"
- **Informações básicas**: "Que horas são?", "Obrigado", "Tchau"
- **Detecção de spam**: Bloqueia mensagens inadequadas

### **2. Cache Inteligente**

- **Cache em memória**: Respostas rápidas para perguntas similares
- **Cache Redis**: Persistência de cache entre reinicializações
- **Cache por contexto**: Considera histórico da conversa
- **TTL configurável**: Diferentes tempos para diferentes tipos de resposta

### **3. Otimização de Custos**

- **Redução de 40-60%** nas chamadas à IA
- **Respostas automáticas** para perguntas simples
- **Cache inteligente** para respostas similares
- **Monitoramento de custos** por usuário

### **4. Gestão de Contexto**

- **Histórico de conversas** por usuário
- **Detecção de mudança de tópico**
- **Resumo de contexto** para IA
- **Sessões ativas** com timeout

### **5. Integração com AI Service**

- **Verificação de limites** antes de chamar IA
- **Consulta de configurações** do usuário
- **Envio de metadados** para rastreamento
- **Fallback inteligente** em caso de erro

### **6. 🔒 Gateway de Segurança**

- **Validação completa** de todas as entradas
- **Sanitização automática** de PII
- **Detecção de ataques** (prompt injection, spam)
- **Conformidade LGPD** e políticas de uso
- **Rate limiting** inteligente
- **Validadores brasileiros** (CPF, CNPJ, telefone)

## **📊 Métricas e Monitoramento**

### **Métricas de Performance:**

- Taxa de respostas diretas (sem IA)
- Tempo médio de resposta
- Taxa de cache hit
- Uptime e disponibilidade

### **Métricas de Custos:**

- Custo por conversa
- Custo por usuário
- Economia com cache
- Distribuição por provider

### **Métricas de Qualidade:**

- Satisfação do usuário
- Taxa de sucesso das chamadas à IA
- Taxa de fallback
- Contexto mantido vs perdido

### **Métricas de Segurança:**

- Taxa de rejeição por validação
- Tipos de ataques detectados
- PII detectada e mascarada
- Rate limiting aplicado

## **🔍 Exemplos de Uso**

### **Exemplo 1: Pergunta Simples (Resposta Automática)**

```bash
curl -X POST "http://localhost:8008/chatbot/process-message" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123",
    "message": "Oi, como você está?"
  }'
```

**Resposta:**
```json
{
  "success": true,
  "response": {
    "response": "Estou funcionando perfeitamente! Pronto para ajudá-lo com suas dúvidas sobre investimentos e trading.",
    "confidence": 0.90,
    "category": "system_status"
  },
  "metadata": {
    "processing_time": 0.02,
    "requires_ai": false,
    "cache_hit": false,
    "auto_response": true,
    "security_validation": {
      "original_length": 20,
      "sanitized_length": 20,
      "content_type": "text/plain",
      "validation_steps": "all_passed"
    }
  }
}
```

### **Exemplo 2: Pergunta Complexa (Requer IA)**

```bash
curl -X POST "http://localhost:8008/chatbot/process-message" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123",
    "message": "Qual é a análise técnica da Petrobras para esta semana?"
  }'
```

**Resposta:**
```json
{
  "success": true,
  "response": {
    "response": "Baseado na análise técnica da Petrobras (PETR4)...",
    "provider": "openai",
    "conversation_id": 456,
    "tokens_used": 250
  },
  "metadata": {
    "processing_time": 1.25,
    "requires_ai": true,
    "cache_hit": false,
    "urgency": "medium",
    "keywords": ["análise", "técnica", "petrobras"],
    "security_validation": {
      "original_length": 65,
      "sanitized_length": 65,
      "content_type": "text/plain",
      "validation_steps": "all_passed"
    }
  }
}
```

### **Exemplo 3: Validação de Segurança**

```bash
curl -X POST "http://localhost:8008/chatbot/validate-input" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123",
    "message": "Meu CPF é 123.456.789-00 e telefone (11) 99999-9999"
  }'
```

**Resposta:**
```json
{
  "success": true,
  "validation": {
    "is_valid": true,
    "level": "pass",
    "message": "Mensagem validada com sucesso",
    "details": {
      "original_length": 50,
      "sanitized_length": 50,
      "content_type": "text/plain"
    },
    "sanitized_content": "Meu CPF é ***.***.***-** e telefone ***-****-****"
  }
}
```

## **🛠️ Desenvolvimento**

### **Estrutura do Projeto:**

```
chatbot_service/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configurações
│   ├── app.py             # Aplicação FastAPI
│   └── main.py            # Ponto de entrada
├── models/
│   ├── __init__.py
│   └── conversation_context.py  # Modelos de dados
├── services/
│   ├── __init__.py
│   ├── cache_service.py       # Serviço de cache
│   ├── context_service.py     # Gestão de contexto
│   ├── ai_integration.py      # Integração com AI Service
│   ├── filters/
│   │   ├── __init__.py
│   │   └── message_filters.py # Filtros de mensagens
│   └── security/
│       ├── __init__.py
│       ├── input_validator.py # Validação de entrada
│       └── brazilian_validators.py # Validadores BR
├── routes/
│   ├── __init__.py
│   ├── chat_router.py         # Endpoints de chat
│   └── analytics_router.py    # Endpoints de analytics
├── tests/
│   └── test_basic.py          # Testes básicos
├── examples/
│   ├── usage_examples.py      # Exemplos de uso
│   └── security_validation_examples.py # Exemplos de segurança
├── requirements.txt           # Dependências atualizadas
├── Dockerfile                 # Configuração Docker
├── README.md                  # Documentação completa
├── env.example               # Configuração de exemplo
├── start_dev.py              # Script de desenvolvimento
└── pytest.ini               # Configuração de testes
```

### **Executando Testes:**

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio

# Executar testes
pytest tests/

# Executar exemplos de uso
python examples/usage_examples.py

# Executar exemplos de segurança
python examples/security_validation_examples.py
```

### **Logs:**

O serviço usa `structlog` para logs estruturados:

```python
import structlog

logger = structlog.get_logger(__name__)
logger.info("Mensagem processada", user_id="123", processing_time=0.85)
```

## **🐳 Docker**

### **Build da Imagem:**

```bash
docker build -t chatbot-service .
```

### **Execução com Docker:**

```bash
docker run -p 8008:8008 \
  -e REDIS_URL=redis://redis:6379/9 \
  -e AI_SERVICE_URL=http://ai-service:8012 \
  chatbot-service
```

### **Docker Compose:**

```yaml
version: '3.8'
services:
  chatbot-service:
    build: .
    ports:
      - "8008:8008"
    environment:
      - REDIS_URL=redis://redis:6379/9
      - AI_SERVICE_URL=http://ai-service:8012
    depends_on:
      - redis
      - ai-service
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  ai-service:
    image: ai-service:latest
    ports:
      - "8012:8012"
```

## **🔒 Segurança**

### **Validações Implementadas:**

- ✅ **Validação de entrada** em todas as mensagens
- ✅ **Detecção de spam** e conteúdo inadequado
- ✅ **Rate limiting** inteligente (30 req/min por usuário)
- ✅ **Verificação de limites** de usuário
- ✅ **Logs de auditoria** para todas as operações
- ✅ **Sanitização automática** de PII
- ✅ **Detecção de prompt injection**
- ✅ **Validadores brasileiros** (CPF, CNPJ, telefone)
- ✅ **Conformidade LGPD**

### **Códigos de Erro HTTP:**

- **400** - "Sua mensagem está vazia ou muito curta."
- **413** - "Sua mensagem ultrapassa o limite permitido."
- **415** - "Tipo de arquivo não suportado."
- **422** - "O JSON está inválido: campo obrigatório."
- **429** - "Muitas requisições. Tente novamente em alguns segundos."
- **451** - "O conteúdo não atende às nossas políticas."

## **📈 Performance**

### **Otimizações Implementadas:**

- **Cache em memória** para respostas rápidas
- **Cache Redis** para persistência
- **Respostas automáticas** para reduzir latência
- **Streaming** para respostas em tempo real
- **Limpeza automática** de sessões expiradas
- **Validação eficiente** com early returns

### **Benchmarks Esperados:**

- **Tempo de resposta**: < 100ms para cache hits
- **Taxa de cache hit**: 60-80%
- **Redução de custos**: 40-60%
- **Uptime**: 99.9%
- **Validação de segurança**: < 50ms

## **🤝 Contribuição**

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## **📄 Licença**

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## **📞 Suporte**

Para suporte e dúvidas:

- **Email**: suporte@b3trader.com
- **Documentação**: `/docs` (quando DEBUG=true)
- **Issues**: GitHub Issues

---

**🎯 Objetivo**: Reduzir custos de IA em 40-60% mantendo alta qualidade de resposta e segurança máxima! 🚀🔒
