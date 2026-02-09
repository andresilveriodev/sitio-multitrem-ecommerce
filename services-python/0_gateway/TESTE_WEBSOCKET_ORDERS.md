# 🧪 Guia de Teste - WebSocket de Ordens

## ✅ Checklist Pré-Teste

- [ ] Redis está rodando e acessível na porta 6379
- [ ] Trade Service está publicando no Redis DB 5 no canal `ORDER_UPDATE:{order_id}`
- [ ] Gateway Service está rodando na porta 8000

## 🚀 Como Testar

### 1. Iniciar o Gateway Service

```bash
# No diretório do gateway
python main.py
# ou
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Verificar se o endpoint está disponível

O endpoint WebSocket estará disponível em:
```
ws://localhost:8000/ws/orders
```

### 3. Teste com Python (script de exemplo)

Crie um arquivo `test_order_websocket.py`:

```python
import asyncio
import websockets
import json

async def test_order_websocket():
    uri = "ws://localhost:8000/ws/orders"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Conectado ao WebSocket de ordens")
        
        # Assinar ordem ID 123
        subscribe_msg = {
            "action": "subscribe",
            "type": "order",
            "order_id": 123
        }
        await websocket.send(json.dumps(subscribe_msg))
        print(f"📤 Enviado: {subscribe_msg}")
        
        # Escutar mensagens
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"📥 Recebido: {data}")
                
                if data.get("action") == "order_update":
                    print(f"🔄 Ordem {data['order_id']} atualizada!")
                    print(f"   Status: {data['data'].get('status')}")
                    print(f"   Preço: {data['data'].get('price')}")
        except KeyboardInterrupt:
            print("\n🔌 Desconectando...")

if __name__ == "__main__":
    asyncio.run(test_order_websocket())
```

Execute:
```bash
pip install websockets
python test_order_websocket.py
```

### 4. Teste com JavaScript/Node.js

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8000/ws/orders');

ws.on('open', () => {
    console.log('✅ Conectado ao WebSocket de ordens');
    
    // Assinar ordem ID 123
    ws.send(JSON.stringify({
        action: 'subscribe',
        type: 'order',
        order_id: 123
    }));
});

ws.on('message', (data) => {
    const message = JSON.parse(data);
    console.log('📥 Recebido:', message);
    
    if (message.action === 'order_update') {
        console.log(`🔄 Ordem ${message.order_id} atualizada!`);
        console.log(`   Status: ${message.data.status}`);
        console.log(`   Preço: ${message.data.price}`);
    }
});

ws.on('error', (error) => {
    console.error('❌ Erro:', error);
});

ws.on('close', () => {
    console.log('🔌 Desconectado');
});
```

### 5. Teste no Browser (Console)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/orders');

ws.onopen = () => {
    console.log('✅ Conectado');
    
    // Assinar ordem
    ws.send(JSON.stringify({
        action: 'subscribe',
        type: 'order',
        order_id: 123
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('📥 Recebido:', message);
};

ws.onerror = (error) => {
    console.error('❌ Erro:', error);
};
```

## 📡 Simular Publicação no Redis

Para testar sem o Trade Service, você pode publicar manualmente no Redis:

```bash
# Conectar ao Redis DB 5
redis-cli -n 5

# Publicar atualização de ordem
PUBLISH ORDER_UPDATE:123 '{"id":123,"account_id":7,"price":"32.50","status":"FILLED","offers":[{"offer_id":"of_123","symbol":"PETR4","operation":"BUY","qtty":"100.0","filled":"100.0","amount":"3250.0","status":"FILLED"}]}'
```

## 🔍 Verificar Logs

Os logs do Gateway mostrarão:
- `✅ OrderWebSocketService inicializado`
- `📡 Assinado canal Redis: ORDER_UPDATE:123`
- `📤 [REDIS] Ordem 123: X/Y enviadas`

## ⚠️ Troubleshooting

### Erro: "Service unavailable"
- Verifique se o Redis está rodando
- Verifique se o Redis DB 5 está acessível

### Erro: "Connection refused"
- Verifique se o Gateway está rodando na porta 8000
- Verifique se há firewall bloqueando

### Não recebe atualizações
- Verifique se o Trade Service está publicando no Redis DB 5
- Verifique se o canal está correto: `ORDER_UPDATE:{order_id}`
- Verifique os logs do Gateway para erros

### WebSocket fecha imediatamente
- Verifique os logs do Gateway
- Verifique se há exceções sendo lançadas

## 📝 Mensagens Esperadas

### Confirmação de Assinatura
```json
{
  "action": "subscribed",
  "type": "order",
  "order_id": 123,
  "status": "success"
}
```

### Atualização de Ordem
```json
{
  "action": "order_update",
  "type": "order",
  "order_id": 123,
  "data": {
    "id": 123,
    "account_id": 7,
    "status": "FILLED",
    "price": "32.50",
    ...
  }
}
```

### Ping (Heartbeat)
```json
{
  "action": "ping",
  "type": "heartbeat"
}
```



