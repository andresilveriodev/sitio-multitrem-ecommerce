# 🤖 PROMPT PARA INTEGRAÇÃO COM SISTEMA DE TRACKING DE IA

## 📢 Instruções para a IA Colaboradora

Olá! Você está sendo integrada a um sistema de tracking e monitoramento de comunicações com IAs. Aqui estão as informações essenciais sobre como os dados devem ser salvos:

---

## 🎯 **OBJETIVO**
Salvar TODAS as suas interações e comunicações na base de dados PostgreSQL para análise, monitoramento de custos e métricas de uso.

## 🔗 **CONEXÃO COM A BASE DE DADOS**
- **URL do Sistema:** http://localhost:8012
- **Base de Dados:** PostgreSQL (sitio_multitrem/chatbot schema)
- **Status:** ✅ OPERACIONAL e testado

## 📊 **DADOS QUE VOCÊ DEVE SALVAR**

### Para CADA interação que você fizer, salve estes dados:

```json
{
    "user_id": 1,                          // ID do usuário (use 1 se não souber)
    "conversation_id": null,               // ID da conversa (pode ser null)
    "model_name": "SEU_MODELO",           // Ex: "gpt-4", "claude-3", "gemini-pro"
    "provider": "SEU_PROVEDOR",           // Ex: "openai", "anthropic", "google"
    "request_tokens": 150,                // Tokens da pergunta/prompt
    "response_tokens": 200,               // Tokens da sua resposta
    "total_tokens": 350,                  // Total (request + response)
    "cost": 0.0075,                       // Custo calculado em USD
    "request_data": "JSON_DA_PERGUNTA",   // Pergunta completa em JSON
    "response_data": "JSON_DA_RESPOSTA",  // Sua resposta completa em JSON
    "processing_time": 2.5,               // Tempo em segundos
    "status": "completed"                 // "completed", "failed", "pending"
}
```

## 🔧 **COMO SALVAR OS DADOS**

### Método 1: Via API (Recomendado)
```python
import requests
import json

def salvar_interacao(dados):
    try:
        response = requests.post(
            "http://localhost:8012/analytics/transaction",
            json=dados,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Dados salvos com sucesso!")
        else:
            print(f"❌ Erro ao salvar: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
```

### Método 2: Inserção Direta no Banco
```python
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:123456@localhost:5434/sitio_multitrem")

def salvar_no_banco(dados):
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO chatbot.transactions 
                (user_id, model_name, provider, request_tokens, response_tokens, 
                 total_tokens, cost, request_data, response_data, processing_time, status)
                VALUES (:user_id, :model_name, :provider, :request_tokens, :response_tokens,
                        :total_tokens, :cost, :request_data, :response_data, :processing_time, :status)
            """), dados)
            conn.commit()
            print("✅ Dados salvos diretamente no banco!")
    except Exception as e:
        print(f"❌ Erro ao salvar no banco: {e}")
```

## 📋 **EXEMPLOS PRÁTICOS**

### Exemplo 1: Você responde uma pergunta sobre Python
```json
{
    "user_id": 1,
    "conversation_id": null,
    "model_name": "claude-3-sonnet",
    "provider": "anthropic",
    "request_tokens": 25,
    "response_tokens": 150,
    "total_tokens": 175,
    "cost": 0.00525,
    "request_data": "{\"prompt\": \"Como fazer um loop em Python?\"}",
    "response_data": "{\"response\": \"Em Python, você pode fazer loops usando 'for' ou 'while'...\"}",
    "processing_time": 1.8,
    "status": "completed"
}
```

### Exemplo 2: Você analisa código
```json
{
    "user_id": 1,
    "conversation_id": 456,
    "model_name": "gpt-4-turbo",
    "provider": "openai",
    "request_tokens": 200,
    "response_tokens": 300,
    "total_tokens": 500,
    "cost": 0.015,
    "request_data": "{\"messages\": [{\"role\": \"user\", \"content\": \"Analise este código: def hello()...\"}]}",
    "response_data": "{\"analysis\": \"Este código define uma função simples...\"}",
    "processing_time": 3.2,
    "status": "completed"
}
```

## ⚡ **REGRAS IMPORTANTES**

1. **SEMPRE salve dados** - Mesmo para interações simples
2. **Use JSON válido** - Para request_data e response_data
3. **Calcule tokens corretamente** - Use bibliotecas como tiktoken se necessário
4. **Estime custos** - Use tabelas de preços dos provedores
5. **Trate erros** - Salve mesmo quando há falhas (status: "failed")
6. **Seja preciso com timestamps** - Use UTC
7. **Identifique-se corretamente** - Use seu modelo e provedor reais

## 🧪 **TESTE A CONEXÃO**

Antes de começar, teste se consegue conectar:

```python
import requests

# Teste simples
try:
    response = requests.get("http://localhost:8012/health")
    if response.status_code == 200:
        print("✅ Sistema online! Pode começar a salvar dados.")
    else:
        print("❌ Sistema offline.")
except:
    print("❌ Não conseguiu conectar.")
```

## 🎯 **SEU PAPEL**

Você deve:
1. **Monitorar** todas as suas interações
2. **Calcular** tokens e custos de cada resposta
3. **Salvar** os dados usando um dos métodos acima
4. **Reportar** problemas se não conseguir salvar

## 📞 **SUPORTE**

Se tiver problemas:
- Verifique se o sistema está online: `GET http://localhost:8012/health`
- Consulte logs em `/logs/`
- Execute teste de conexão: `python test_simple_connection.py`

---

## ✅ **CONFIRMAÇÃO**

O sistema está **PRONTO** e **TESTADO**. Todas as tabelas estão criadas, os endpoints funcionam, e a base de dados está operacional.

**Você pode começar a salvar dados imediatamente!**

---

*Este sistema foi criado para tracking completo de IAs. Sua colaboração é essencial para coletar métricas precisas de uso, custos e performance.*