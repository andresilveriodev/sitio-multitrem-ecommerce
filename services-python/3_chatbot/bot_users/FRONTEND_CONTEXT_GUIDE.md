# 📱 Guia: Como o Frontend Deve Enviar Contexto ao Chatbot Service

## 🎯 Visão Geral

O frontend pode enviar contexto de investimentos para melhorar as respostas da IA. O contexto é opcional - o sistema funciona sem ele, mas funciona melhor com ele.

## 📝 Endpoint Principal

### `POST /chatbot/process-message`

## 🔄 Formato da Requisição

### Estrutura Básica (sem contexto)

```json
{
  "user_id": "uuid-do-usuario",
  "message": "Adiciona 500 PETR4",
  "session_id": "session-123" // opcional
}
```

### Estrutura com Contexto de Investimentos

```json
{
  "user_id": "uuid-do-usuario",
  "message": "Adiciona 500 PETR4",
  "session_id": "session-123", // opcional
  "context": {
    "current_plan_id": "uuid-do-plano-atual",
    "current_periodo_id": "uuid-do-periodo-atual", // opcional
    "investment_categories": [
      {
        "id": "cat-1",
        "nome": "Ações",
        "percentual": 40,
        "valor": 120000.00,
        "investimentos": [
          {
            "id": "inv-1",
            "ticker": "PETR4",
            "quantity": 1000,
            "price": 25.50,
            "valor": 25500.00
          },
          {
            "id": "inv-2",
            "ticker": "VALE3",
            "quantity": 500,
            "price": 65.80,
            "valor": 32900.00
          }
        ]
      },
      {
        "id": "cat-2",
        "nome": "CDB",
        "percentual": 30,
        "valor": 90000.00,
        "investimentos": []
      }
    ],
    "available_investment_types": [
      {
        "id": 1,
        "name": "Ações",
        "category": "Renda Variável",
        "description": "Ações negociadas na bolsa"
      },
      {
        "id": 2,
        "name": "CDB",
        "category": "Renda Fixa",
        "description": "Certificado de Depósito Bancário"
      },
      {
        "id": 3,
        "name": "FIIs",
        "category": "Renda Variável",
        "description": "Fundos Imobiliários"
      }
    ],
    "current_investments": [
      {
        "id": "inv-1",
        "ticker": "PETR4",
        "categoryName": "Ações",
        "quantity": 1000,
        "price": 25.50,
        "valor": 25500.00,
        "dataAquisicao": "2025-01-15"
      }
    ]
  }
}
```

## 📋 Campos do Contexto

### Campos Obrigatórios (quando enviar contexto)

Nenhum campo é obrigatório - o contexto é totalmente opcional.

### Campos Opcionais (mas úteis)

#### `current_plan_id` (string, opcional)
- ID do plano financeiro atual do usuário
- Usado para associar investimentos ao plano correto

#### `current_periodo_id` (string, opcional)
- ID do período atual (se o sistema usa períodos)
- Usado para associar investimentos ao período correto

#### `investment_categories` (array, opcional)
- Lista de categorias de investimento do usuário
- Cada categoria deve ter:
  - `id`: ID da categoria
  - `nome`: Nome da categoria (ex: "Ações", "CDB")
  - `percentual`: Percentual alocado (opcional)
  - `valor`: Valor total da categoria (opcional)
  - `investimentos`: Lista de investimentos da categoria (opcional)

#### `available_investment_types` (array, opcional)
- Tipos de investimento disponíveis no sistema
- Cada tipo deve ter:
  - `id`: ID do tipo
  - `name`: Nome do tipo
  - `category`: Categoria (ex: "Renda Variável", "Renda Fixa")
  - `description`: Descrição (opcional)

#### `current_investments` (array, opcional)
- Lista de investimentos atuais do usuário
- Cada investimento deve ter:
  - `id`: ID do investimento
  - `ticker`: Ticker do ativo (se aplicável)
  - `categoryName`: Nome da categoria
  - `quantity`: Quantidade
  - `price`: Preço unitário
  - `valor`: Valor total
  - `dataAquisicao`: Data de aquisição (opcional)

## 💡 Exemplos de Uso

### Exemplo 1: Enviar apenas plan_id

```typescript
const response = await fetch('http://localhost:8008/chatbot/process-message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'user-123',
    message: 'Adiciona 500 PETR4',
    context: {
      current_plan_id: 'plan-456'
    }
  })
});
```

### Exemplo 2: Enviar contexto completo

```typescript
const response = await fetch('http://localhost:8008/chatbot/process-message', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: 'user-123',
    message: 'Adiciona 500 PETR4',
    context: {
      current_plan_id: 'plan-456',
      current_periodo_id: 'periodo-789',
      investment_categories: [
        {
          id: 'cat-1',
          nome: 'Ações',
          percentual: 40,
          valor: 120000.00,
          investimentos: [
            {
              id: 'inv-1',
              ticker: 'PETR4',
              quantity: 1000,
              price: 25.50,
              valor: 25500.00
            }
          ]
        }
      ],
      available_investment_types: [
        {
          id: 1,
          name: 'Ações',
          category: 'Renda Variável',
          description: 'Ações negociadas na bolsa'
        }
      ]
    }
  })
});
```

### Exemplo 3: Hook React para enviar contexto

```typescript
import { useState } from 'react';

interface InvestmentContext {
  current_plan_id?: string;
  current_periodo_id?: string;
  investment_categories?: Array<{
    id: string;
    nome: string;
    percentual?: number;
    valor?: number;
    investimentos?: Array<any>;
  }>;
  available_investment_types?: Array<{
    id: number;
    name: string;
    category: string;
    description?: string;
  }>;
  current_investments?: Array<any>;
}

interface ChatMessage {
  user_id: string;
  message: string;
  session_id?: string;
  context?: InvestmentContext;
}

const useChatbotWithContext = () => {
  const [loading, setLoading] = useState(false);
  
  const sendMessage = async (
    userId: string,
    message: string,
    context?: InvestmentContext
  ) => {
    setLoading(true);
    
    try {
      const chatMessage: ChatMessage = {
        user_id: userId,
        message,
        context // Envia contexto se disponível
      };
      
      const response = await fetch('http://localhost:8008/chatbot/process-message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chatMessage)
      });
      
      const data = await response.json();
      return data;
    } finally {
      setLoading(false);
    }
  };
  
  return { sendMessage, loading };
};

// Uso no componente
const MyComponent = () => {
  const { sendMessage, loading } = useChatbotWithContext();
  const [currentPlan] = useState('plan-123');
  const [categories] = useState([...]);
  
  const handleSend = async () => {
    const context = {
      current_plan_id: currentPlan,
      investment_categories: categories
    };
    
    const result = await sendMessage('user-123', 'Adiciona 500 PETR4', context);
    console.log(result);
  };
  
  return <button onClick={handleSend}>Enviar</button>;
};
```

## 🔄 Como o Chatbot Service Processa

1. **Recebe requisição** com ou sem contexto
2. **Se tem contexto:**
   - Armazena no `conversation_metadata` do contexto da conversa
   - Envia para AI Service junto com a mensagem
   - Usa para processar comandos de investimento
3. **Se não tem contexto:**
   - Funciona normalmente (sem contexto)
   - AI Service recebe apenas a mensagem

## 📊 Onde o Contexto é Usado

### 1. No AI Service
- Melhora respostas da IA com conhecimento dos investimentos do usuário
- Permite respostas mais contextualizadas

### 2. No Investment Processor
- Usa `plan_id` e `periodo_id` para gerar `frontend_action` correto
- Valida contra categorias existentes
- Sugere categorias baseado em tipos disponíveis

### 3. No Context Service
- Armazena no `conversation_metadata` para uso futuro
- Mantém contexto entre mensagens da mesma sessão

## ⚠️ Observações Importantes

1. **Contexto é opcional**: O sistema funciona perfeitamente sem ele
2. **Pode enviar parcialmente**: Não precisa enviar todos os campos
3. **Não é persistido automaticamente**: Se quiser manter entre sessões, envie novamente
4. **Pode atualizar**: Envie contexto atualizado quando necessário

## 🎯 Quando Enviar Contexto

### ✅ Envie contexto quando:
- Usuário está em uma tela de investimentos
- Tem dados de plano/período disponíveis
- Quer respostas mais contextualizadas
- Está processando comandos de investimento

### ❌ Não precisa enviar quando:
- Conversa geral (não relacionada a investimentos)
- Não tem dados disponíveis
- Primeira interação (pode enviar depois)

## 🔧 Integração com Context Service

O Chatbot Service armazena o contexto no `conversation_metadata`:

```typescript
// Contexto enviado pelo frontend
{
  current_plan_id: 'plan-123',
  investment_categories: [...]
}

// É armazenado em:
conversation_metadata = {
  current_plan_id: 'plan-123',
  investment_categories: [...]
}

// E usado em mensagens subsequentes (se não enviar novo contexto)
```

## 📝 Exemplo Completo de Integração

```typescript
// services/chatbotService.ts
export class ChatbotService {
  private baseUrl = 'http://localhost:8008';
  private currentContext: InvestmentContext | null = null;
  
  // Atualiza contexto quando necessário
  updateContext(context: InvestmentContext) {
    this.currentContext = context;
  }
  
  // Envia mensagem com contexto atual
  async sendMessage(userId: string, message: string) {
    const response = await fetch(`${this.baseUrl}/chatbot/process-message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        message,
        context: this.currentContext // Usa contexto atual
      })
    });
    
    return response.json();
  }
}

// Uso
const chatbot = new ChatbotService();

// Quando usuário entra na tela de investimentos
chatbot.updateContext({
  current_plan_id: 'plan-123',
  investment_categories: [...],
  available_investment_types: [...]
});

// Envia mensagem (usa contexto automaticamente)
const result = await chatbot.sendMessage('user-123', 'Adiciona 500 PETR4');
```

## 🚀 Próximos Passos

1. **Frontend**: Implementar envio de contexto quando disponível
2. **Testes**: Testar com e sem contexto
3. **Otimização**: Enviar apenas contexto relevante para reduzir payload

