# 🔌 Detalhes da Conexão WebSocket - Streaming de Cotações

## 📡 Fluxo Completo de Conexão

### 1. Inicialização do Cliente (Frontend)

```
Cliente → WebSocket.connect('ws://localhost:8000/ws/quotes?symbols=PETR4,VALE3')
```

### 2. Backend Aceita Conexão

```python
await websocket.accept()
# ✅ Conexão WebSocket aceita
```

### 3. Backend Inicializa Redis

```python
if not redis_client:
    redis_client = await aioredis.from_url(REDIS_URL)
    redis_pubsub = redis_client.pubsub()
    redis_listener_task = asyncio.create_task(_redis_listener_loop())
# ✅ Redis conectado e listener iniciado
```

### 4. Backend Assina Canais Redis

Para cada símbolo (PETR4, VALE3):
```python
await redis_pubsub.subscribe(f"quotes.{SYMBOL}")
await redis_pubsub.subscribe(f"quotes.{SYMBOL}.header")
# ✅ Canais assinados no Redis
```

### 5. Backend Envia Mensagem de Conexão

```json
{
  "type": "connected",
  "symbols": ["PETR4", "VALE3"],
  "message": "Conectado ao stream de cotações"
}
```

### 6. Backend Recebe e Processa Headers do Redis

Quando o Market Data Service publica um header:
```
Redis: PUBLISH quotes.PETR4.header ["symbol","preco_compra",...]
```

Backend processa:
```python
# Listener Redis recebe mensagem
channel = "quotes.PETR4.header"
data = ["symbol","preco_compra",...]

# Armazena header
headers["PETR4"] = data

# Envia para cliente
await websocket.send_json({
    "type": "header",
    "symbol": "PETR4",
    "data": data
})
```

### 7. Backend Recebe e Processa Cotações do Redis

Quando o Market Data Service publica uma cotação:
```
Redis: PUBLISH quotes.PETR4 ["PETR4",38.1,-1,38.14,-1,38.12,1.5,0.38,null,1763606647]
```

Backend processa:
```python
# Listener Redis recebe mensagem
channel = "quotes.PETR4"
data = ["PETR4",38.1,-1,...]
header = headers["PETR4"]  # ["symbol","preco_compra",...]

# Converte array para objeto
quote_data = {
    "symbol": "PETR4",
    "preco_compra": 38.1,
    "qtde_compra": -1,
    ...
}

# Envia para cliente
await websocket.send_json({
    "type": "quote",
    "symbol": "PETR4",
    "data": quote_data
})
```

### 8. Manutenção da Conexão (Ping/Pong)

A cada 30 segundos sem mensagens do cliente:
```python
# Backend envia ping
await websocket.send_json({"type": "ping"})

# Cliente responde
# Cliente envia: {"type": "pong"}
```

## 🔄 Loop do Listener Redis

O listener Redis roda em uma task separada e processa todas as mensagens:

```python
async def _redis_listener_loop():
    while True:
        # Recebe mensagem do Redis
        message = await redis_pubsub.get_message(timeout=1.0)
        
        if message["type"] == "message":
            channel = message["channel"]
            data = json.loads(message["data"])
            
            # Processa header ou cotação
            if channel.endswith(".header"):
                process_header(channel, data)
            else:
                process_quote(channel, data)
```

## ⚠️ Problemas Identificados e Corrigidos

### 1. Erro 1012 - Conexão Fechada Inesperadamente

**Problema:** A conexão estava sendo fechada com código 1012 (Internal Server Error) logo após receber os headers.

**Causa Raiz:**
- Exceções não tratadas no handler WebSocket
- Listener Redis não estava sendo inicializado corretamente antes de processar mensagens
- Falta de proteção quando `redis_pubsub` não estava criado

**Correções Aplicadas:**

#### A. Tratamento de Exceções Robusto

```python
# Antes
except Exception as e:
    logger.error(f"Erro: {e}")
    break

# Depois
except Exception as e:
    logger.error(f"❌ Erro crítico: {e}", exc_info=True)
    try:
        await websocket.close(code=1011, reason=f"Erro: {str(e)[:50]}")
    except:
        pass
    break
```

#### B. Verificação do Listener Redis

```python
# Garantir que o listener está rodando antes de aceitar conexões
if not self.redis_listener_task or self.redis_listener_task.done():
    self.redis_listener_task = asyncio.create_task(self._redis_listener_loop())
    await asyncio.sleep(0.1)  # Aguardar inicialização
```

#### C. Proteção ao Assinar Canais

```python
# Garantir que pubsub está criado
if not self.redis_pubsub:
    self.redis_pubsub = self.redis_client.pubsub()
    
# Garantir que listener está rodando
if not self.redis_listener_task or self.redis_listener_task.done():
    self.redis_listener_task = asyncio.create_task(self._redis_listener_loop())
```

#### D. Logs Detalhados

Adicionados logs em todos os pontos críticos:
- ✅ Conexão aceita
- ✅ Redis conectado
- ✅ Listener iniciado
- ✅ Canais assinados
- ✅ Headers recebidos
- ✅ Cotações recebidas
- ❌ Erros detalhados com stack trace

### 2. Headers Recebidos mas Cotações Não Chegam

**Problema:** Headers eram recebidos mas as cotações não apareciam.

**Causa Raiz:**
- Cotação chegava antes do header ser armazenado
- Condição `if symbol in headers` falhava

**Correção:**
```python
# Tentar buscar header se não estiver disponível
if symbol not in self.headers:
    await self._try_fetch_header(symbol)
    
if symbol not in self.headers:
    logger.error(f"Não foi possível obter header para {symbol}")
    continue  # Ignorar cotação sem header
```

## 🛡️ Proteções Implementadas

### 1. Validação de Estado

```python
# Antes de enviar mensagem
if websocket.client_state != WebSocketState.CONNECTED:
    logger.warning("WebSocket não está conectado")
    return
```

### 2. Tratamento de Exceções em Cada Operação

```python
try:
    await websocket.send_json(message)
except Exception as e:
    logger.error(f"Erro ao enviar: {e}")
    raise  # Propag para limpar conexão
```

### 3. Limpeza de Recursos

```python
finally:
    # Sempre limpar recursos
    for symbol in symbols:
        await self.unsubscribe_symbol(symbol, websocket)
```

### 4. Verificação de Recursos Antes de Usar

```python
if not self.redis_client:
    await self.initialize()

if not self.redis_pubsub:
    self.redis_pubsub = self.redis_client.pubsub()
```

## 📊 Estrutura de Dados

### Conexões Ativas

```python
active_connections: Dict[str, Set[WebSocket]]
# {
#   "PETR4": {websocket1, websocket2},
#   "VALE3": {websocket1}
# }
```

### Headers Armazenados

```python
headers: Dict[str, List[str]]
# {
#   "PETR4": ["symbol","preco_compra","qtde_compra",...],
#   "VALE3": ["symbol","preco_compra","qtde_compra",...]
# }
```

### Canais Assinados

```python
subscribed_channels: Set[str]
# {"quotes.PETR4", "quotes.PETR4.header", "quotes.VALE3", "quotes.VALE3.header"}
```

## 🔍 Debugging

### Verificar Estado do Serviço

```python
# Status das conexões
print(f"Conexões ativas: {len(active_connections)}")
print(f"Símbolos: {list(active_connections.keys())}")
print(f"Headers: {list(headers.keys())}")
print(f"Canais assinados: {subscribed_channels}")
print(f"Listener rodando: {redis_listener_task and not redis_listener_task.done()}")
```

### Logs Importantes

Procure por estas mensagens nos logs:

**Sucesso:**
- ✅ `Conexão com Redis estabelecida`
- ✅ `Listener Redis iniciado`
- ✅ `Assinado canal Redis: quotes.PETR4`
- ✅ `Header recebido para PETR4`
- ✅ `Cotação recebida para PETR4`

**Erro:**
- ❌ `Erro ao conectar com Redis`
- ❌ `Erro ao iniciar listener Redis`
- ❌ `Erro ao assinar canal`
- ❌ `Erro no listener Redis`

## 🚀 Próximos Passos

1. **Monitorar Logs**: Verificar se os erros 1012 pararam de ocorrer
2. **Testar Reconexão**: Garantir que reconexão automática funciona
3. **Monitorar Performance**: Verificar se não há vazamento de memória
4. **Testar Múltiplos Clientes**: Garantir que múltiplas conexões funcionam

## 📝 Resumo das Mudanças

1. ✅ Tratamento de exceções robusto em todos os pontos críticos
2. ✅ Verificação e inicialização adequada do listener Redis
3. ✅ Proteção ao assinar canais Redis
4. ✅ Logs detalhados para debugging
5. ✅ Limpeza adequada de recursos
6. ✅ Validação de estado antes de operações
7. ✅ Tentativa de buscar headers quando não disponíveis

Essas mudanças devem resolver o problema do erro 1012 e garantir que a conexão WebSocket permaneça estável.







