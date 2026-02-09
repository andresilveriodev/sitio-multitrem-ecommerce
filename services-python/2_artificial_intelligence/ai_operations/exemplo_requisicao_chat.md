# Exemplo de Requisição - Endpoint /ai/chat

## Endpoint
```
POST http://localhost:8012/ai/chat
```

## Headers
```
Content-Type: application/json
```

## Body (JSON)
```json
{
  "message": "Oi, tudo bem?"
}
```

## Exemplo com cURL
```bash
curl -X POST http://localhost:8012/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Oi, tudo bem?"}'
```

## Exemplo com Python (httpx)
```python
import httpx

response = httpx.post(
    "http://localhost:8012/ai/chat",
    json={"message": "Oi, tudo bem?"}
)

print(response.json())
# {"reply": "Oi! Tudo certo, e você? Como posso ajudar hoje?"}
```

## Exemplo com JavaScript (fetch)
```javascript
fetch('http://localhost:8012/ai/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'Oi, tudo bem?'
  })
})
.then(response => response.json())
.then(data => console.log(data));
// {reply: "Oi! Tudo certo, e você? Como posso ajudar hoje?"}
```

## Resposta de Sucesso (200 OK)
```json
{
  "reply": "Oi! Tudo certo, e você? Como posso ajudar hoje?"
}
```

## Estrutura da Requisição

### ChatRequest
```json
{
  "message": "string"  // Mensagem do usuário (obrigatório)
}
```

### ChatResponse
```json
{
  "reply": "string"  // Resposta da IA
}
```

## Exemplos de Mensagens

### Exemplo 1: Saudação
```json
{
  "message": "Olá, como você está?"
}
```

### Exemplo 2: Pergunta
```json
{
  "message": "Qual é a capital do Brasil?"
}
```

### Exemplo 3: Conversa
```json
{
  "message": "Me explique o que é inteligência artificial"
}
```

