# 📱 Integração Frontend - WebSocket de Atualizações de Ordens

## 📋 Visão Geral

O Gateway fornece um endpoint WebSocket para receber atualizações de ordens em tempo real. Quando uma ordem é criada, atualizada ou executada no Trade Service, o frontend recebe automaticamente essas atualizações via WebSocket.

## 🔌 Endpoint WebSocket

**URL:** `ws://localhost:8000/ws/orders` (ou a URL do seu ambiente)

**Autenticação:** **OBRIGATÓRIA** - Token JWT do Keycloak deve ser enviado na **primeira mensagem** após conexão (não na URL por segurança)

## 📡 Protocolo de Comunicação

### Mensagens do Frontend → Gateway

#### 0. Autenticar (PRIMEIRA MENSAGEM OBRIGATÓRIA)

```json
{
  "action": "auth",
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Resposta de sucesso:**
```json
{
  "action": "authenticated",
  "status": "success",
  "user_id": "user-uuid"
}
```

**Resposta de erro:**
```json
{
  "action": "error",
  "message": "Invalid token"
}
```
(Conexão será fechada após erro de autenticação)

#### 1. Assinar uma ordem

```json
{
  "action": "subscribe",
  "type": "order",
  "order_id": 123
}
```

#### 2. Assinar múltiplas ordens

```json
{
  "action": "subscribe",
  "type": "orders",
  "order_ids": [123, 456, 789]
}
```

#### 3. Cancelar assinatura de uma ordem

```json
{
  "action": "unsubscribe",
  "type": "order",
  "order_id": 123
}
```

#### 4. Cancelar assinatura de múltiplas ordens

```json
{
  "action": "unsubscribe",
  "type": "orders",
  "order_ids": [123, 456]
}
```

### Mensagens do Gateway → Frontend

#### 1. Confirmação de Assinatura

```json
{
  "action": "subscribed",
  "type": "order",
  "order_id": 123,
  "status": "success"
}
```

#### 2. Atualização de Ordem

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

#### 3. Erro

```json
{
  "action": "error",
  "type": "order",
  "order_id": 123,
  "message": "Order not found or access denied"
}
```

#### 4. Ping (Heartbeat)

```json
{
  "action": "ping",
  "type": "heartbeat"
}
```

## 💻 Implementação TypeScript/JavaScript

### 1. Serviço WebSocket (Recomendado)

Crie um arquivo `services/orderWebSocketService.ts`:

```typescript
type OrderUpdateCallback = (order: any) => void;
type ConnectionStatusCallback = (connected: boolean) => void;

class OrderWebSocketService {
  private ws: WebSocket | null = null;
  private wsUrl: string;
  private token: string | null = null;
  private reconnectInterval: number = 5000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private subscriptions: Set<number> = new Set();
  private listeners: Map<number, OrderUpdateCallback[]> = new Map();
  private connectionStatusListeners: ConnectionStatusCallback[] = [];
  private isConnected: boolean = false;

  constructor(wsUrl: string, token: string) {
    // Token JWT é obrigatório - será enviado na primeira mensagem (não na URL)
    this.wsUrl = wsUrl;
    this.token = token;
  }

  /**
   * Conecta ao WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const url = this.token 
          ? `${this.wsUrl}?token=${this.token}` 
          : this.wsUrl;
        
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log('✅ WebSocket de ordens conectado');
          
          // PRIMEIRA MENSAGEM: Autenticar
          if (this.token) {
            this.ws.send(JSON.stringify({
              action: 'auth',
              token: this.token
            }));
          } else {
            console.error('❌ Token não fornecido');
            this.ws.close();
            reject(new Error('Token não fornecido'));
            return;
          }
          
          // Aguardar autenticação antes de marcar como conectado
          // O status será atualizado quando receber 'authenticated'
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Erro ao processar mensagem WebSocket:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('❌ Erro no WebSocket:', error);
          this.isConnected = false;
          this.notifyConnectionStatus(false);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('🔌 WebSocket de ordens desconectado');
          this.isConnected = false;
          this.notifyConnectionStatus(false);
          this.scheduleReconnect();
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Agenda reconexão automática
   */
  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      console.log('🔄 Tentando reconectar WebSocket...');
      this.connect().catch(console.error);
    }, this.reconnectInterval);
  }

  /**
   * Limpa timer de reconexão
   */
  private clearReconnectTimer() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Processa mensagens recebidas do Gateway
   */
  private handleMessage(message: any) {
    switch (message.action) {
      case 'authenticated':
        console.log('✅ Autenticado com sucesso');
        this.isConnected = true;
        this.clearReconnectTimer();
        this.notifyConnectionStatus(true);
        
        // Re-assina todas as ordens após reconexão
        this.subscriptions.forEach(orderId => {
          this.subscribe(orderId);
        });
        break;
      
      case 'order_update':
        this.notifyListeners(message.order_id, message.data);
        break;
      
      case 'subscribed':
        console.log(`✅ Assinado na ordem ${message.order_id}`);
        break;
      
      case 'unsubscribed':
        console.log(`❌ Desassinado da ordem ${message.order_id}`);
        break;
      
      case 'error':
        console.error(`❌ Erro WebSocket: ${message.message}`);
        // Se erro de autenticação, fechar conexão
        if (message.message.includes('token') || message.message.includes('auth')) {
          this.isConnected = false;
          this.notifyConnectionStatus(false);
        }
        break;
      
      case 'ping':
        // Responder ao ping (opcional)
        // this.send({ action: 'pong', type: 'heartbeat' });
        break;
      
      default:
        console.warn('Ação desconhecida:', message.action);
    }
  }

  /**
   * Assina atualizações de uma ordem
   */
  subscribe(orderId: number): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN || !this.isConnected) {
      console.warn('⚠️ WebSocket não conectado ou não autenticado, será assinado após conexão');
      this.subscriptions.add(orderId);
      
      // Tentar conectar se não estiver conectado
      if (!this.isConnected) {
        this.connect().catch(console.error);
      }
      return;
    }

    this.subscriptions.add(orderId);
    this.ws.send(JSON.stringify({
      action: 'subscribe',
      type: 'order',
      order_id: orderId
    }));
  }

  /**
   * Assina múltiplas ordens de uma vez
   */
  subscribeMultiple(orderIds: number[]): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('⚠️ WebSocket não conectado, será assinado após conexão');
      orderIds.forEach(id => this.subscriptions.add(id));
      
      if (!this.isConnected) {
        this.connect().catch(console.error);
      }
      return;
    }

    orderIds.forEach(id => this.subscriptions.add(id));
    this.ws.send(JSON.stringify({
      action: 'subscribe',
      type: 'orders',
      order_ids: orderIds
    }));
  }

  /**
   * Cancela assinatura de uma ordem
   */
  unsubscribe(orderId: number): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.subscriptions.delete(orderId);
      return;
    }

    this.subscriptions.delete(orderId);
    this.ws.send(JSON.stringify({
      action: 'unsubscribe',
      type: 'order',
      order_id: orderId
    }));
  }

  /**
   * Cancela assinatura de múltiplas ordens
   */
  unsubscribeMultiple(orderIds: number[]): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      orderIds.forEach(id => this.subscriptions.delete(id));
      return;
    }

    orderIds.forEach(id => this.subscriptions.delete(id));
    this.ws.send(JSON.stringify({
      action: 'unsubscribe',
      type: 'orders',
      order_ids: orderIds
    }));
  }

  /**
   * Registra callback para atualizações de uma ordem específica
   */
  onOrderUpdate(orderId: number, callback: OrderUpdateCallback): () => void {
    if (!this.listeners.has(orderId)) {
      this.listeners.set(orderId, []);
    }
    this.listeners.get(orderId)!.push(callback);

    // Retorna função para remover listener
    return () => {
      const callbacks = this.listeners.get(orderId);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  /**
   * Registra callback para mudanças no status de conexão
   */
  onConnectionStatusChange(callback: ConnectionStatusCallback): () => void {
    this.connectionStatusListeners.push(callback);
    
    return () => {
      const index = this.connectionStatusListeners.indexOf(callback);
      if (index > -1) {
        this.connectionStatusListeners.splice(index, 1);
      }
    };
  }

  /**
   * Notifica listeners de uma ordem
   */
  private notifyListeners(orderId: number, orderData: any) {
    const callbacks = this.listeners.get(orderId);
    if (callbacks) {
      callbacks.forEach(callback => callback(orderData));
    }
  }

  /**
   * Notifica listeners de status de conexão
   */
  private notifyConnectionStatus(connected: boolean) {
    this.connectionStatusListeners.forEach(callback => callback(connected));
  }

  /**
   * Desconecta do WebSocket
   */
  disconnect(): void {
    this.clearReconnectTimer();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnected = false;
    this.subscriptions.clear();
    this.listeners.clear();
    this.connectionStatusListeners = [];
  }

  /**
   * Verifica se está conectado
   */
  get connected(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }
}

export default OrderWebSocketService;
```

### 2. Hook React (Recomendado)

Crie um arquivo `hooks/useOrderUpdates.ts`:

```typescript
import { useEffect, useState, useRef, useCallback } from 'react';
import OrderWebSocketService from '../services/orderWebSocketService';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/orders';

/**
 * Hook para receber atualizações de uma ordem específica
 */
export function useOrderUpdates(orderId: number | null) {
  const [order, setOrder] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsServiceRef = useRef<OrderWebSocketService | null>(null);

  useEffect(() => {
    if (!orderId) {
      return;
    }

    // Token é obrigatório
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('Token não encontrado - não é possível conectar ao WebSocket');
      return;
    }
    
    const wsService = new OrderWebSocketService(WS_URL, token);
    wsServiceRef.current = wsService;

    // Conecta ao WebSocket
    wsService.connect()
      .then(() => {
        setIsConnected(true);
        
        // Assina a ordem
        wsService.subscribe(orderId);
        
        // Escuta atualizações
        const unsubscribe = wsService.onOrderUpdate(orderId, (updatedOrder) => {
          setOrder(updatedOrder);
        });

        // Escuta mudanças no status de conexão
        wsService.onConnectionStatusChange((connected) => {
          setIsConnected(connected);
        });

        // Cleanup
        return () => {
          unsubscribe();
          wsService.unsubscribe(orderId);
        };
      })
      .catch((error) => {
        console.error('❌ Falha ao conectar WebSocket:', error);
        setIsConnected(false);
      });

    // Cleanup ao desmontar
    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.unsubscribe(orderId);
        wsServiceRef.current.disconnect();
      }
    };
  }, [orderId]);

  return { order, isConnected };
}

/**
 * Hook para receber atualizações de múltiplas ordens
 */
export function useMultipleOrderUpdates(orderIds: number[]) {
  const [orders, setOrders] = useState<Map<number, any>>(new Map());
  const [isConnected, setIsConnected] = useState(false);
  const wsServiceRef = useRef<OrderWebSocketService | null>(null);

  useEffect(() => {
    if (!orderIds || orderIds.length === 0) {
      return;
    }

    const token = localStorage.getItem('token');
    const wsService = new OrderWebSocketService(WS_URL, token || undefined);
    wsServiceRef.current = wsService;

    wsService.connect()
      .then(() => {
        setIsConnected(true);
        
        // Assina todas as ordens
        wsService.subscribeMultiple(orderIds);
        
        // Escuta atualizações de cada ordem
        const unsubscribes = orderIds.map(orderId => {
          return wsService.onOrderUpdate(orderId, (updatedOrder) => {
            setOrders(prev => {
              const newMap = new Map(prev);
              newMap.set(orderId, updatedOrder);
              return newMap;
            });
          });
        });

        // Escuta mudanças no status de conexão
        wsService.onConnectionStatusChange((connected) => {
          setIsConnected(connected);
        });

        // Cleanup
        return () => {
          unsubscribes.forEach(unsub => unsub());
          wsService.unsubscribeMultiple(orderIds);
        };
      })
      .catch((error) => {
        console.error('❌ Falha ao conectar WebSocket:', error);
        setIsConnected(false);
      });

    // Cleanup ao desmontar
    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.unsubscribeMultiple(orderIds);
        wsServiceRef.current.disconnect();
      }
    };
  }, [orderIds.join(',')]); // Re-executa quando orderIds mudar

  return { orders, isConnected };
}
```

### 3. Exemplo de Uso em Componente React

```typescript
import React from 'react';
import { useOrderUpdates } from '../hooks/useOrderUpdates';

interface OrderDetailProps {
  orderId: number;
}

function OrderDetail({ orderId }: OrderDetailProps) {
  const { order, isConnected } = useOrderUpdates(orderId);

  if (!order) {
    return (
      <div>
        <div>Carregando ordem...</div>
        <div>Status conexão: {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}</div>
      </div>
    );
  }

  return (
    <div>
      <div>
        <h2>Ordem #{order.id}</h2>
        <div>Status conexão: {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}</div>
      </div>
      
      <div>
        <h3>Informações da Ordem</h3>
        <p>Status: <strong>{order.status}</strong></p>
        <p>Preço: R$ {order.price}</p>
        <p>Stop Loss: R$ {order.stop_loss}</p>
        <p>Take Profit: R$ {order.take_profit}</p>
        <p>Atualizado em: {new Date(order.updated_at).toLocaleString()}</p>
      </div>

      <div>
        <h3>Ofertas</h3>
        {order.offers?.map((offer: any, index: number) => (
          <div key={index}>
            <p>Símbolo: {offer.symbol}</p>
            <p>Operação: {offer.operation}</p>
            <p>Quantidade: {offer.qtty}</p>
            <p>Preenchido: {offer.filled}</p>
            <p>Status: {offer.status}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default OrderDetail;
```

### 4. Exemplo de Uso com Múltiplas Ordens

```typescript
import React from 'react';
import { useMultipleOrderUpdates } from '../hooks/useOrderUpdates';

function OrderList({ orderIds }: { orderIds: number[] }) {
  const { orders, isConnected } = useMultipleOrderUpdates(orderIds);

  return (
    <div>
      <div>Status conexão: {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}</div>
      
      <h2>Ordens em Execução</h2>
      {orderIds.map(orderId => {
        const order = orders.get(orderId);
        return (
          <div key={orderId}>
            <h3>Ordem #{orderId}</h3>
            {order ? (
              <>
                <p>Status: {order.status}</p>
                <p>Preço: R$ {order.price}</p>
                <p>Atualizado: {new Date(order.updated_at).toLocaleString()}</p>
              </>
            ) : (
              <p>Carregando...</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
```

## 🎯 Boas Práticas

### 1. Gerenciamento de Conexão

- **Conectar uma vez**: Use um singleton ou contexto React para manter uma única conexão WebSocket
- **Reconexão automática**: O serviço já implementa reconexão automática
- **Cleanup**: Sempre cancele assinaturas ao desmontar componentes

### 2. Performance

- **Assinar apenas ordens visíveis**: Não assine todas as ordens de uma vez
- **Cancelar assinaturas**: Quando o usuário sair da página de detalhes, cancele a assinatura
- **Debounce de atualizações**: Se necessário, use debounce para atualizações muito frequentes

### 3. Tratamento de Erros

```typescript
// Sempre trate erros de conexão
wsService.connect()
  .then(() => {
    // Sucesso
  })
  .catch((error) => {
    console.error('Erro ao conectar:', error);
    // Mostrar mensagem ao usuário
    // Tentar reconectar após delay
  });
```

### 4. Indicadores Visuais

```typescript
// Mostrar status de conexão ao usuário
{isConnected ? (
  <span className="status-connected">🟢 Conectado</span>
) : (
  <span className="status-disconnected">🔴 Desconectado</span>
)}
```

## 🔐 Autenticação

**O token JWT é obrigatório** e deve ser enviado na **primeira mensagem** após a conexão WebSocket (não na URL por segurança):

```typescript
const token = localStorage.getItem('token');
if (!token) {
  console.error('Token não encontrado');
  return;
}

const wsService = new OrderWebSocketService(WS_URL, token);
// O serviço automaticamente envia o token na primeira mensagem
```

**Por que não na URL?**
- URLs aparecem em logs de servidor
- URLs ficam no histórico do navegador
- URLs podem ser compartilhadas acidentalmente
- URLs aparecem em referrers

O token será validado pelo Gateway usando Keycloak JWT. Se o token for inválido ou expirado, a conexão será fechada com código 1008 (Invalid token).

## 📊 Estados da Ordem

Os principais estados que você receberá:

- `PENDING` - Ordem pendente
- `SUBMITTED` - Ordem enviada
- `FILLED` - Ordem executada
- `PARTIALLY_FILLED` - Ordem parcialmente executada
- `CANCELLED` - Ordem cancelada
- `REJECTED` - Ordem rejeitada

## 🐛 Debugging

### Habilitar logs detalhados

```typescript
// No serviço, adicione mais logs
console.log('📤 Enviando:', message);
console.log('📥 Recebido:', data);
```

### Verificar conexão

```typescript
console.log('WebSocket state:', wsService.connected);
console.log('Assinaturas ativas:', Array.from(wsService.subscriptions));
```

## 📝 Checklist de Implementação

- [ ] Criar `OrderWebSocketService`
- [ ] Criar hooks React (`useOrderUpdates`, `useMultipleOrderUpdates`)
- [ ] Integrar em componentes que mostram ordens
- [ ] Adicionar indicadores de status de conexão
- [ ] Implementar tratamento de erros
- [ ] Testar reconexão automática
- [ ] Testar com múltiplas ordens
- [ ] Adicionar cleanup adequado
- [ ] Testar em produção

## 🚀 Exemplo Completo Mínimo

```typescript
// 1. Instalar dependências (se necessário)
// npm install --save-dev @types/websocket

// 2. Criar serviço básico
import OrderWebSocketService from './services/orderWebSocketService';

const wsService = new OrderWebSocketService('ws://localhost:8000/ws/orders');

// 3. Conectar e assinar
wsService.connect().then(() => {
  wsService.subscribe(123);
  
  wsService.onOrderUpdate(123, (order) => {
    console.log('Ordem atualizada:', order);
    // Atualizar UI aqui
  });
});

// 4. Cleanup quando necessário
// wsService.unsubscribe(123);
// wsService.disconnect();
```

## 📚 Referências

- [WebSocket API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [React Hooks](https://react.dev/reference/react)
- Documentação do Gateway: `GATEWAY-README.md`

