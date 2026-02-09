# Prompt: Implementar Consumo de Streaming de Cotações no Frontend

## 📋 Objetivo

Implementar no frontend a conexão com o endpoint WebSocket do Gateway Service para receber cotações de ativos em tempo real, processar os dados no formato JSON Array Rows e atualizar a interface do usuário.

## 🔗 Endpoint WebSocket

**URL Base**: `ws://localhost:8000` (ou URL do ambiente)

**Endpoint**: `/ws/quotes`

**Exemplo completo**: `ws://localhost:8000/ws/quotes?symbols=PETR4,VALE3,ITUB4`

## 📡 Formato das Mensagens

### 1. Mensagem de Conexão (Recebida ao conectar)

```json
{
  "type": "connected",
  "symbols": ["PETR4", "VALE3", "ITUB4"],
  "message": "Conectado ao stream de cotações"
}
```

### 2. Header (Enviado uma vez por símbolo ao conectar)

```json
{
  "type": "header",
  "symbol": "PETR4",
  "data": [
    "symbol",
    "preco_compra",
    "qtde_compra",
    "preco_venda",
    "qtde_venda",
    "preco_ultimo",
    "mudanca_diaria",
    "oscilacao_diaria",
    "ultimo_horario",
    "timestamp"
  ]
}
```

**Importante**: O header define a ordem dos campos nas mensagens de cotação. Armazene o header por símbolo para processar as mensagens corretamente.

### 3. Cotações (Enviadas continuamente)

```json
{
  "type": "quote",
  "symbol": "PETR4",
  "data": {
    "symbol": "PETR4",
    "preco_compra": 38.1,
    "qtde_compra": -1,
    "preco_venda": 38.14,
    "qtde_venda": -1,
    "preco_ultimo": 38.12,
    "mudanca_diaria": 1.5,
    "oscilacao_diaria": 0.38,
    "ultimo_horario": null,
    "timestamp": 1763606647
  }
}
```

**Campos do objeto `data`**:
- `symbol` (string): Símbolo do ativo (ex: "PETR4")
- `preco_compra` (number): Preço de compra (bid)
- `qtde_compra` (number): Quantidade de compra (-1 se não disponível)
- `preco_venda` (number): Preço de venda (ask)
- `qtde_venda` (number): Quantidade de venda (-1 se não disponível)
- `preco_ultimo` (number): Último preço negociado
- `mudanca_diaria` (number): Mudança percentual diária
- `oscilacao_diaria` (number): Oscilação diária em valor
- `ultimo_horario` (string | null): Horário do último negócio
- `timestamp` (number): Timestamp Unix

### 4. Ping (Mantém conexão viva)

```json
{
  "type": "ping"
}
```

O servidor envia ping a cada 30 segundos se não houver atividade. Responda com `pong` para manter a conexão.

## 💻 Implementação em JavaScript/TypeScript

### Exemplo Básico (JavaScript)

```javascript
class QuoteStreamService {
  constructor(apiUrl = 'ws://localhost:8000') {
    this.apiUrl = apiUrl;
    this.ws = null;
    this.symbols = [];
    this.headers = {}; // Armazenar headers por símbolo
    this.onQuoteCallback = null;
    this.onErrorCallback = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000; // 3 segundos
  }

  connect(symbols) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.warn('Já conectado. Use subscribe() para adicionar símbolos.');
      return;
    }

    this.symbols = Array.isArray(symbols) ? symbols : symbols.split(',').map(s => s.trim());
    const symbolsParam = this.symbols.join(',');
    const wsUrl = `${this.apiUrl}/ws/quotes?symbols=${encodeURIComponent(symbolsParam)}`;

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Erro ao criar WebSocket:', error);
      if (this.onErrorCallback) {
        this.onErrorCallback(error);
      }
    }
  }

  setupEventHandlers() {
    this.ws.onopen = () => {
      console.log('✅ Conectado ao stream de cotações');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Erro ao processar mensagem:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('Erro no WebSocket:', error);
      if (this.onErrorCallback) {
        this.onErrorCallback(error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('Conexão fechada:', event.code, event.reason);
      this.attemptReconnect();
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'connected':
        console.log('Conectado. Símbolos:', message.symbols);
        break;

      case 'header':
        // Armazenar header para processar cotações
        this.headers[message.symbol] = message.data;
        console.log(`Header recebido para ${message.symbol}:`, message.data);
        break;

      case 'quote':
        // Processar cotação e chamar callback
        if (this.onQuoteCallback) {
          this.onQuoteCallback(message.symbol, message.data);
        }
        break;

      case 'ping':
        // Responder ao ping para manter conexão viva
        this.send({ type: 'pong' });
        break;

      default:
        console.warn('Tipo de mensagem desconhecido:', message.type);
    }
  }

  subscribe(symbols) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket não está conectado');
      return;
    }

    const symbolsList = Array.isArray(symbols) ? symbols : symbols.split(',').map(s => s.trim());
    this.send({
      type: 'subscribe',
      symbols: symbolsList
    });
  }

  unsubscribe(symbols) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket não está conectado');
      return;
    }

    const symbolsList = Array.isArray(symbols) ? symbols : symbols.split(',').map(s => s.trim());
    this.send({
      type: 'unsubscribe',
      symbols: symbolsList
    });
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket não está aberto');
    }
  }

  onQuote(callback) {
    this.onQuoteCallback = callback;
  }

  onError(callback) {
    this.onErrorCallback = callback;
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Tentando reconectar (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect(this.symbols);
      }, this.reconnectDelay);
    } else {
      console.error('Máximo de tentativas de reconexão atingido');
      if (this.onErrorCallback) {
        this.onErrorCallback(new Error('Falha ao reconectar após múltiplas tentativas'));
      }
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.headers = {};
    }
  }
}

// Uso básico
const quoteStream = new QuoteStreamService('ws://localhost:8000');

quoteStream.onQuote((symbol, quoteData) => {
  console.log(`Cotação ${symbol}:`, quoteData);
  // Atualizar UI aqui
  updateQuoteInUI(symbol, quoteData);
});

quoteStream.onError((error) => {
  console.error('Erro no stream:', error);
  // Exibir notificação de erro ao usuário
});

// Conectar com símbolos iniciais
quoteStream.connect(['PETR4', 'VALE3', 'ITUB4']);

// Adicionar mais símbolos depois
setTimeout(() => {
  quoteStream.subscribe(['BBDC4', 'ABEV3']);
}, 5000);

// Remover símbolos
setTimeout(() => {
  quoteStream.unsubscribe(['ITUB4']);
}, 10000);
```

### Exemplo React Hook

```typescript
import { useEffect, useState, useRef, useCallback } from 'react';

interface QuoteData {
  symbol: string;
  preco_compra: number;
  qtde_compra: number;
  preco_venda: number;
  qtde_venda: number;
  preco_ultimo: number;
  mudanca_diaria: number;
  oscilacao_diaria: number;
  ultimo_horario: string | null;
  timestamp: number;
}

interface UseQuoteStreamOptions {
  symbols: string[];
  apiUrl?: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
}

export function useQuoteStream(options: UseQuoteStreamOptions) {
  const { symbols, apiUrl = 'ws://localhost:8000', autoReconnect = true, maxReconnectAttempts = 5 } = options;
  
  const [quotes, setQuotes] = useState<Record<string, QuoteData>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const symbolsParam = symbols.join(',');
    const wsUrl = `${apiUrl}/ws/quotes?symbols=${encodeURIComponent(symbolsParam)}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ Conectado ao stream de cotações');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          switch (message.type) {
            case 'connected':
              console.log('Conectado. Símbolos:', message.symbols);
              break;

            case 'quote':
              setQuotes((prev) => ({
                ...prev,
                [message.symbol]: message.data,
              }));
              break;

            case 'ping':
              ws.send(JSON.stringify({ type: 'pong' }));
              break;

            default:
              // Ignorar headers e outros tipos
              break;
          }
        } catch (err) {
          console.error('Erro ao processar mensagem:', err);
        }
      };

      ws.onerror = (err) => {
        console.error('Erro no WebSocket:', err);
        setError(new Error('Erro na conexão WebSocket'));
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        console.log('Conexão fechada:', event.code, event.reason);

        if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Tentando reconectar (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
            connect();
          }, 3000);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError(new Error('Falha ao reconectar após múltiplas tentativas'));
        }
      };
    } catch (err) {
      console.error('Erro ao criar WebSocket:', err);
      setError(err as Error);
    }
  }, [symbols, apiUrl, autoReconnect, maxReconnectAttempts]);

  const subscribe = useCallback((newSymbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        symbols: newSymbols,
      }));
    }
  }, []);

  const unsubscribe = useCallback((symbolsToRemove: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        symbols: symbolsToRemove,
      }));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    quotes,
    isConnected,
    error,
    subscribe,
    unsubscribe,
    reconnect: connect,
    disconnect,
  };
}

// Uso no componente
function QuoteDisplay({ symbols }: { symbols: string[] }) {
  const { quotes, isConnected, error } = useQuoteStream({ symbols });

  if (error) {
    return <div>Erro: {error.message}</div>;
  }

  if (!isConnected) {
    return <div>Conectando...</div>;
  }

  return (
    <div>
      {symbols.map((symbol) => {
        const quote = quotes[symbol];
        if (!quote) {
          return <div key={symbol}>{symbol}: Aguardando cotação...</div>;
        }

        return (
          <div key={symbol}>
            <h3>{quote.symbol}</h3>
            <p>Último: R$ {quote.preco_ultimo.toFixed(2)}</p>
            <p>Compra: R$ {quote.preco_compra.toFixed(2)}</p>
            <p>Venda: R$ {quote.preco_venda.toFixed(2)}</p>
            <p>
              Variação: {quote.mudanca_diaria > 0 ? '+' : ''}
              {quote.mudanca_diaria.toFixed(2)}% ({quote.oscilacao_diaria.toFixed(2)})
            </p>
            <span
              style={{
                color: quote.mudanca_diaria >= 0 ? 'green' : 'red',
              }}
            >
              {quote.mudanca_diaria >= 0 ? '▲' : '▼'}
            </span>
          </div>
        );
      })}
    </div>
  );
}
```

### Exemplo Vue.js Composable

```typescript
// composables/useQuoteStream.ts
import { ref, onMounted, onUnmounted } from 'vue';

interface QuoteData {
  symbol: string;
  preco_compra: number;
  qtde_compra: number;
  preco_venda: number;
  qtde_venda: number;
  preco_ultimo: number;
  mudanca_diaria: number;
  oscilacao_diaria: number;
  ultimo_horario: string | null;
  timestamp: number;
}

export function useQuoteStream(symbols: string[], apiUrl = 'ws://localhost:8000') {
  const quotes = ref<Record<string, QuoteData>>({});
  const isConnected = ref(false);
  const error = ref<Error | null>(null);
  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

  const connect = () => {
    if (ws?.readyState === WebSocket.OPEN) {
      return;
    }

    const symbolsParam = symbols.join(',');
    const wsUrl = `${apiUrl}/ws/quotes?symbols=${encodeURIComponent(symbolsParam)}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('✅ Conectado ao stream de cotações');
      isConnected.value = true;
      error.value = null;
      reconnectAttempts = 0;
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'quote') {
          quotes.value[message.symbol] = message.data;
        } else if (message.type === 'ping') {
          ws?.send(JSON.stringify({ type: 'pong' }));
        }
      } catch (err) {
        console.error('Erro ao processar mensagem:', err);
      }
    };

    ws.onerror = () => {
      error.value = new Error('Erro na conexão WebSocket');
    };

    ws.onclose = () => {
      isConnected.value = false;
      
      if (reconnectAttempts < 5) {
        reconnectAttempts++;
        reconnectTimeout = setTimeout(() => {
          connect();
        }, 3000);
      }
    };
  };

  const disconnect = () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
    }
    ws?.close();
    ws = null;
  };

  onMounted(() => {
    connect();
  });

  onUnmounted(() => {
    disconnect();
  });

  return {
    quotes,
    isConnected,
    error,
    connect,
    disconnect,
  };
}

// Uso no componente
<script setup lang="ts">
import { useQuoteStream } from '@/composables/useQuoteStream';

const { quotes, isConnected } = useQuoteStream(['PETR4', 'VALE3']);
</script>

<template>
  <div>
    <div v-if="!isConnected">Conectando...</div>
    <div v-else>
      <div v-for="(quote, symbol) in quotes" :key="symbol">
        <h3>{{ symbol }}</h3>
        <p>Último: R$ {{ quote.preco_ultimo.toFixed(2) }}</p>
        <p :class="{ positive: quote.mudanca_diaria >= 0, negative: quote.mudanca_diaria < 0 }">
          {{ quote.mudanca_diaria >= 0 ? '+' : '' }}{{ quote.mudanca_diaria.toFixed(2) }}%
        </p>
      </div>
    </div>
  </div>
</template>
```

## ✅ Checklist de Implementação

- [ ] Criar classe/service para gerenciar conexão WebSocket
- [ ] Implementar tratamento de mensagens (connected, header, quote, ping)
- [ ] Implementar reconexão automática em caso de desconexão
- [ ] Criar estado/estado reativo para armazenar cotações
- [ ] Implementar funções subscribe/unsubscribe
- [ ] Atualizar UI quando novas cotações chegarem
- [ ] Implementar tratamento de erros e feedback ao usuário
- [ ] Adicionar indicador visual de status da conexão (conectado/desconectado)
- [ ] Implementar cleanup ao desmontar componente/sair da página
- [ ] Testar com múltiplos símbolos simultaneamente
- [ ] Implementar debounce/throttle se necessário para atualizações frequentes

## 🎨 Boas Práticas

1. **Formatação de Valores**: Formate preços com 2 casas decimais
2. **Cores Indicativas**: Use verde para valores positivos e vermelho para negativos
3. **Loading States**: Mostre indicador de carregamento enquanto aguarda primeira cotação
4. **Error Handling**: Exiba mensagens amigáveis para o usuário em caso de erro
5. **Performance**: Use debounce/throttle se atualizar UI muitas vezes por segundo
6. **Memory Leaks**: Sempre desconecte WebSocket ao desmontar componente
7. **Reconexão**: Implemente reconexão automática com limite de tentativas
8. **Status Visual**: Mostre indicador se conexão está ativa ou não

## 🧪 Testes

### Teste Manual com Browser Console

```javascript
// No console do navegador
const ws = new WebSocket('ws://localhost:8000/ws/quotes?symbols=PETR4,VALE3');

ws.onopen = () => console.log('Conectado!');
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log('Mensagem recebida:', msg);
};
ws.onerror = (error) => console.error('Erro:', error);
ws.onclose = (event) => console.log('Fechado:', event.code, event.reason);
```

### Teste com wscat (CLI)

```bash
# Instalar wscat
npm install -g wscat

# Conectar
wscat -c "ws://localhost:8000/ws/quotes?symbols=PETR4,VALE3"

# Deve receber mensagens JSON continuamente
```

## 📝 Exemplo de Integração Completa

```typescript
// services/quoteStreamService.ts
export class QuoteStreamService {
  private ws: WebSocket | null = null;
  private quotes: Map<string, QuoteData> = new Map();
  private listeners: Set<(symbol: string, data: QuoteData) => void> = new Set();

  async connect(symbols: string[]) {
    const url = `ws://localhost:8000/ws/quotes?symbols=${symbols.join(',')}`;
    this.ws = new WebSocket(url);
    
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'quote') {
        this.quotes.set(msg.symbol, msg.data);
        this.listeners.forEach(listener => listener(msg.symbol, msg.data));
      }
    };
  }

  onQuote(callback: (symbol: string, data: QuoteData) => void) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  getQuote(symbol: string): QuoteData | undefined {
    return this.quotes.get(symbol);
  }
}

// Uso
const service = new QuoteStreamService();
service.connect(['PETR4', 'VALE3']);

const unsubscribe = service.onQuote((symbol, data) => {
  console.log(`${symbol}: R$ ${data.preco_ultimo}`);
});
```

## 🔗 Endpoint de Status

Você também pode verificar o status do serviço de streaming:

```typescript
// GET /stream/status
fetch('http://localhost:8000/stream/status')
  .then(res => res.json())
  .then(data => {
    console.log('Status:', data);
    // {
    //   "status": "running",
    //   "redis": "connected",
    //   "active_symbols": ["PETR4", "VALE3"],
    //   "total_connections": 2,
    //   "symbols_count": 2
    // }
  });
```

---

**Nota**: Ajuste a URL do WebSocket (`ws://localhost:8000`) conforme seu ambiente de desenvolvimento/produção.







