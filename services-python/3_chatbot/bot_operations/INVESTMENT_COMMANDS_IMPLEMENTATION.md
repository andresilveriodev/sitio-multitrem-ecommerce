# 📊 Implementação de Comandos de Investimento

## ✅ O que foi implementado

### 1. **Serviço de Extração de Dados** (`services/investment_extractor.py`)
- Extrai dados de investimentos de mensagens do usuário e respostas da IA
- Detecta ações: adicionar, remover, atualizar
- Extrai: ticker, quantity, price, valor, categoria, data, rentabilidade
- Detecta operações vendidas (short selling)
- Valida campos obrigatórios
- Calcula valores faltantes quando possível

### 2. **Serviço de Processamento** (`services/investment_processor.py`)
- Processa comandos de investimento
- Gera `frontend_action` conforme especificação
- Valida dados antes de gerar ação
- Busca preços de mercado quando necessário
- Pergunta ao usuário se faltar informação crítica
- Suporta operações vendidas (quantidade negativa)

### 3. **Serviço de Mercado** (`services/market_service.py`)
- ✅ **Integrado com Market Data Service** para cotações em tempo real
- Busca preços de tickers via `/quotes/quote-box`
- Valida tickers consultando o Market Data Service
- Busca informações de tipos de investimento
- Suporta busca de múltiplas cotações via `/quotes/cotacoes`
- Fallback para mock quando API não está disponível

### 4. **Modelos Pydantic** (`models/investment_models.py`)
- `FrontendAction`: Estrutura de frontend_action
- `InvestmentAddParameters`: Parâmetros para adicionar
- `InvestmentRemoveParameters`: Parâmetros para remover
- `InvestmentUpdateParameters`: Parâmetros para atualizar
- `ChatResponse`: Resposta do chat
- `ProcessMessageResponse`: Resposta completa

### 5. **Integração no Chat Router** (`routes/chat_router.py`)
- Processa comandos de investimento após resposta da IA
- Gera `frontend_action` quando dados estão completos
- Retorna pergunta ao usuário se faltar informação
- Mantém compatibilidade com comandos existentes

## 🔄 Fluxo de Processamento

```
1. Usuário envia mensagem: "Adiciona 500 PETR4"
   ↓
2. Chatbot Service valida segurança
   ↓
3. Verifica cache e filtros automáticos
   ↓
4. Envia para AI Service
   ↓
5. AI Service retorna resposta da IA
   ↓
6. InvestmentProcessor extrai dados da mensagem + resposta IA
   ↓
7. Se dados completos:
   - Busca preço de mercado (se necessário)
   - Calcula valores faltantes
   - Gera frontend_action
   - Retorna com confirmation_required=true
   ↓
8. Se faltar informação:
   - Retorna pergunta ao usuário
   - frontend_action = null
   - needs_user_input = true
   ↓
9. Frontend recebe e exibe confirmação ou pergunta
```

## 📝 Exemplos de Uso

### Exemplo 1: Adicionar investimento com dados completos
```
Usuário: "Adiciona 500 PETR4 a R$ 25,50"

Resposta:
{
  "success": true,
  "response": {
    "response": "Adicionei 500 de PETR4\n• Preço: R$ 25.50\n• Valor total: R$ 12750.00\n\nDeseja confirmar a adição?",
    "frontend_action": {
      "type": "add_investment",
      "parameters": {
        "categoryName": "Ações",
        "ticker": "PETR4",
        "quantity": 500,
        "price": 25.50,
        "valor": 12750.00,
        "isShort": false,
        "dataAquisicao": "2025-01-26",
        "rentabilidade": 0
      },
      "command_id": "uuid-gerado"
    },
    "confirmation_required": true
  }
}
```

### Exemplo 2: Adicionar investimento sem preço
```
Usuário: "Adiciona 500 PETR4"

Resposta:
{
  "success": true,
  "response": {
    "response": "Adicionei 500 de PETR4\n• Preço: R$ 25.50 (preço atual de mercado)\n• Valor total: R$ 12750.00\n\nDeseja confirmar a adição?",
    "frontend_action": {
      "type": "add_investment",
      "parameters": {
        "categoryName": "Ações",
        "ticker": "PETR4",
        "quantity": 500,
        "price": 25.50,
        "price_from_market": true,
        "valor": 12750.00,
        "isShort": false,
        "dataAquisicao": "2025-01-26"
      },
      "command_id": "uuid-gerado"
    },
    "confirmation_required": true,
    "warnings": ["Preço obtido do mercado atual"]
  }
}
```

### Exemplo 3: Falta informação crítica
```
Usuário: "Adiciona PETR4"

Resposta:
{
  "success": true,
  "response": {
    "response": "Para adicionar PETR4, preciso saber:\n• Quantas ações/cotas ou qual o valor total?\n• Qual foi o preço de compra? (ou posso usar o preço atual de mercado)",
    "frontend_action": null,
    "confirmation_required": false,
    "needs_user_input": true,
    "missing_fields": ["quantity ou valor total", "price"]
  }
}
```

### Exemplo 4: Operação vendida (short selling)
```
Usuário: "Vendi 500 PETR4"

Resposta:
{
  "success": true,
  "response": {
    "response": "Operação vendida detectada:\n• Ticker: PETR4\n• Quantidade: -500 (negativa = posição vendida)\n• Preço: R$ 25.50\n• Valor total: -R$ 12750.00\n\nDeseja confirmar a adição?",
    "frontend_action": {
      "type": "add_investment",
      "parameters": {
        "categoryName": "Ações",
        "ticker": "PETR4",
        "quantity": -500,
        "price": 25.50,
        "valor": -12750.00,
        "isShort": true,
        "dataAquisicao": "2025-01-26"
      },
      "command_id": "uuid-gerado"
    },
    "confirmation_required": true
  }
}
```

## 🎯 Regras Implementadas

### ✅ Regras Críticas Seguidas

1. **NUNCA inventar valores**
   - Se faltar informação crítica, pergunta ao usuário
   - Não retorna `frontend_action` com dados incompletos

2. **Sempre avisar quando usar preço de mercado**
   - Flag `price_from_market: true`
   - Mensagem explicativa na resposta

3. **Suporta operações vendidas**
   - Quantidade negativa = operação vendida
   - Valor negativo quando quantity < 0
   - Flag `isShort: true`

4. **Validações obrigatórias**
   - Ticker válido (se for ação)
   - Quantidade != 0 (pode ser negativa)
   - Preço > 0 (sempre positivo)
   - Valor != 0 (pode ser negativo)

5. **Calcula valores quando possível**
   - Se tem quantity e price → calcula valor
   - Se tem valor e price → calcula quantity
   - Se tem valor e quantity → calcula price

## 🔧 Configuração

### Variáveis de Ambiente

Adicione ao `.env`:
```env
# Market Data Service (cotações em tempo real)
MARKET_DATA_SERVICE_URL=http://localhost:8000
MARKET_DATA_SERVICE_TIMEOUT=10
```

**Endpoints utilizados:**
- `GET /quotes/quote-box?symbol={TICKER}&compact=true` - Cotação de um ativo
- `GET /quotes/cotacoes?symbols={TICKER1},{TICKER2},...` - Múltiplas cotações

### Inicialização

Os serviços são inicializados automaticamente no `app.py`:
- `market_service.connect()` - Conecta ao serviço de mercado
- `investment_extractor` - Instância global
- `investment_processor` - Instância global

## 📚 Próximos Passos

### 1. ✅ Integração com Market Data Service - CONCLUÍDA
- ✅ Implementado `get_ticker_price()` com API real
- ✅ Implementado `validate_ticker()` com API real
- ⚠️ Adicionar cache de preços (opcional, para reduzir chamadas)

### 2. Adicionar Comandos de Categoria
- `add_investment_category`
- `remove_investment_category`
- `update_investment_category`
- `distribute_investments`

### 3. Melhorar Extração de Dados
- Usar IA para extrair dados mais complexos
- Suportar mais formatos de entrada
- Melhorar detecção de contexto

### 4. Adicionar Validações de Negócio
- Validar limites de investimento
- Validar categorias existentes
- Validar planId e periodoId

### 5. Testes
- Testes unitários para extração
- Testes de integração
- Testes de validação

## 📖 Documentação Relacionada

- `CHATBOT_IA_SERVICE_INTEGRATION.md` - Arquitetura completa
- `BACKEND_INVESTMENT_ACTIONS_API.md` - Especificação de ações
- `BACKEND_INVESTMENT_ACTIONS_RULES.md` - Regras de processamento

## 🐛 Troubleshooting

### Problema: Não detecta comandos de investimento
- Verificar se a mensagem contém palavras-chave (adiciona, remove, atualiza)
- Verificar logs do `investment_extractor`

### Problema: Preço não encontrado
- Verificar se `market_service` está conectado
- Verificar se ticker está no mock (ou implementar API real)

### Problema: frontend_action não gerado
- Verificar se dados obrigatórios estão presentes
- Verificar logs do `investment_processor`
- Verificar se `missing_fields` está vazio

