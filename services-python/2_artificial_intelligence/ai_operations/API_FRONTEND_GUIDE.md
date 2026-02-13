# API B3 FastAPI AI - Guia para Frontend

## 📋 Informações Gerais

**Base URL:** `http://localhost:8012`  
**Content-Type:** `application/json`  
**Porta:** 8012 (configurada no .env)  

---

## 🔗 Endpoints Disponíveis

### 1. Health Check
**GET** `/chatbot/health`

**Resposta:**
```json
{
  "status": "healthy",
  "service": "chatbot"
}
```

---

### 2. Listar Provedores de IA
**GET** `/ai/providers`

**Resposta:**
```json
{
  "providers": [
    {
      "name": "openai",
      "available": true,
      "models": ["gpt-5-nano", "gpt-4.1-nano", "gpt-5-mini", "gpt-4o-mini"],
      "description": "OpenAI GPT - Modelos avançados de linguagem natural"
    },
    {
      "name": "deepseek",
      "available": true,
      "models": ["deepseek-chat", "deepseek-coder"],
      "description": "DeepSeek - Modelos especializados em código e chat"
    },
    {
      "name": "ollama",
      "available": true,
      "models": ["llama2", "codellama", "mistral", "neural-chat"],
      "description": "Ollama - Modelos locais de código aberto"
    }
  ],
  "default_provider": "openai",
  "supported_providers": ["openai", "deepseek", "ollama"]
}
```

---

### 3. Listar Modelos por Provedor
**GET** `/ai/models?provider=openai`

**Parâmetros:**
- `provider` (opcional): openai, deepseek, ollama

**Resposta (com provedor específico):**
```json
{
  "provider": "openai",
  "models": ["gpt-5-nano", "gpt-4.1-nano", "gpt-5-mini", "gpt-4o-mini"],
  "default_model": "gpt-5-nano"
}
```

**Resposta (todos os provedores):**
```json
{
  "providers": {
    "openai": {
      "models": ["gpt-5-nano", "gpt-4.1-nano", "gpt-5-mini", "gpt-4o-mini"],
      "default_model": "gpt-5-nano"
    },
    "deepseek": {
      "models": ["deepseek-chat", "deepseek-coder"],
      "default_model": "deepseek-chat"
    },
    "ollama": {
      "models": ["llama2", "codellama", "mistral", "neural-chat"],
      "default_model": "llama3.1"
    }
  },
  "default_provider": "openai"
}
```

---

### 4. Gerar Resposta de IA
**POST** `/ai/generate`

**Requisição:**
```json
{
  "message": "Analise a seguinte operação: Compra 100 PETR4 a R$ 35,50",
  "provider": "openai",
  "model": "gpt-5-nano",
  "max_tokens": 150,
  "temperature": 0.7
}
```

**Campos da Requisição:**
- `message` (obrigatório): Mensagem do usuário
- `provider` (opcional): openai, deepseek, ollama (padrão: openai)
- `model` (opcional): Modelo específico (padrão: modelo padrão do provedor)
- `max_tokens` (opcional): Máximo de tokens na resposta (padrão: 1000)
- `temperature` (opcional): Criatividade da resposta 0.0-1.0 (padrão: 0.7)

**Resposta:**
```json
{
  "response": "Esta operação representa uma compra de 100 ações da Petrobras (PETR4) ao preço de R$ 35,50 por ação. O valor total da operação seria R$ 3.550,00. Considerando o cenário atual do mercado...",
  "provider": "openai",
  "model": "gpt-5-nano",
  "total_tokens": 145
}
```

---

### 5. Streaming de Resposta
**POST** `/ai/stream`

**Requisição:**
```json
{
  "messages": [
    {"role": "user", "content": "Explique o que é stop loss"}
  ],
  "provider": "openai",
  "model": "gpt-5-nano",
  "max_tokens": 200,
  "temperature": 0.7
}
```

**Campos da Requisição:**
- `messages` (obrigatório): Array de mensagens no formato OpenAI
- `provider` (opcional): openai, deepseek, ollama
- `model` (opcional): Modelo específico
- `max_tokens` (opcional): Máximo de tokens
- `temperature` (opcional): Criatividade da resposta

**Resposta (Stream):**
Cada chunk retorna:
```json
{"content": "Stop", "done": false}
{"content": " loss", "done": false}
{"content": " é", "done": false}
{"content": " uma", "done": false}
...
{"content": "", "done": true}
```

---

## 🎯 Modelos Disponíveis

### OpenAI
| Modelo | Uso Recomendado | Custo | Características |
|--------|----------------|-------|----------------|
| `gpt-5-nano` | Prototipagem rápida | Mais barato | Rápido, econômico |
| `gpt-4.1-nano` | Testes rápidos | Muito barato | Protótipos, validação |
| `gpt-5-mini` | Produção econômica | Médio | Equilibrio custo/qualidade |
| `gpt-4o-mini` | Produção | Médio-alto | Melhor qualidade |

### DeepSeek
| Modelo | Uso Recomendado |
|--------|----------------|
| `deepseek-chat` | Conversas gerais |
| `deepseek-coder` | Programação |

### Ollama
| Modelo | Uso Recomendado |
|--------|----------------|
| `llama2` | Conversas gerais |
| `codellama` | Programação |
| `mistral` | Análises |
| `neural-chat` | Chat avançado |

---

## 🔧 Configurações Especiais

### Modelos GPT-5 e GPT-4.1-nano
Estes modelos têm configurações especiais:
- Usam `max_completion_tokens` em vez de `max_tokens`
- `temperature` fixo em 1.0
- Otimizados para velocidade

### Tratamento de Erros
**Códigos de Status:**
- `200`: Sucesso
- `400`: Erro na requisição (parâmetros inválidos)
- `404`: Recurso não encontrado
- `500`: Erro interno do servidor

**Formato de Erro:**
```json
{
  "detail": "Descrição do erro"
}
```

---

## 📝 Exemplos de Uso

### JavaScript/Fetch
```javascript
// Gerar resposta simples
const response = await fetch('http://localhost:8012/ai/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: "Analise PETR4",
    provider: "openai",
    model: "gpt-5-nano",
    max_tokens: 100
  })
});

const data = await response.json();
console.log(data.response);
```

### Python/Requests
```python
import requests

response = requests.post('http://localhost:8012/ai/generate', json={
    "message": "Analise VALE3",
    "provider": "openai",
    "model": "gpt-5-nano",
    "max_tokens": 100
})

data = response.json()
print(data['response'])
```

### cURL
```bash
curl -X POST "http://localhost:8012/ai/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analise ITUB4",
    "provider": "openai",
    "model": "gpt-5-nano",
    "max_tokens": 100
  }'
```

---

## 🚀 Casos de Uso para Homebroker

### 1. Análise de Ações
```json
{
  "message": "Analise a ação PETR4 considerando o cenário atual do mercado",
  "provider": "openai",
  "model": "gpt-5-mini",
  "max_tokens": 200
}
```

### 2. Configuração de Stop Loss
```json
{
  "message": "Configure stop loss para VALE3: preço atual R$ 68,20, stop em R$ 65,00",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "max_tokens": 150
}
```

### 3. Análise de Carteira
```json
{
  "message": "Analise esta carteira: 40% PETR4, 30% VALE3, 20% ITUB4, 10% BBAS3",
  "provider": "openai",
  "model": "gpt-5-mini",
  "max_tokens": 300
}
```

### 4. Recomendações de Timing
```json
{
  "message": "É 15:30 de uma sexta-feira. Devo comprar MGLU3 agora ou aguardar?",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "max_tokens": 200
}
```

---

## ⚡ Dicas de Performance

1. **Use gpt-5-nano** para respostas rápidas e baratas
2. **Use gpt-4o-mini** para análises mais detalhadas
3. **Limite max_tokens** para respostas mais focadas
4. **Use streaming** para interfaces mais responsivas
5. **Cache respostas** quando apropriado
6. **Implemente timeout** nas requisições (30s recomendado)

---

## 🔒 Segurança

- API keys estão no servidor (não expostas ao frontend)
- CORS configurado para aceitar todas as origens (*)
- Logs detalhados para auditoria
- Rate limiting pode ser implementado conforme necessário

---

## 📊 Monitoramento

- Logs disponíveis em `/logs/chatbot_middleware_YYYYMMDD.log`
- Health check em `/chatbot/health`
- Métricas de uso por modelo disponíveis nos logs

---

**Última atualização:** Janeiro 2025  
**Versão da API:** 1.0  
**Suporte:** Consulte os logs para debugging