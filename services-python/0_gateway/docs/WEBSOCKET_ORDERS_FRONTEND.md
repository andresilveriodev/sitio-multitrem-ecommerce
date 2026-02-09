# WebSocket de Ordens - Guia para Frontend

## 📋 Visão Geral

O Gateway fornece um WebSocket para receber atualizações de ordens em tempo real. Quando uma ordem é criada, atualizada ou executada no Trade Service, o frontend recebe automaticamente a atualização via WebSocket.

## 🔌 Conexão

### Endpoint

```
ws://localhost:8000/ws/orders?token={JWT_TOKEN}
```

**Importante:**
- O token JWT deve ser passado como query parameter
- O token é validado na conexão
- Se o token for inválido, a conexão será fechada com código 1008

### Exemplo de Conexão

```javascript
const token = localStorage.getItem('token'); // ou de onde você armazena o token
const ws = new WebSocket(`ws://localhost:8000/ws/orders?token=${token}`);
```

---

## 📤 Mensagens do Frontend → Gateway

### 1. Assinar uma Ordem

Solicita atualizações para uma ordem específica:

```json
{
  "action": "subscribe",
  "type": "order",
  "order_id": 123
}
```

**Resposta de Confirmação:**
```json
{
  "action": "subscribed",
  "type": "order",
  "order_id": 123,
  "status": "success"
}
```

### 2. Assinar Múltiplas Ordens

Assina várias ordens de uma vez:

```json
{
  "action": "subscribe",
  "type": "orders",
  "order_ids": [123, 456, 789]
}
```

**Resposta:**
```json
{
  "action": "subscribed",
  "type": "orders",
  "order_ids": [123, 456, 789],
  "status": "success"
}
```

### 3. Cancelar Assinatura

Cancela a assinatura de uma ordem:

```json
{
  "action": "unsubscribe",
  "type": "order",
  "order_id": 123
}
```

**Resposta:**
```json
{
  "action": "unsubscribed",
  "type": "order",
  "order_id": 123,
  "status": "success"
}
```

---

## 📥 Mensagens do Gateway → Frontend

### 1. Atualização de Ordem

Recebida quando a ordem é atualizada no Trade Service:

```json
{
  "action": "order_update",
  "type": "order",
  "order_id": 123,
  "data": {
    "id": 123,
    "account_id": 7,
    "price": "32.50",
    "stop_loss": "31.50",
    "take_profit": "33.50",
    "status": "FILLED",
    "start_date": "2025-12-03T05:07:46-03:00",
    "end_date": "2025-12-04T02:59:59-03:00",
    "created_at": "2025-12-03T02:07:48-03:00",
    "updated_at": "2025-12-03T02:08:15-03:00",
    "comments": null,
    "offers": [
      {
        "offer_id": "of_0a0924c181f04c68",
        "symbol": "PETR4",
        "operation": "BUY",
        "qtty": "100.0",
        "filled": "100.0",
        "amount": "3250.0",
        "status": "FILLED"
      }
    ],
    "broker_params": {
      "broker_name": "MT5",
      "order_type": "Pendente",
      "type_filling": "RETURN",
      "deviation": 20,
      "magic": 7001,
      "comment": ""
    }
  }
}
```

### 2. Erro

Recebida quando há erro na assinatura ou processamento:

```json
{
  "action": "error",
  "type": "order",
  "order_id": 123,
  "message": "Order not found or access denied"
}
```

---

## 💻 Exemplos de Implementação

### JavaScript Vanilla

```javascript
class OrderWebSocket {
  constructor(token) {
    this.token = token;
    this.ws = null;
    this.subscribedOrders = new Set();
    this.onOrderUpdate = null; // Callback para atualizações
  }

  connect() {
    const url = `ws://localhost:8000/ws/orders?token=${this.token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('✅ WebSocket de ordens conectado');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('❌ Erro no WebSocket:', error);
    };

    this.ws.onclose = (event) => {
      console.log('🔌 WebSocket fechado:', event.code, event.reason);
      // Reconectar após 3 segundos
      setTimeout(() => this.connect(), 3000);
    };
  }

  handleMessage(message) {
    switch (message.action) {
      case 'subscribed':
        console.log(`✅ Assinado na ordem ${message.order_id}`);
        this.subscribedOrders.add(message.order_id);
        break;

      case 'unsubscribed':
        console.log(`✅ Cancelada assinatura da ordem ${message.order_id}`);
        this.subscribedOrders.delete(message.order_id);
        break;

      case 'order_update':
        console.log('📊 Atualização de ordem:', message.order_id, message.data);
        if (this.onOrderUpdate) {
          this.onOrderUpdate(message.data);
        }
        break;

      case 'error':
        console.error('❌ Erro:', message.message);
        break;

      default:
        console.warn('Mensagem desconhecida:', message);
    }
  }

  subscribe(orderId) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'subscribe',
        type: 'order',
        order_id: orderId
      }));
    } else {
      console.error('WebSocket não está conectado');
    }
  }

  subscribeMultiple(orderIds) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'subscribe',
        type: 'orders',
        order_ids: orderIds
      }));
    } else {
      console.error('WebSocket não está conectado');
    }
  }

  unsubscribe(orderId) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'unsubscribe',
        type: 'order',
        order_id: orderId
      }));
    } else {
      console.error('WebSocket não está conectado');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Uso
const token = localStorage.getItem('token');
const orderWS = new OrderWebSocket(token);

orderWS.onOrderUpdate = (order) => {
  // Atualizar UI com a ordem
  updateOrderInList(order);
  
  // Mostrar notificação se status mudou
  if (order.status === 'FILLED') {
    showNotification(`Ordem ${order.id} executada!`);
  }
};

orderWS.connect();

// Assinar ordens
orderWS.subscribe(123);
orderWS.subscribeMultiple([456, 789]);

// Cancelar assinatura
orderWS.unsubscribe(123);
```

---

### React Hook

```typescript
import { useEffect, useRef, useState, useCallback } from 'react';

interface Order {
  id: number;
  account_id: number;
  status: string;
  price: string;
  // ... outros campos
}

interface OrderUpdateMessage {
  action: string;
  type: string;
  order_id: number;
  data: Order;
}

export function useOrderWebSocket(token: string | null) {
  const [orders, setOrders] = useState<Map<number, Order>>(new Map());
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const subscribedOrdersRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    if (!token) {
      return;
    }

    const url = `ws://localhost:8000/ws/orders?token=${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket de ordens conectado');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const message: OrderUpdateMessage = JSON.parse(event.data);

      switch (message.action) {
        case 'subscribed':
          subscribedOrdersRef.current.add(message.order_id);
          break;

        case 'unsubscribed':
          subscribedOrdersRef.current.delete(message.order_id);
          break;

        case 'order_update':
          setOrders((prev) => {
            const newMap = new Map(prev);
            newMap.set(message.order_id, message.data);
            return newMap;
          });
          break;

        case 'error':
          console.error('Erro:', message);
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('❌ Erro no WebSocket:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('🔌 WebSocket fechado');
      setIsConnected(false);
      // Reconectar após 3 segundos
      setTimeout(() => {
        if (token) {
          // Reconectar
        }
      }, 3000);
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [token]);

  const subscribe = useCallback((orderId: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        type: 'order',
        order_id: orderId
      }));
    }
  }, []);

  const subscribeMultiple = useCallback((orderIds: number[]) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        type: 'orders',
        order_ids: orderIds
      }));
    }
  }, []);

  const unsubscribe = useCallback((orderId: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        type: 'order',
        order_id: orderId
      }));
    }
  }, []);

  return {
    orders,
    isConnected,
    subscribe,
    subscribeMultiple,
    unsubscribe
  };
}

// Uso no componente
function OrderList() {
  const token = localStorage.getItem('token');
  const { orders, isConnected, subscribe, subscribeMultiple } = useOrderWebSocket(token);

  useEffect(() => {
    // Assinar ordens quando o componente montar
    if (isConnected) {
      // Exemplo: assinar ordens específicas
      subscribe(123);
      subscribeMultiple([456, 789]);
    }
  }, [isConnected, subscribe, subscribeMultiple]);

  return (
    <div>
      <p>Status: {isConnected ? '✅ Conectado' : '❌ Desconectado'}</p>
      <ul>
        {Array.from(orders.values()).map((order) => (
          <li key={order.id}>
            Ordem {order.id} - Status: {order.status}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

### React Hook para uma Ordem Específica

```typescript
import { useEffect, useState, useRef } from 'react';

export function useOrderUpdates(orderId: number, token: string | null) {
  const [order, setOrder] = useState<Order | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token || !orderId) {
      return;
    }

    const url = `ws://localhost:8000/ws/orders?token=${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      // Assinar a ordem imediatamente após conectar
      ws.send(JSON.stringify({
        action: 'subscribe',
        type: 'order',
        order_id: orderId
      }));
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.action === 'order_update' && message.order_id === orderId) {
        setOrder(message.data);
      }
    };

    ws.onerror = (error) => {
      console.error('Erro no WebSocket:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      // Cancelar assinatura antes de fechar
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          action: 'unsubscribe',
          type: 'order',
          order_id: orderId
        }));
      }
      ws.close();
      wsRef.current = null;
    };
  }, [orderId, token]);

  return { order, isConnected };
}

// Uso
function OrderDetail({ orderId }: { orderId: number }) {
  const token = localStorage.getItem('token');
  const { order, isConnected } = useOrderUpdates(orderId, token);

  if (!order) {
    return <div>Carregando...</div>;
  }

  return (
    <div>
      <p>Status da conexão: {isConnected ? '✅' : '❌'}</p>
      <h2>Ordem {order.id}</h2>
      <p>Status: {order.status}</p>
      <p>Preço: {order.price}</p>
      {/* ... outros campos */}
    </div>
  );
}
```

---

## ⚠️ Tratamento de Erros

### Códigos de Fechamento

- **1008**: Token inválido ou erro de autenticação
- **1011**: Erro interno do servidor (ex: Redis indisponível)

### Reconexão Automática

Recomenda-se implementar reconexão automática:

```javascript
function connectWithRetry(token, maxRetries = 5) {
  let retries = 0;

  function connect() {
    const ws = new WebSocket(`ws://localhost:8000/ws/orders?token=${token}`);

    ws.onopen = () => {
      retries = 0; // Reset contador
      console.log('✅ Conectado');
    };

    ws.onclose = (event) => {
      if (retries < maxRetries) {
        retries++;
        const delay = Math.min(1000 * Math.pow(2, retries), 30000); // Backoff exponencial
        console.log(`Tentando reconectar em ${delay}ms... (tentativa ${retries}/${maxRetries})`);
        setTimeout(connect, delay);
      } else {
        console.error('❌ Máximo de tentativas de reconexão atingido');
      }
    };

    return ws;
  }

  return connect();
}
```

---

## 📊 Status do Serviço

Você pode verificar o status do serviço via HTTP:

```javascript
async function checkStatus() {
  const response = await fetch('http://localhost:8000/ws/orders/status');
  const status = await response.json();
  
  console.log('Status:', status);
  // {
  //   "status": "running",
  //   "redis": "connected",
  //   "active_orders": [123, 456],
  //   "total_connections": 2,
  //   "orders_count": 2,
  //   "order_ref_counts": {"123": 2, "456": 1},
  //   "listener_running": true
  // }
}
```

---

## 🔐 Segurança

- **Token JWT obrigatório**: Sem token válido, a conexão será rejeitada
- **Validação de acesso**: O Gateway valida se o usuário tem acesso à ordem antes de assinar
- **Limite de assinaturas**: Máximo de 100 assinaturas por cliente WebSocket

---

## 📝 Notas Importantes

1. **Token JWT**: O token deve ser válido e não expirado
2. **Reconexão**: Implemente reconexão automática para melhor experiência do usuário
3. **Limpeza**: Sempre cancele assinaturas antes de fechar a conexão
4. **Múltiplas conexões**: Você pode ter múltiplas conexões WebSocket, cada uma com suas próprias assinaturas
5. **Atualizações em tempo real**: As atualizações são enviadas automaticamente quando a ordem muda no Trade Service

---

## 🎯 Fluxo Completo

1. **Frontend conecta** ao WebSocket com token JWT
2. **Frontend assina** ordens específicas enviando mensagens `subscribe`
3. **Gateway valida** acesso às ordens via Trade Service
4. **Gateway assina** canais Redis `ORDER_UPDATE:{order_id}`
5. **Trade Service publica** atualizações no Redis quando ordens mudam
6. **Gateway recebe** do Redis e repassa para o frontend via WebSocket
7. **Frontend atualiza** a UI com os dados recebidos

---

## 🐛 Debugging

Para debugar problemas:

1. Verifique o console do navegador para erros
2. Verifique se o token JWT é válido
3. Verifique o status do serviço: `GET /ws/orders/status`
4. Verifique os logs do Gateway para erros
5. Teste a conexão WebSocket manualmente usando ferramentas como Postman ou WebSocket King

---

## 📚 Exemplo Completo (TypeScript)

```typescript
// orderWebSocket.ts
export class OrderWebSocketManager {
  private ws: WebSocket | null = null;
  private token: string;
  private subscribers: Map<number, (order: Order) => void> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(token: string) {
    this.token = token;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = `ws://localhost:8000/ws/orders?token=${this.token}`;
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('✅ WebSocket conectado');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onmessage = (event) => {
        this.handleMessage(JSON.parse(event.data));
      };

      this.ws.onerror = (error) => {
        console.error('❌ Erro:', error);
        reject(error);
      };

      this.ws.onclose = (event) => {
        console.log('🔌 WebSocket fechado:', event.code, event.reason);
        this.ws = null;
        this.attemptReconnect();
      };
    });
  }

  private handleMessage(message: any) {
    switch (message.action) {
      case 'order_update':
        const callback = this.subscribers.get(message.order_id);
        if (callback) {
          callback(message.data);
        }
        break;
      case 'error':
        console.error('Erro:', message.message);
        break;
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(`Tentando reconectar em ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }

  subscribe(orderId: number, callback: (order: Order) => void) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket não está conectado');
      return;
    }

    this.subscribers.set(orderId, callback);
    this.ws.send(JSON.stringify({
      action: 'subscribe',
      type: 'order',
      order_id: orderId
    }));
  }

  unsubscribe(orderId: number) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    this.subscribers.delete(orderId);
    this.ws.send(JSON.stringify({
      action: 'unsubscribe',
      type: 'order',
      order_id: orderId
    }));
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.subscribers.clear();
  }
}

// Uso
const token = localStorage.getItem('token');
const wsManager = new OrderWebSocketManager(token!);

await wsManager.connect();

wsManager.subscribe(123, (order) => {
  console.log('Ordem atualizada:', order);
  // Atualizar UI
});
```

---

## ✅ Checklist de Implementação

- [ ] Conectar ao WebSocket com token JWT
- [ ] Implementar tratamento de erros e reconexão
- [ ] Assinar ordens após conexão estabelecida
- [ ] Processar mensagens `order_update` e atualizar UI
- [ ] Cancelar assinaturas ao desmontar componente/fechar conexão
- [ ] Implementar feedback visual para status da conexão
- [ ] Tratar erros de autenticação (token inválido/expirado)
- [ ] Testar com múltiplas ordens simultaneamente

