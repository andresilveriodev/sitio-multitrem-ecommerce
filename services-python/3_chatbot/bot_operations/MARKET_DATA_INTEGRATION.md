# 📊 Integração com Market Data Service

## ✅ Implementação Concluída

O Chatbot Service agora está integrado com o **Market Data Service** para buscar cotações em tempo real.

## 🔗 Endpoints Utilizados

### 1. `/quotes/quote-box` - Cotação Completa
**Uso:** Buscar preço e informações de um ativo específico

```python
# Exemplo de uso no código
price = await market_service.get_ticker_price("PETR4")
# Faz requisição: GET /quotes/quote-box?symbol=PETR4&compact=true
```

**Parâmetros:**
- `symbol` (obrigatório): Ticker do ativo (ex: PETR4)
- `compact` (opcional): `true` para resposta compacta, `false` para completa

**Retorna:**
- Preço último negociado (`last` ou `ultimo`)
- Informações adicionais quando `compact=false`

### 2. `/quotes/cotacoes` - Múltiplas Cotações
**Uso:** Buscar preços de vários ativos de uma vez

```python
# Exemplo de uso no código
quotes = await market_service.get_multiple_quotes(["PETR4", "VALE3", "ITUB4"])
# Faz requisição: GET /quotes/cotacoes?symbols=PETR4,VALE3,ITUB4
```

**Parâmetros:**
- `symbols` (obrigatório): Lista de tickers separados por vírgula

**Retorna:**
- Dict com ticker como chave e preço como valor

## 🔧 Configuração

### Variáveis de Ambiente

Adicione ao `.env`:
```env
MARKET_DATA_SERVICE_URL=http://localhost:8000
MARKET_DATA_SERVICE_TIMEOUT=10
```

### Inicialização

O serviço é inicializado automaticamente no `app.py`:
```python
await market_service.connect()
```

## 📝 Métodos Disponíveis

### `get_ticker_price(ticker: str) -> Optional[float]`
Busca preço atual de um ticker.

**Exemplo:**
```python
price = await market_service.get_ticker_price("PETR4")
# Retorna: 25.50 ou None se não encontrar
```

**Comportamento:**
- Tenta buscar do Market Data Service
- Se falhar, usa fallback com preços mock
- Loga erros e warnings

### `validate_ticker(ticker: str) -> bool`
Valida se um ticker existe.

**Exemplo:**
```python
is_valid = await market_service.validate_ticker("PETR4")
# Retorna: True ou False
```

**Comportamento:**
- Valida formato primeiro (4 letras + número opcional)
- Tenta buscar cotação para confirmar existência
- Se falhar, usa lista de tickers conhecidos como fallback

### `get_multiple_quotes(symbols: List[str]) -> Dict[str, Optional[float]]`
Busca preços de múltiplos tickers.

**Exemplo:**
```python
quotes = await market_service.get_multiple_quotes(["PETR4", "VALE3"])
# Retorna: {"PETR4": 25.50, "VALE3": 65.80}
```

### `get_investment_type_info(ticker: str) -> Optional[Dict[str, Any]]`
Busca informações sobre o tipo de investimento.

**Exemplo:**
```python
info = await market_service.get_investment_type_info("PETR4")
# Retorna: {
#   "ticker": "PETR4",
#   "category": "Ações",
#   "name": "Ação PETR4",
#   "market": "B3"
# }
```

## 🛡️ Tratamento de Erros

### Fallback Automático
Se o Market Data Service não estiver disponível ou retornar erro:
- Usa preços mock para desenvolvimento
- Loga warnings mas não quebra o fluxo
- Permite que o chatbot continue funcionando

### Casos Tratados
- ✅ Timeout na requisição
- ✅ Erro de conexão
- ✅ Ticker não encontrado (404)
- ✅ Erro de servidor (5xx)
- ✅ Resposta em formato inesperado

## 📊 Exemplo de Fluxo Completo

```python
# 1. Usuário diz: "Adiciona 500 PETR4"
# 2. InvestmentProcessor detecta que falta preço
# 3. Chama market_service.get_ticker_price("PETR4")
# 4. MarketService faz requisição:
#    GET http://localhost:8000/quotes/quote-box?symbol=PETR4&compact=true
# 5. Market Data Service retorna:
#    {
#      "symbol": "PETR4",
#      "last": 25.50,
#      "bid": 25.49,
#      "ask": 25.51,
#      ...
#    }
# 6. MarketService extrai preço: 25.50
# 7. InvestmentProcessor gera frontend_action com preço de mercado
# 8. Resposta inclui aviso: "Preço obtido do mercado atual"
```

## 🔍 Logs e Monitoramento

O serviço loga:
- ✅ Requisições bem-sucedidas
- ⚠️ Warnings quando usa fallback
- ❌ Erros de conexão/timeout
- 📊 Estatísticas de uso

**Exemplo de logs:**
```
INFO: Buscando preço de PETR4 via Market Data Service
INFO: Preço encontrado para PETR4: R$ 25.50
```

ou

```
WARNING: Timeout ao buscar preço de PETR4, usando fallback
INFO: Usando preço mock para PETR4: R$ 25.50
```

## 🚀 Melhorias Futuras (Opcional)

1. **Cache de Preços**
   - Cachear preços por alguns segundos
   - Reduzir chamadas ao Market Data Service
   - Melhorar performance

2. **Retry com Backoff**
   - Tentar novamente em caso de erro temporário
   - Backoff exponencial

3. **Streaming de Cotações**
   - Usar Redis Pub/Sub para cotações em tempo real
   - Canal: `quotes.{SYMBOL}`

4. **Validação de Horário de Mercado**
   - Verificar se mercado está aberto
   - Ajustar comportamento fora do horário

## 📖 Documentação Relacionada

- `INVESTMENT_COMMANDS_IMPLEMENTATION.md` - Implementação de comandos
- Market Data Service - Documentação dos endpoints

