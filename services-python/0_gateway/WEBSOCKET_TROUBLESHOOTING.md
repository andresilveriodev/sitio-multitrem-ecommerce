# 🔧 Troubleshooting: WebSocket Streaming de Cotações

## 📋 Problemas Comuns e Soluções

### 1. Erro: "WebSocket is closed before the connection is established" / Código 1012

**Sintomas:**
- Conexão WebSocket é fechada logo após conectar
- Código de erro 1012 (Internal Server Error)
- Headers são recebidos mas depois a conexão fecha
- Logs mostram "Conexão fechada: 1012 Sem motivo especificado"

**Causas Possíveis:**

#### A. Erro não tratado no backend

O servidor está encontrando uma exceção não tratada que causa o fechamento da conexão.

**Solução:**
1. Verificar logs do backend para encontrar a exceção exata
2. Procurar por mensagens de erro no console do servidor Python
3. Verificar se o Redis está conectado e respondendo
4. Verificar se há mensagens no formato correto sendo publicadas no Redis

**Verificação no Backend:**
```bash
# Verificar logs do servidor
tail -f logs/app.log | grep ERROR

# Ou se estiver rodando com uvicorn
# Verificar console do terminal onde o servidor está rodando
```

#### B. Problema na inicialização do listener Redis

O listener Redis pode não estar iniciando corretamente.

**Solução:**
1. Verificar se o listener está rodando:
   ```python
   # No código, verificar se redis_listener_task está ativo
   if streaming_service.redis_listener_task and not streaming_service.redis_listener_task.done():
       print("Listener está rodando")
   else:
       print("Listener NÃO está rodando")
   ```

2. Verificar conexão Redis:
   ```bash
   # Testar conexão Redis
   redis-cli -h localhost -p 6379 -n 1 ping
   # Deve retornar: PONG
   ```

#### C. Exceção ao processar mensagens do Redis

Se o formato das mensagens do Redis não estiver correto, pode causar exceções.

**Solução:**
1. Verificar formato das mensagens no Redis:
   ```bash
   # Monitorar mensagens publicadas no Redis
   redis-cli -h localhost -p 6379 -n 1
   > PSUBSCRIBE quotes.*
   ```

2. Verificar se as mensagens são JSON válido
3. Verificar se os arrays têm o tamanho correto

### 2. Headers recebidos mas cotações não chegam

**Sintomas:**
- Headers são recebidos corretamente
- Mensagem "Conectado" aparece
- Mas nenhuma cotação chega

**Causas Possíveis:**

#### A. Redis não está publicando cotações

**Solução:**
1. Verificar se o Market Data Service está rodando
2. Verificar se está publicando no Redis:
   ```bash
   redis-cli -h localhost -p 6379 -n 1
   > PSUBSCRIBE quotes.*
   ```
3. Verificar se está publicando nos canais corretos:
   - `quotes.PETR4` (para cotações)
   - `quotes.PETR4.header` (para headers)

#### B. Símbolos não estão sendo negociados

Se o mercado estiver fechado ou os símbolos não estiverem ativos, não haverá cotações.

**Solução:**
1. Verificar horário de funcionamento do mercado
2. Testar com símbolos conhecidos por estarem ativos
3. Verificar se o Market Data Service está recebendo dados do MT5

#### C. Listener Redis não está escutando os canais corretos

**Solução:**
1. Verificar logs do backend para ver quais canais foram assinados:
   ```
   Assinado canal Redis: quotes.PETR4
   Assinado canal Redis: quotes.PETR4.header
   ```

2. Verificar se os canais estão na lista de `subscribed_channels`

### 3. Conexão fecha e reconecta repetidamente

**Sintomas:**
- Conexão fecha
- Tenta reconectar automaticamente
- Fecha novamente
- Loop infinito

**Causas Possíveis:**

#### A. Erro persistente no backend

Há um erro que acontece toda vez que a conexão é estabelecida.

**Solução:**
1. Verificar logs do backend para encontrar o padrão de erro
2. Verificar se há recursos sendo esgotados (memória, conexões)
3. Verificar se há múltiplas instâncias do listener tentando rodar

#### B. Problema na inicialização do serviço

**Solução:**
1. Garantir que o serviço é inicializado apenas uma vez
2. Verificar se há múltiplas conexões sendo criadas para o mesmo serviço
3. Limpar recursos antigos antes de criar novos

### 4. Erro ao enviar mensagens (exceções silenciosas)

**Sintomas:**
- Backend parece estar funcionando
- Mas mensagens não chegam no frontend
- Logs mostram warnings sobre erros ao enviar

**Solução:**
1. Verificar se o WebSocket está realmente aberto:
   ```python
   # No backend, antes de enviar:
   if websocket.client_state != WebSocketState.CONNECTED:
       logger.warning("WebSocket não está conectado")
   ```

2. Verificar se há exceções sendo suprimidas
3. Verificar logs de erro completos (com stack trace)

## 🔍 Checklist de Diagnóstico

### Backend

- [ ] Redis está rodando e acessível?
- [ ] Servidor Python está logando erros?
- [ ] Listener Redis está iniciado?
- [ ] Canais Redis estão sendo assinados corretamente?
- [ ] Mensagens estão chegando do Redis?
- [ ] Formato das mensagens está correto (JSON válido)?
- [ ] Headers estão sendo armazenados corretamente?
- [ ] WebSocket está aceitando conexões?
- [ ] Não há exceções não tratadas?

### Frontend

- [ ] WebSocket está conectando?
- [ ] URL do WebSocket está correta?
- [ ] Headers estão sendo recebidos?
- [ ] Mensagens de "connected" estão chegando?
- [ ] Callbacks estão sendo chamados?
- [ ] Não há erros no console do navegador?
- [ ] Reconexão está funcionando?

### Redis/Market Data

- [ ] Market Data Service está rodando?
- [ ] Está publicando no Redis?
- [ ] Canais estão corretos (quotes.{SYMBOL})?
- [ ] Formato das mensagens está correto?
- [ ] Headers estão sendo publicados?
- [ ] Cotações estão sendo publicadas continuamente?

## 🛠️ Comandos Úteis para Debug

### Verificar conexão Redis

```bash
redis-cli -h localhost -p 6379 -n 1 ping
```

### Monitorar mensagens Redis em tempo real

```bash
redis-cli -h localhost -p 6379 -n 1
> PSUBSCRIBE quotes.*
```

### Verificar canais ativos

```bash
redis-cli -h localhost -p 6379 -n 1 PUBSUB CHANNELS quotes.*
```

### Testar WebSocket manualmente (wscat)

```bash
# Instalar wscat
npm install -g wscat

# Conectar
wscat -c "ws://localhost:8000/ws/quotes?symbols=PETR4,VALE3"
```

### Verificar status do streaming

```bash
curl http://localhost:8000/stream/status
```

## 📝 Logs Detalhados

Para habilitar logs mais detalhados no backend:

```python
import logging

# No arquivo de configuração ou antes de iniciar o servidor
logging.basicConfig(
    level=logging.DEBUG,  # Mudar de INFO para DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Ou para logs específicos do streaming:

```python
logging.getLogger('services.streaming_service').setLevel(logging.DEBUG)
```

## 🔄 Fluxo Esperado

1. **Cliente conecta** → WebSocket aceito
2. **Backend inicializa Redis** → Conexão estabelecida
3. **Listener Redis inicia** → Task criada
4. **Símbolos são assinados** → Canais Redis assinados
5. **Header é recebido** → Enviado para cliente
6. **Mensagem "connected"** → Enviada para cliente
7. **Cotações começam a chegar** → Convertidas e enviadas
8. **Ping/Pong** → Mantém conexão viva

## ⚠️ Problema Específico: Código 1012

O código 1012 indica "Internal Server Error". Isso significa que o servidor encontrou uma condição inesperada.

**Causas mais comuns:**
1. Exceção não tratada que fecha a conexão
2. Problema ao processar mensagens do Redis
3. Erro ao enviar mensagens para o WebSocket
4. Problema na inicialização do listener

**Como diagnosticar:**
1. Verificar logs do backend imediatamente após a conexão
2. Procurar por exceções não tratadas
3. Verificar se o listener Redis está rodando
4. Verificar se há recursos sendo esgotados

**Solução imediata:**
1. Adicionar try/catch em todos os pontos críticos
2. Adicionar logs detalhados
3. Verificar stack trace completo das exceções
4. Garantir que o listener Redis está inicializado antes de aceitar conexões







