# 📱 Integração Frontend - Chatbot Service

## 🎯 Visão Geral

O **Chatbot Service** retorna respostas estruturadas que podem conter **ações** para o frontend executar. O frontend deve **interpretar e executar** essas ações localmente, sem fazer requisições HTTP adicionais.

## 🔄 Fluxo de Comunicação

```
Frontend → POST /chatbot/process-message → Chatbot Service
Frontend ← Response com frontend_action ← Chatbot Service
Frontend → Executa ação localmente
```

## 🤖 Configurando Provedor de IA (OpenAI, DeepSeek, Ollama)

### Visão Geral

O Chatbot Service suporta múltiplos provedores de IA. Você pode especificar qual provedor usar em cada requisição ou usar o provedor padrão configurado.

### Provedores Disponíveis

- **OpenAI** (`openai`) - OpenAI GPT
- **DeepSeek** (`deepseek`) - DeepSeek AI
- **Ollama** (`ollama`) - Ollama (local)

### 1. Usando o Endpoint `/chatbot/chat`

Este endpoint é mais simples para chat direto:

```typescript
interface ChatRequest {
  conversation_id: number;
  message: string;
  provider?: string;  // 'openai' | 'deepseek' | 'ollama'
  model?: string;     // ex: 'gpt-4o-mini'
}

interface ChatResponse {
  user_message: string;
  ai_response: string;
  conversation_id: number;
}

// Exemplo de uso
const sendMessage = async (
  conversationId: number,
  message: string,
  provider: string = 'openai',
  model: string = 'gpt-4o-mini'
) => {
  const response = await fetch('http://localhost:8012/chatbot/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
      provider,
      model
    })
  });

  const data: ChatResponse = await response.json();
  return data.ai_response;
};
```

### 2. Usando o Endpoint `/chatbot/process-message` com Provider

O endpoint principal também suporta provider e model:

```typescript
interface ProcessMessageRequest {
  user_id: string;
  message: string;
  provider?: string;
  model?: string;
  session_id?: string;
}

// Exemplo de uso
const processMessage = async (
  userId: string,
  message: string,
  provider: string = 'openai',
  model: string = 'gpt-4o-mini'
) => {
  const response = await fetch('http://localhost:8008/chatbot/process-message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      message,
      provider,
      model
    })
  });

  const data: ChatbotResponse = await response.json();
  return data;
};
```

### 3. Listar Provedores Disponíveis

Antes de usar, você pode verificar quais provedores estão disponíveis:

```typescript
interface Provider {
  name: string;
  available: boolean;
  models: string[];
  description: string;
}

interface ProvidersResponse {
  providers: Provider[];
  default_provider: string;
  supported_providers: string[];
}

const getAvailableProviders = async (): Promise<ProvidersResponse> => {
  const response = await fetch('http://localhost:8012/ai/providers');
  const data: ProvidersResponse = await response.json();
  return data;
};

// Uso
const providers = await getAvailableProviders();
console.log('Provedores disponíveis:', providers.providers);
console.log('Provedor padrão:', providers.default_provider);
```

### 4. Hook React para Chat

```typescript
import { useState, useCallback } from 'react';

interface UseChatOptions {
  conversationId: number;
  defaultProvider?: string;
  defaultModel?: string;
}

export function useChat({
  conversationId,
  defaultProvider = 'openai',
  defaultModel = 'gpt-4o-mini'
}: UseChatOptions) {
  const [messages, setMessages] = useState<Array<{
    role: 'user' | 'assistant';
    content: string;
  }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (
    message: string,
    provider: string = defaultProvider,
    model: string = defaultModel
  ) => {
    setLoading(true);
    setError(null);

    try {
      // Adiciona mensagem do usuário
      setMessages(prev => [...prev, { role: 'user', content: message }]);

      const response = await fetch('http://localhost:8012/chatbot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          message,
          provider,
          model
        })
      });

      if (!response.ok) {
        throw new Error(`Erro: ${response.statusText}`);
      }

      const data: ChatResponse = await response.json();

      // Adiciona resposta da IA
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.ai_response
      }]);

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [conversationId, defaultProvider, defaultModel]);

  return {
    messages,
    loading,
    error,
    sendMessage
  };
}
```

### 5. Componente React Completo com Seletor de Provedor

```typescript
import React, { useState, useEffect } from 'react';
import { useChat } from '@/hooks/useChat';

function ChatWithProviderSelector() {
  const [conversationId] = useState(1);
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [selectedModel, setSelectedModel] = useState('gpt-4o-mini');
  const [providers, setProviders] = useState<ProvidersResponse | null>(null);
  const [inputMessage, setInputMessage] = useState('');

  const { messages, loading, error, sendMessage } = useChat({
    conversationId,
    defaultProvider: selectedProvider,
    defaultModel: selectedModel
  });

  // Carrega provedores disponíveis
  useEffect(() => {
    const loadProviders = async () => {
      try {
        const data = await getAvailableProviders();
        setProviders(data);
      } catch (err) {
        console.error('Erro ao carregar provedores:', err);
      }
    };
    loadProviders();
  }, []);

  const handleSend = async () => {
    if (!inputMessage.trim()) return;

    try {
      await sendMessage(inputMessage, selectedProvider, selectedModel);
      setInputMessage('');
    } catch (err) {
      console.error('Erro ao enviar mensagem:', err);
    }
  };

  // Filtra modelos do provedor selecionado
  const availableModels = providers?.providers.find(
    p => p.name === selectedProvider
  )?.models || [];

  return (
    <div className="chat-container">
      {/* Seletor de Provedor */}
      <div className="provider-selector">
        <label>
          Provedor:
          <select
            value={selectedProvider}
            onChange={(e) => {
              setSelectedProvider(e.target.value);
              // Reseta modelo quando troca provedor
              const newProvider = providers?.providers.find(
                p => p.name === e.target.value
              );
              if (newProvider?.models.length) {
                setSelectedModel(newProvider.models[0]);
              }
            }}
          >
            {providers?.supported_providers.map(provider => (
              <option key={provider} value={provider}>
                {provider}
              </option>
            ))}
          </select>
        </label>

        <label>
          Modelo:
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={!availableModels.length}
          >
            {availableModels.map(model => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Mensagens */}
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <strong>{msg.role === 'user' ? 'Você' : 'IA'}:</strong>
            <p>{msg.content}</p>
          </div>
        ))}
        {loading && <div className="loading">Digitando...</div>}
        {error && <div className="error">Erro: {error}</div>}
      </div>

      {/* Input */}
      <div className="input-area">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Digite sua mensagem..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !inputMessage.trim()}>
          Enviar
        </button>
      </div>
    </div>
  );
}
```

### 6. Armazenar Preferência do Usuário

Você pode salvar a preferência do usuário no localStorage ou no backend:

```typescript
// Salvar preferência
const saveUserPreference = (provider: string, model: string) => {
  localStorage.setItem('ai_provider', provider);
  localStorage.setItem('ai_model', model);
};

// Carregar preferência
const loadUserPreference = () => {
  return {
    provider: localStorage.getItem('ai_provider') || 'openai',
    model: localStorage.getItem('ai_model') || 'gpt-4o-mini'
  };
};

// Uso no componente
const { provider, model } = loadUserPreference();
const [selectedProvider, setSelectedProvider] = useState(provider);
const [selectedModel, setSelectedModel] = useState(model);

// Salvar quando mudar
useEffect(() => {
  saveUserPreference(selectedProvider, selectedModel);
}, [selectedProvider, selectedModel]);
```

### 7. Exemplo com TypeScript Strict

```typescript
// types/chat.ts
export type AIProvider = 'openai' | 'deepseek' | 'ollama';

export interface ChatRequest {
  conversation_id: number;
  message: string;
  provider?: AIProvider;
  model?: string;
}

export interface ChatResponse {
  user_message: string;
  ai_response: string;
  conversation_id: number;
}

// services/chatService.ts
import { ChatRequest, ChatResponse, AIProvider } from '@/types/chat';

export class ChatService {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8012') {
    this.baseUrl = baseUrl;
  }

  async sendMessage(
    request: ChatRequest
  ): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/chatbot/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getProviders() {
    const response = await fetch(`${this.baseUrl}/ai/providers`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
}
```

### 8. Tratamento de Erros Específicos

```typescript
const sendMessageWithErrorHandling = async (
  conversationId: number,
  message: string,
  provider: string = 'openai',
  model: string = 'gpt-4o-mini'
) => {
  try {
    const response = await fetch('http://localhost:8012/chatbot/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message,
        provider,
        model
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      // Tratamento específico de erros
      if (response.status === 400) {
        throw new Error(errorData.detail || 'Requisição inválida');
      } else if (response.status === 500) {
        throw new Error('Erro interno do servidor. Tente novamente.');
      } else if (response.status === 404) {
        throw new Error('Modelo não encontrado. Verifique o nome do modelo.');
      }
      
      throw new Error(`Erro: ${response.statusText}`);
    }

    const data: ChatResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Erro de conexão. Verifique se o servidor está rodando.');
    }
    throw error;
  }
};
```

### 9. Comparação Rápida de Provedores

```typescript
const providerComparison = {
  openai: {
    speed: '⚡⚡ Rápido',
    cost: '💰💰 Pago',
    quality: '⭐⭐⭐⭐ Muito Bom',
    recommended: true,
    bestFor: 'Tarefas complexas, quando qualidade é prioridade'
  },
  deepseek: {
    speed: '⚡⚡⚡ Muito Rápido',
    cost: '💰💰 Muito Barato',
    quality: '⭐⭐⭐ Bom',
    recommended: false,
    bestFor: 'Alternativa barata ao OpenAI'
  },
  ollama: {
    speed: '⚡ Lento',
    cost: '💰💰💰 Gratuito (local)',
    quality: '⭐⭐⭐ Bom',
    recommended: false,
    bestFor: 'Uso local, privacidade total'
  }
};
```

### ✅ Resumo: Como Usar Provedores de IA no Frontend

1. **Endpoint Simples**: Use `/chatbot/chat` para chat direto
2. **Especifique Provider**: Passe `provider: 'openai'` (ou outro provedor) na requisição
3. **Especifique Model**: Passe `model: 'gpt-4o-mini'` (ou outro modelo)
4. **Liste Provedores**: Use `/ai/providers` para ver opções disponíveis
5. **Salve Preferências**: Armazene a escolha do usuário no localStorage
6. **Trate Erros**: Implemente tratamento de erros específicos

**Exemplo Mínimo:**
```typescript
const response = await fetch('http://localhost:8012/chatbot/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    conversation_id: 1,
    message: 'Olá!',
    provider: 'openai',
    model: 'gpt-4o-mini'
  })
});
const { ai_response } = await response.json();
```

## 📋 Formato da Resposta

### Resposta Padrão (sem ação)

```json
{
  "success": true,
  "response": {
    "response": "Olá! Como posso ajudá-lo hoje?",
    "confidence": 0.95,
    "category": "greeting"
  },
  "metadata": {
    "processing_time": 0.02,
    "requires_ai": false,
    "cache_hit": false,
    "auto_response": true
  }
}
```

### Resposta com Comando Executado (com ação)

```json
{
  "success": true,
  "response": {
    "response": "Box de cotação para PETR4 criado com sucesso",
    "command_id": "add_multibox",
    "command_result": {
      "symbol": "PETR4",
      "action": "add_multibox",
      "target": "frontend"
    },
    "action": "command_executed",
    "frontend_action": {
      "type": "add_multibox",
      "parameters": {
        "symbol": "PETR4"
      },
      "command_id": "add_multibox"
    }
  },
  "metadata": {
    "processing_time": 0.05,
    "requires_ai": false,
    "cache_hit": false,
    "command_executed": true,
    "command_id": "add_multibox"
  }
}
```

### Resposta com Confirmação Necessária

```json
{
  "success": true,
  "response": {
    "response": "Comando aguardando confirmação. Confirmação necessária.",
    "command_id": "add_multibox",
    "confirmation_required": true,
    "confirmation": {
      "id": "confirmation-uuid",
      "message": "Criar box de cotação para PETR4?",
      "command": "add_multibox",
      "parameters": {
        "symbol": "PETR4"
      }
    },
    "frontend_action": {
      "type": "await_confirmation",
      "command_id": "add_multibox",
      "confirmation_id": "confirmation-uuid",
      "parameters": {
        "symbol": "PETR4"
      }
    }
  },
  "metadata": {
    "command_executed": true,
    "command_id": "add_multibox"
  }
}
```

## 🎬 Ações Disponíveis

### 1. **add_multibox** - Criar Box de Cotação

**Quando aparece:** Usuário solicita criar/abrir um box de cotação

**Parâmetros:**
```typescript
{
  symbol?: string  // Opcional: símbolo do ativo (ex: "PETR4")
}
```

**Exemplo de Implementação:**
```typescript
if (frontend_action?.type === "add_multibox") {
  const { symbol } = frontend_action.parameters;
  
  // Criar novo box de cotação
  dispatch(createMultibox({ symbol: symbol || null }));
  
  // Ou navegar para página de box
  if (symbol) {
    router.push(`/multibox/${symbol}`);
  } else {
    router.push('/multibox/new');
  }
}
```

### 2. **show_position** - Mostrar Posição

**Quando aparece:** Usuário solicita ver posição de um ativo

**Parâmetros:**
```typescript
{
  symbol: string  // Obrigatório: símbolo do ativo
}
```

**Exemplo de Implementação:**
```typescript
if (frontend_action?.type === "show_position") {
  const { symbol } = frontend_action.parameters;
  
  // Abrir modal/aba com posição do ativo
  dispatch(showPosition({ symbol }));
  
  // Ou navegar para página de posições
  router.push(`/positions/${symbol}`);
}
```

### 3. **show_book_offers** - Mostrar Book de Ofertas

**Quando aparece:** Usuário solicita ver book de ofertas

**Parâmetros:**
```typescript
{
  symbol: string  // Obrigatório: símbolo do ativo
}
```

**Exemplo de Implementação:**
```typescript
if (frontend_action?.type === "show_book_offers") {
  const { symbol } = frontend_action.parameters;
  
  // Abrir book de ofertas
  dispatch(openBookOffers({ symbol }));
  
  // Ou navegar para página de book
  router.push(`/book/${symbol}`);
}
```

### 4. **show_watchlist** - Mostrar Watchlist

**Quando aparece:** Usuário solicita ver lista de observação

**Parâmetros:**
```typescript
{}  // Sem parâmetros
```

**Exemplo de Implementação:**
```typescript
if (frontend_action?.type === "show_watchlist") {
  // Abrir/focar na watchlist
  dispatch(showWatchlist());
  
  // Ou navegar para página de watchlist
  router.push('/watchlist');
}
```

### 5. **add_watchlist** - Adicionar ao Watchlist

**Quando aparece:** Usuário solicita adicionar ativo ao watchlist

**Parâmetros:**
```typescript
{
  symbol: string  // Obrigatório: símbolo do ativo
}
```

**Exemplo de Implementação:**
```typescript
if (frontend_action?.type === "add_watchlist") {
  const { symbol } = frontend_action.parameters;
  
  // Adicionar ao watchlist
  dispatch(addToWatchlist({ symbol }));
  
  // Mostrar feedback
  toast.success(`Ativo ${symbol} adicionado ao watchlist`);
}
```

### 6. **create_analysis_tab** - Criar Aba de Análise

**Quando aparece:** Usuário solicita criar aba de análise

**Parâmetros:**
```typescript
{
  symbol: string  // Obrigatório: símbolo do ativo
}
```

**Exemplo de Implementação:**
```typescript
if (frontend_action?.type === "create_analysis_tab") {
  const { symbol } = frontend_action.parameters;
  
  // Criar nova aba de análise
  dispatch(createAnalysisTab({ symbol }));
  
  // Ou navegar para página de análise
  router.push(`/analysis/${symbol}`);
}
```

### 7. **await_confirmation** - Aguardar Confirmação

**Quando aparece:** Comando requer confirmação do usuário

**Parâmetros:**
```typescript
{
  command_id: string,
  confirmation_id: string,
  parameters: Record<string, any>
}
```

**Exemplo de Implementação:**
```typescript
if (frontend_action?.type === "await_confirmation") {
  const { command_id, confirmation_id, parameters } = frontend_action;
  
  // Mostrar modal de confirmação
  showConfirmationModal({
    title: "Confirmar Ação",
    message: response.response,
    onConfirm: async () => {
      // Enviar confirmação para o backend
      await confirmCommand({
        confirmation_id,
        user_id: currentUser.id
      });
    },
    onCancel: () => {
      // Cancelar comando
      cancelCommand({ confirmation_id });
    }
  });
}
```

## 💻 Implementação TypeScript/React

### Interface TypeScript

```typescript
interface ChatbotResponse {
  success: boolean;
  response: {
    response: string;
    command_id?: string;
    command_result?: Record<string, any>;
    action?: string;
    frontend_action?: FrontendAction;
    confirmation_required?: boolean;
    confirmation?: {
      id: string;
      message: string;
      command: string;
      parameters: Record<string, any>;
    };
  };
  metadata: {
    processing_time: number;
    requires_ai: boolean;
    cache_hit: boolean;
    command_executed?: boolean;
    command_id?: string;
  };
}

interface FrontendAction {
  type: 
    | "add_multibox"
    | "show_position"
    | "show_book_offers"
    | "show_watchlist"
    | "add_watchlist"
    | "create_analysis_tab"
    | "await_confirmation";
  parameters: Record<string, any>;
  command_id?: string;
  confirmation_id?: string;
}
```

### Hook React para Processar Respostas

```typescript
import { useDispatch } from 'react-redux';
import { useRouter } from 'next/router';

export function useChatbotActions() {
  const dispatch = useDispatch();
  const router = useRouter();

  const executeFrontendAction = (
    frontendAction: FrontendAction | undefined,
    responseMessage: string
  ) => {
    if (!frontendAction) return;

    switch (frontendAction.type) {
      case "add_multibox":
        const { symbol } = frontendAction.parameters;
        if (symbol) {
          router.push(`/multibox/${symbol}`);
        } else {
          router.push('/multibox/new');
        }
        break;

      case "show_position":
        dispatch(showPosition({ symbol: frontendAction.parameters.symbol }));
        break;

      case "show_book_offers":
        dispatch(openBookOffers({ symbol: frontendAction.parameters.symbol }));
        break;

      case "show_watchlist":
        router.push('/watchlist');
        break;

      case "add_watchlist":
        dispatch(addToWatchlist({ symbol: frontendAction.parameters.symbol }));
        toast.success(`Ativo ${frontendAction.parameters.symbol} adicionado ao watchlist`);
        break;

      case "create_analysis_tab":
        router.push(`/analysis/${frontendAction.parameters.symbol}`);
        break;

      case "await_confirmation":
        // Mostrar modal de confirmação
        showConfirmationModal({
          confirmation: frontendAction,
          onConfirm: () => confirmCommand(frontendAction.confirmation_id),
          onCancel: () => cancelCommand(frontendAction.confirmation_id)
        });
        break;

      default:
        console.warn(`Ação desconhecida: ${frontendAction.type}`);
    }
  };

  return { executeFrontendAction };
}
```

### Uso no Componente de Chat

```typescript
import { useChatbotActions } from '@/hooks/useChatbotActions';

function ChatInterface() {
  const { executeFrontendAction } = useChatbotActions();
  const [messages, setMessages] = useState([]);

  const handleSendMessage = async (message: string) => {
    const response = await fetch('http://localhost:8008/chatbot/process-message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.id,
        message
      })
    });

    const data: ChatbotResponse = await response.json();

    if (data.success) {
      // Adicionar mensagem à conversa
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response.response
      }]);

      // Executar ação se presente
      if (data.response.frontend_action) {
        executeFrontendAction(
          data.response.frontend_action,
          data.response.response
        );
      }
    }
  };

  return (
    // ... UI do chat
  );
}
```

## ✅ Boas Práticas

### 1. **Sempre verificar `frontend_action` antes de executar**

```typescript
if (response.response.frontend_action) {
  executeFrontendAction(response.response.frontend_action);
}
```

### 2. **Tratar confirmações adequadamente**

```typescript
if (response.response.confirmation_required) {
  showConfirmationModal(response.response.confirmation);
}
```

### 3. **Validar parâmetros antes de usar**

```typescript
const { symbol } = frontend_action.parameters;
if (!symbol) {
  console.error("Símbolo não fornecido");
  return;
}
```

### 4. **Mostrar feedback ao usuário**

```typescript
// Mostrar mensagem do backend
toast.success(response.response.response);

// Executar ação
executeFrontendAction(response.response.frontend_action);
```

### 5. **Tratar erros graciosamente**

```typescript
try {
  if (frontend_action) {
    executeFrontendAction(frontend_action);
  }
} catch (error) {
  console.error("Erro ao executar ação:", error);
  toast.error("Erro ao executar ação");
}
```

## 🔒 Segurança

- ✅ O frontend **sempre** recebe dados **validados** do backend
- ✅ Ações são **sugeridas**, não **executadas automaticamente**
- ✅ Confirmações são **obrigatórias** para comandos críticos
- ✅ Parâmetros são **sanitizados** pelo backend antes do envio

## 📝 Endpoint de Confirmação

Para confirmar comandos que requerem confirmação:

```typescript
// POST /chatbot/confirm-command (a ser implementado)
const confirmCommand = async (confirmationId: string) => {
  const response = await fetch(
    `http://localhost:8008/chatbot/confirm-command/${confirmationId}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.id,
        confirmed: true
      })
    }
  );

  const data = await response.json();
  return data;
};
```

## 🎯 Resumo

1. **Backend retorna** → Resposta estruturada com `frontend_action`
2. **Frontend interpreta** → Lê `frontend_action.type` e `parameters`
3. **Frontend executa** → Executa ação localmente (navegação, dispatch, etc.)
4. **Não há requisições adicionais** → Tudo é feito com uma única requisição

Essa abordagem é **mais segura, rápida e eficiente** que fazer o backend chamar o frontend via HTTP.

