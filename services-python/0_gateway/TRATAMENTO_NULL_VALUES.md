# 🔧 Tratamento de Valores Null nas Cotações

## 🐛 Problema

O frontend está recebendo valores `null` em campos numéricos e tentando chamar `.toFixed()` neles, causando erro:

```
TypeError: Cannot read properties of null (reading 'toFixed')
at formatPrice (useQuoteStream.ts:12:1)
```

## ✅ Solução no Backend

O backend agora trata valores `null` adequadamente ao converter arrays para objetos:

1. **Campos que podem ser null:**
   - `ultimo_horario`: Mantido como `null` (string opcional)
   - Campos numéricos: Tratados adequadamente

2. **Valores padrão:**
   - Quantidades (`qtde_compra`, `qtde_venda`): `null` → `-1`
   - Outros campos numéricos: Mantêm `null` se vierem assim

## 🔧 Solução no Frontend

O frontend DEVE tratar valores `null` ao formatar números:

### ❌ Código ERRADO

```typescript
function formatPrice(price: number): string {
  return price.toFixed(2);  // ❌ Erro se price for null
}
```

### ✅ Código CORRETO

```typescript
function formatPrice(price: number | null): string {
  if (price === null || price === undefined) {
    return '--';
  }
  return price.toFixed(2);
}

// Ou com valor padrão
function formatPrice(price: number | null): string {
  return (price ?? 0).toFixed(2);
}
```

### ✅ Exemplo Completo

```typescript
interface QuoteData {
  symbol: string;
  preco_compra: number | null;
  qtde_compra: number | null;
  preco_venda: number | null;
  qtde_venda: number | null;
  preco_ultimo: number | null;
  mudanca_diaria: number | null;
  oscilacao_diaria: number | null;
  ultimo_horario: string | null;
  timestamp: number | null;
}

function formatPrice(price: number | null): string {
  if (price === null || price === undefined || isNaN(price)) {
    return '--';
  }
  return `R$ ${price.toFixed(2)}`;
}

function formatPercentage(value: number | null): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '--';
  }
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function formatQuantity(qty: number | null): string {
  if (qty === null || qty === undefined || qty === -1) {
    return '--';
  }
  return qty.toString();
}

// Uso
const quote: QuoteData = message.data;
const lastPrice = formatPrice(quote.preco_ultimo);
const change = formatPercentage(quote.mudanca_diaria);
const quantity = formatQuantity(quote.qtde_compra);
```

## 📋 Campos que Podem Ser Null

Baseado no formato JSON Array Rows:

| Campo | Tipo | Pode ser null? | Valor padrão sugerido |
|-------|------|----------------|----------------------|
| `symbol` | string | Não | Sempre presente |
| `preco_compra` | number | Sim | `--` ou `0` |
| `qtde_compra` | number | Sim | `-1` = não disponível |
| `preco_venda` | number | Sim | `--` ou `0` |
| `qtde_venda` | number | Sim | `-1` = não disponível |
| `preco_ultimo` | number | Sim | `--` ou `0` |
| `mudanca_diaria` | number | Sim | `--` ou `0` |
| `oscilacao_diaria` | number | Sim | `--` ou `0` |
| `ultimo_horario` | string | Sim | `--` ou vazio |
| `timestamp` | number | Sim | `0` |

## 🛠️ Funções Utilitárias Recomendadas

```typescript
// utils/formatQuote.ts

export function formatPrice(price: number | null | undefined): string {
  if (price == null || isNaN(price)) {
    return '--';
  }
  return `R$ ${price.toFixed(2).replace('.', ',')}`;
}

export function formatPercentage(value: number | null | undefined): string {
  if (value == null || isNaN(value)) {
    return '--';
  }
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2).replace('.', ',')}%`;
}

export function formatAbsolute(value: number | null | undefined): string {
  if (value == null || isNaN(value)) {
    return '--';
  }
  return value.toFixed(2).replace('.', ',');
}

export function formatQuantity(qty: number | null | undefined): string {
  if (qty == null || qty === -1) {
    return '--';
  }
  return qty.toLocaleString('pt-BR');
}

export function formatTime(time: string | null | undefined): string {
  if (!time) {
    return '--';
  }
  return time;
}

export function formatTimestamp(ts: number | null | undefined): string {
  if (!ts) {
    return '--';
  }
  const date = new Date(ts * 1000);
  return date.toLocaleTimeString('pt-BR');
}
```

## 🎨 Uso no Componente React

```typescript
import { formatPrice, formatPercentage } from '@/utils/formatQuote';

function QuoteDisplay({ quote }: { quote: QuoteData }) {
  return (
    <div>
      <h3>{quote.symbol}</h3>
      <p>Último: {formatPrice(quote.preco_ultimo)}</p>
      <p>Compra: {formatPrice(quote.preco_compra)}</p>
      <p>Venda: {formatPrice(quote.preco_venda)}</p>
      <p>
        Variação: {formatPercentage(quote.mudanca_diaria)}
        {' '}
        ({formatAbsolute(quote.oscilacao_diaria)})
      </p>
      <p>Horário: {formatTime(quote.ultimo_horario)}</p>
    </div>
  );
}
```

## ✅ Checklist de Correção

- [ ] Verificar função `formatPrice` - deve tratar null
- [ ] Verificar função `formatPercentage` - deve tratar null
- [ ] Verificar todos os lugares onde `.toFixed()` é chamado
- [ ] Adicionar validação `null` antes de operações numéricas
- [ ] Testar com dados que contenham null
- [ ] Usar valores padrão apropriados para cada campo

## 🔍 Debug

Para debugar valores null:

```typescript
function formatPrice(price: number | null): string {
  console.log('formatPrice recebeu:', price, 'tipo:', typeof price);
  
  if (price === null || price === undefined) {
    console.warn('Preço é null ou undefined');
    return '--';
  }
  
  if (isNaN(price)) {
    console.warn('Preço não é um número válido:', price);
    return '--';
  }
  
  return price.toFixed(2);
}
```







