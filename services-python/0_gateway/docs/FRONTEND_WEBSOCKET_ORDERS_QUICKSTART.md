# ⚡ Quick Start - WebSocket de Ordens (Frontend)

## 🎯 Objetivo

Receber atualizações de ordens em tempo real via WebSocket.

## 📦 Setup Rápido

### 1. Criar Serviço (TypeScript)

```typescript
// services/orderWebSocket.ts
class OrderWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private callbacks: Map<number, (order: any) => void> = new Map();

  constructor(url: string, token: string) {
    // Token JWT é obrigatório - será enviado na primeira mensagem (não na URL)
    this.url = url;
    this.token = token;
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('✅ Conectado');
      
      // PRIMEIRA MENSAGEM: Autenticar
      this.ws.send(JSON.stringify({
        action: 'auth',
        token: this.token
      }));
    };

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      
      if (msg.action === 'authenticated') {
        console.log('✅ Autenticado com sucesso');
        // Agora pode assinar ordens
      } else if (msg.action === 'order_update') {
        const callback = this.callbacks.get(msg.order_id);
        if (callback) callback(msg.data);
      } else if (msg.action === 'error') {
        console.error('❌ Erro:', msg.message);
      }
    };

    this.ws.onerror = (error) => {
      console.error('❌ Erro:', error);
    };

    this.ws.onclose = () => {
      console.log('🔌 Desconectado');
      // Reconectar após 5s
      setTimeout(() => this.connect(), 5000);
    };
  }

  subscribe(orderId: number, callback: (order: any) => void) {
    this.callbacks.set(orderId, callback);
    
    // Aguardar autenticação antes de assinar
    // Assinar será feito automaticamente após autenticação
    if (this.ws?.readyState === WebSocket.OPEN) {
      // Verificar se já recebeu 'authenticated'
      // Por simplicidade, tentar assinar (servidor rejeitará se não autenticado)
      this.ws.send(JSON.stringify({
        action: 'subscribe',
        type: 'order',
        order_id: orderId
      }));
    }
  }

  unsubscribe(orderId: number) {
    this.callbacks.delete(orderId);
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'unsubscribe',
        type: 'order',
        order_id: orderId
      }));
    }
  }

  disconnect() {
    this.ws?.close();
    this.callbacks.clear();
  }
}

export default OrderWebSocket;
```

### 2. Usar no Componente React

```typescript
// components/OrderCard.tsx
import { useEffect, useState } from 'react';
import OrderWebSocket from '../services/orderWebSocket';

function OrderCard({ orderId }: { orderId: number }) {
  const [order, setOrder] = useState<any>(null);
  const wsRef = useRef<OrderWebSocket | null>(null);

  useEffect(() => {
    // Token é obrigatório
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('Token não encontrado');
      return;
    }
    
    const ws = new OrderWebSocket('ws://localhost:8000/ws/orders', token);
    wsRef.current = ws;
    
    ws.connect();
    ws.subscribe(orderId, (updatedOrder) => {
      setOrder(updatedOrder);
    });

    return () => {
      ws.unsubscribe(orderId);
      ws.disconnect();
    };
  }, [orderId]);

  if (!order) return <div>Carregando...</div>;

  return (
    <div>
      <h3>Ordem #{order.id}</h3>
      <p>Status: {order.status}</p>
      <p>Preço: R$ {order.price}</p>
    </div>
  );
}
```

## 🔥 Exemplo JavaScript Puro (Sem React)

```javascript
// Token é obrigatório - será enviado na primeira mensagem (não na URL)
const token = localStorage.getItem('token');
if (!token) {
  console.error('Token não encontrado');
  return;
}

// Conectar (sem token na URL)
const ws = new WebSocket('ws://localhost:8000/ws/orders');

// PRIMEIRA MENSAGEM: Autenticar
ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'auth',
    token: token
  }));
};

// Assinar ordem 123
ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    type: 'order',
    order_id: 123
  }));
};

// Receber mensagens
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.action === 'authenticated') {
    console.log('✅ Autenticado com sucesso');
    // Agora pode assinar ordens
    ws.send(JSON.stringify({
      action: 'subscribe',
      type: 'order',
      order_id: 123
    }));
  } else if (msg.action === 'order_update') {
    console.log('Ordem atualizada:', msg.data);
    // Atualizar UI aqui
    updateOrderUI(msg.data);
  } else if (msg.action === 'error') {
    console.error('❌ Erro:', msg.message);
  }
};

// Função para atualizar UI
function updateOrderUI(order) {
  document.getElementById('order-status').textContent = order.status;
  document.getElementById('order-price').textContent = `R$ ${order.price}`;
}
```

## 📋 Checklist Mínimo

- [ ] Criar instância WebSocket
- [ ] Conectar ao `ws://localhost:8000/ws/orders`
- [ ] Enviar mensagem `subscribe` com `order_id`
- [ ] Escutar mensagens `order_update`
- [ ] Atualizar UI quando receber atualização
- [ ] Fazer cleanup ao desmontar componente

## 🎨 Exemplo Visual Completo

```typescript
import { useEffect, useState } from 'react';

function OrderTracker({ orderId }: { orderId: number }) {
  const [order, setOrder] = useState<any>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Token é obrigatório - será enviado na primeira mensagem
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('Token não encontrado');
      return;
    }
    
    const ws = new WebSocket('ws://localhost:8000/ws/orders');
    
    // PRIMEIRA MENSAGEM: Autenticar
    ws.onopen = () => {
      ws.send(JSON.stringify({
        action: 'auth',
        token: token
      }));
    };

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({
        action: 'subscribe',
        type: 'order',
        order_id: orderId
      }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      
      if (msg.action === 'authenticated') {
        console.log('✅ Autenticado');
        // Agora pode assinar ordens
        ws.send(JSON.stringify({
          action: 'subscribe',
          type: 'order',
          order_id: orderId
        }));
      } else if (msg.action === 'order_update') {
        setOrder(msg.data);
      } else if (msg.action === 'error') {
        console.error('❌ Erro:', msg.message);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      // Reconectar
      setTimeout(() => {
        const newWs = new WebSocket('ws://localhost:8000/ws/orders');
        // ... repetir setup
      }, 5000);
    };

    return () => ws.close();
  }, [orderId]);

  return (
    <div>
      <div className="status">
        {connected ? '🟢 Conectado' : '🔴 Desconectado'}
      </div>
      
      {order && (
        <div className="order-info">
          <h2>Ordem #{order.id}</h2>
          <p><strong>Status:</strong> {order.status}</p>
          <p><strong>Preço:</strong> R$ {order.price}</p>
          <p><strong>Atualizado:</strong> {new Date(order.updated_at).toLocaleString()}</p>
        </div>
      )}
    </div>
  );
}
```

## 🚨 Erros Comuns

### Erro: "WebSocket is closed"
```typescript
// ✅ Verificar estado antes de enviar
if (ws.readyState === WebSocket.OPEN) {
  ws.send(JSON.stringify({...}));
}
```

### Erro: "Cannot read property 'data'"
```typescript
// ✅ Verificar tipo de mensagem
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.action === 'order_update') {
    // Processar
  }
};
```

### Não recebe atualizações
```typescript
// ✅ Verificar se assinou corretamente
ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',  // ✅ Correto
    type: 'order',
    order_id: 123
  }));
};
```

## 📞 Suporte

Para documentação completa, veja: `FRONTEND_WEBSOCKET_ORDERS_INTEGRATION.md`

