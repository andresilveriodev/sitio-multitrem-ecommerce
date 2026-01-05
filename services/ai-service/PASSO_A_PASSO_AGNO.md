# 🚀 Guia de Instalação do Agno no AI-Service

Este guia detalha passo a passo como instalar e configurar o framework Agno para substituir a implementação atual do ai-service (NestJS + OpenAI SDK) por uma arquitetura baseada em agentes Python.

---

## 📋 Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Preparação do Ambiente](#2-preparação-do-ambiente)
3. [Instalação do Agno](#3-instalação-do-agno)
4. [Configuração das Chaves de API](#4-configuração-das-chaves-de-api)
5. [Criando o Primeiro Agente](#5-criando-o-primeiro-agente)
6. [Criando as Ferramentas (Tools)](#6-criando-as-ferramentas-tools)
7. [Configurando Memória e Storage](#7-configurando-memória-e-storage)
8. [Integrando com os Microsserviços](#8-integrando-com-os-microsserviços)
9. [Configurando o Playground](#9-configurando-o-playground)
10. [Testando a Implementação](#10-testando-a-implementação)
11. [Estrutura Final do Projeto](#11-estrutura-final-do-projeto)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Pré-requisitos

Antes de começar, certifique-se de ter instalado:

### Software Necessário
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **PostgreSQL** - Já configurado no projeto (porta 5432)
- **Redis** - Já configurado no projeto (porta 6379)

### Verificar Instalações

```powershell
# Verificar Python
python --version
# Esperado: Python 3.11.x ou superior

# Verificar pip
pip --version
```

### Chaves de API Necessárias
- **OpenAI API Key** - [Obter aqui](https://platform.openai.com/api-keys)
- **Groq API Key** (opcional, gratuito) - [Obter aqui](https://console.groq.com)
- **Tavily API Key** (opcional, para pesquisa web) - [Obter aqui](https://www.tavily.com)

---

## 2. Preparação do Ambiente

### 2.1 Criar Diretório do Agente Python

Dentro da pasta `ai-service`, vamos criar uma estrutura separada para o agente Python:

```powershell
# Navegar até o ai-service
cd services/ai-service

# Criar pasta para o agente Agno
mkdir agno-agent
cd agno-agent
```

### 2.2 Instalar o UV (Gerenciador de Pacotes Recomendado)

O Agno recomenda o uso do **UV** (Yuvi), um gerenciador de pacotes moderno e muito mais rápido que pip:

```powershell
# Instalar o UV
pip install uv
```

### 2.3 Inicializar o Projeto Python

```powershell
# Inicializar projeto com UV
uv init

# Isso criará os arquivos:
# - .gitignore
# - pyproject.toml
# - README.md
```

### 2.4 Criar Ambiente Virtual

```powershell
# Criar ambiente virtual isolado
uv venv

# Ativar o ambiente virtual (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Ativar o ambiente virtual (Windows CMD)
.\.venv\Scripts\activate.bat

# Ativar o ambiente virtual (Linux/Mac)
source .venv/bin/activate
```

> ⚠️ **Importante**: Sempre ative o ambiente virtual antes de trabalhar no projeto!

---

## 3. Instalação do Agno

### 3.1 Instalar o Framework Agno

```powershell
# Instalar Agno
uv add agno
```

### 3.2 Instalar Dependências Adicionais

```powershell
# OpenAI (modelo principal)
uv add openai

# Groq (alternativa gratuita)
uv add groq

# Para carregar variáveis de ambiente
uv add python-dotenv

# Para o Playground (interface web)
uv add fastapi uvicorn

# Para Storage com PostgreSQL (já temos no projeto)
uv add sqlalchemy psycopg2-binary

# Para requisições HTTP aos outros microsserviços
uv add httpx

# Para Tavily (pesquisa web - opcional)
uv add tavily-python
```

### 3.3 Verificar Instalação

Crie um arquivo `test_install.py`:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

print("✅ Agno instalado com sucesso!")
print(f"   Versão do Agent: {Agent.__module__}")
```

Execute:

```powershell
python test_install.py
```

---

## 4. Configuração das Chaves de API

### 4.1 Criar Arquivo .env

Crie o arquivo `.env` na pasta `agno-agent` com as configurações do projeto Sítio Multitrem:

```env
# ============================================
# CONFIGURAÇÃO DO AGNO - AI SERVICE
# Sítio Multitrem E-commerce
# ============================================

# ============================================
# OPENAI (Assistente IA - Principal)
# Obtenha em: https://platform.openai.com/api-keys
# ============================================
OPENAI_API_KEY=sk-sua-chave-openai-aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=500

# ============================================
# GROQ (Alternativa Gratuita)
# Obtenha em: https://console.groq.com
# ============================================
GROQ_API_KEY=gsk_sua-chave-groq-aqui

# ============================================
# TAVILY (Pesquisa Web - Opcional)
# Obtenha em: https://www.tavily.com
# ============================================
TAVILY_API_KEY=tvly-sua-chave-tavily-aqui

# ============================================
# URLS DOS MICROSSERVIÇOS
# ============================================
PRODUCT_SERVICE_URL=http://localhost:3001
CART_SERVICE_URL=http://localhost:3002
ORDER_SERVICE_URL=http://localhost:3003
PAYMENT_SERVICE_URL=http://localhost:3004
AUTH_SERVICE_URL=http://localhost:3005
WHATSAPP_SERVICE_URL=http://localhost:3006
AI_SERVICE_URL=http://localhost:3007
GATEWAY_URL=http://localhost:8000

# ============================================
# BANCO DE DADOS (PostgreSQL)
# ============================================
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=sitio_multitrem
DATABASE_USER=postgres
DATABASE_PASSWORD=sua_senha_aqui

# Alias para compatibilidade com Agno
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sitio_multitrem
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui

# ============================================
# REDIS (Cache e Filas)
# ============================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# ============================================
# KEYCLOAK (Autenticação - Se necessário)
# ============================================
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=sitio-multitrem
KEYCLOAK_CLIENT_ID=sitio-app
KEYCLOAK_CLIENT_SECRET=

# ============================================
# MERCADO PAGO (Pagamentos)
# Obtenha em: https://www.mercadopago.com.br/developers
# ============================================
MERCADO_PAGO_ACCESS_TOKEN=
MERCADO_PAGO_PUBLIC_KEY=
MERCADO_PAGO_WEBHOOK_SECRET=

# ============================================
# EVOLUTION API (WhatsApp)
# ============================================
EVOLUTION_API_URL=http://localhost:8081
EVOLUTION_API_KEY=
EVOLUTION_INSTANCE=sitio-multitrem

# ============================================
# CONFIGURAÇÕES DO SERVIDOR
# ============================================
NODE_ENV=development
PORT=3007
DEBUG=false
```

### 4.2 Portas dos Serviços (Referência)

| Serviço | Porta |
|---------|-------|
| Gateway | 8000 |
| Product Service | 3001 |
| Cart Service | 3002 |
| Order Service | 3003 |
| Payment Service | 3004 |
| Auth Service | 3005 |
| WhatsApp Service | 3006 |
| **AI Service (Agno)** | **3007** |
| Keycloak | 8080 |
| Evolution API | 8081 |
| PostgreSQL | 5432 |
| Redis | 6379 |

### 4.3 Como Obter as Chaves de API

#### OpenAI (Obrigatório)
1. Acesse https://platform.openai.com/api-keys
2. Crie uma conta ou faça login
3. Vá em **Settings → Billing** e adicione saldo (mínimo US$ 5)
4. Crie uma nova chave de API
5. Copie e cole no `.env`

#### Groq (Alternativa Gratuita)
1. Acesse https://console.groq.com
2. Crie uma conta gratuita
3. Gere uma API Key
4. Copie e cole no `.env`

> 💡 **Dica**: O Groq oferece acesso gratuito a modelos como Llama 3.3 70B com alta velocidade!

#### Mercado Pago (Para pagamentos)
1. Acesse https://www.mercadopago.com.br/developers
2. Crie uma aplicação
3. Copie o Access Token e Public Key
4. Cole no `.env`

### 4.2 Carregar Variáveis de Ambiente

Em todos os scripts Python, adicione no início:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 5. Criando o Primeiro Agente

### 5.1 Estrutura de Pastas

```
agno-agent/
├── .env
├── .venv/
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── main.py              # Entrada principal
│   ├── agents/
│   │   ├── __init__.py
│   │   └── sales_agent.py   # Agente de vendas
│   ├── tools/
│   │   ├── __init__.py
│   │   └── ecommerce_tools.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── sales_prompt.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
└── tests/
    └── test_agent.py
```

### 5.2 Criar o Agente de Vendas

Crie o arquivo `src/agents/sales_agent.py`:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.postgres import PostgresStorage
from dotenv import load_dotenv
import os

load_dotenv()

# Importar ferramentas (criaremos no próximo passo)
from src.tools.ecommerce_tools import (
    list_products,
    add_to_cart,
    remove_from_cart,
    view_cart,
    check_delivery_slots,
    create_order,
    generate_payment_link
)

# Importar prompt
from src.prompts.sales_prompt import SYSTEM_PROMPT

def create_sales_agent(visitor_id: str = None):
    """
    Cria uma instância do agente de vendas do Sítio Multitrem.
    
    Args:
        visitor_id: ID único do visitante para rastrear sessão
    
    Returns:
        Agent: Instância configurada do agente
    """
    
    # Configurar Storage (PostgreSQL) - Usando variáveis do projeto Sítio Multitrem
    db_user = os.getenv('DATABASE_USER', os.getenv('DB_USER', 'postgres'))
    db_pass = os.getenv('DATABASE_PASSWORD', os.getenv('DB_PASSWORD', ''))
    db_host = os.getenv('DATABASE_HOST', os.getenv('DB_HOST', 'localhost'))
    db_port = os.getenv('DATABASE_PORT', os.getenv('DB_PORT', '5432'))
    db_name = os.getenv('DATABASE_NAME', os.getenv('DB_NAME', 'sitio_multitrem'))
    
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    storage = PostgresStorage(
        table_name="agent_sessions",
        db_url=db_url
    )
    
    # Configurações do modelo via .env
    model_id = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '500'))
    
    # Criar agente
    agent = Agent(
        name="Assistente Sítio Multitrem",
        model=OpenAIChat(
            id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        ),
        tools=[
            list_products,
            add_to_cart,
            remove_from_cart,
            view_cart,
            check_delivery_slots,
            create_order,
            generate_payment_link
        ],
        instructions=SYSTEM_PROMPT,
        storage=storage,
        add_history_to_messages=True,
        num_history_runs=10,
        show_tool_calls=True,
        markdown=True,
        debug_mode=os.getenv('DEBUG', 'false').lower() == 'true'
    )
    
    return agent
```

### 5.3 Criar o Prompt do Sistema

Crie o arquivo `src/prompts/sales_prompt.py`:

```python
SYSTEM_PROMPT = """Você é o Assistente de Vendas do Sítio Multitrem, uma fazenda em Terezópolis de Goiás que vende hortaliças frescas colhidas no dia e ovos caipiras.

IDENTIDADE:
- Nome: Assistente do Sítio Multitrem
- Personalidade: simpático, prestativo, conhecedor dos produtos
- Tom: amigável, informal mas profissional
- Use emojis com moderação (🥬 🥚 🌿)

CONTEXTO:
- O Sítio Multitrem é uma fazenda em Terezópolis de Goiás
- Vende hortaliças frescas colhidas no dia e ovos caipiras
- Entregas: quarta a sábado, período da manhã
- WhatsApp: (62) 98122-5993
- Instagram: @sitio.multitrem

FUNÇÕES DISPONÍVEIS:
1. list_products - Listar produtos disponíveis
2. add_to_cart - Adicionar produto ao carrinho
3. remove_from_cart - Remover produto do carrinho
4. view_cart - Ver carrinho atual
5. check_delivery_slots - Verificar dias de entrega
6. create_order - Criar pedido
7. generate_payment_link - Gerar link de pagamento

RESTRIÇÕES:
- NÃO responder sobre assuntos não relacionados a vendas
- NÃO fornecer informações pessoais
- NÃO fazer promessas sobre prazos além do padrão
- Para outros assuntos: "Desculpe, só posso ajudar com pedidos 😊"

COMPORTAMENTO:
- Sempre confirmar antes de finalizar pedido
- Sugerir produtos complementares quando apropriado
- Informar sobre kits quando cliente pede vários itens individuais
- Ser proativo em ajudar o cliente a completar o pedido
"""
```

---

## 6. Criando as Ferramentas (Tools)

Crie o arquivo `src/tools/ecommerce_tools.py`:

```python
"""
Ferramentas do E-commerce para o Agente de Vendas.
Cada função é automaticamente disponibilizada ao agente através do decorator.
Configurado para o projeto Sítio Multitrem.
"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# URLs dos Microsserviços - Sítio Multitrem
# ============================================
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:3001')
CART_SERVICE_URL = os.getenv('CART_SERVICE_URL', 'http://localhost:3002')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://localhost:3003')
PAYMENT_SERVICE_URL = os.getenv('PAYMENT_SERVICE_URL', 'http://localhost:3004')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:3005')
WHATSAPP_SERVICE_URL = os.getenv('WHATSAPP_SERVICE_URL', 'http://localhost:3006')
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:8000')

# Variável global para armazenar visitor_id (será injetada pelo contexto)
_current_visitor_id = None

def set_visitor_id(visitor_id: str):
    """Define o visitor_id atual para as operações."""
    global _current_visitor_id
    _current_visitor_id = visitor_id

def get_visitor_id() -> str:
    """Retorna o visitor_id atual."""
    return _current_visitor_id or "anonymous"


def list_products(category: str = None) -> dict:
    """
    Lista produtos disponíveis no Sítio Multitrem.
    
    Args:
        category: Categoria opcional para filtrar (hortalicas, ovos, kits, combos)
    
    Returns:
        dict: Lista de produtos com nome, preço e disponibilidade
    """
    try:
        url = f"{PRODUCT_SERVICE_URL}/products"
        if category:
            url += f"?category={category}"
        
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        
        return {
            "success": True,
            "products": response.json()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def add_to_cart(product_id: int, quantity: int, selected_items: list = None) -> dict:
    """
    Adiciona um produto ao carrinho do cliente.
    
    Args:
        product_id: ID do produto a adicionar
        quantity: Quantidade desejada
        selected_items: Itens selecionados (para kits personalizáveis)
    
    Returns:
        dict: Carrinho atualizado com os itens
    """
    try:
        visitor_id = get_visitor_id()
        
        payload = {
            "productId": product_id,
            "quantity": quantity
        }
        if selected_items:
            payload["selectedItems"] = selected_items
        
        response = httpx.post(
            f"{CART_SERVICE_URL}/cart/{visitor_id}/items",
            json=payload,
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "cart": response.json(),
            "message": "Produto adicionado ao carrinho com sucesso!"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def remove_from_cart(product_id: int) -> dict:
    """
    Remove um produto do carrinho do cliente.
    
    Args:
        product_id: ID do produto a remover
    
    Returns:
        dict: Carrinho atualizado após remoção
    """
    try:
        visitor_id = get_visitor_id()
        
        response = httpx.delete(
            f"{CART_SERVICE_URL}/cart/{visitor_id}/items/{product_id}",
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "cart": response.json(),
            "message": "Produto removido do carrinho"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def view_cart() -> dict:
    """
    Mostra o carrinho atual do cliente com todos os itens e total.
    
    Returns:
        dict: Carrinho com itens, quantidades e valor total
    """
    try:
        visitor_id = get_visitor_id()
        
        response = httpx.get(
            f"{CART_SERVICE_URL}/cart/{visitor_id}",
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "cart": response.json()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def check_delivery_slots() -> dict:
    """
    Verifica os dias e horários disponíveis para entrega.
    Entregas disponíveis de quarta a sábado, período da manhã.
    
    Returns:
        dict: Lista de slots disponíveis com data e horário
    """
    try:
        response = httpx.get(
            f"{ORDER_SERVICE_URL}/delivery/slots",
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "slots": response.json()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_order(
    delivery_date: str,
    customer_name: str,
    customer_phone: str,
    customer_address: str
) -> dict:
    """
    Cria um novo pedido com os itens do carrinho.
    
    Args:
        delivery_date: Data de entrega no formato YYYY-MM-DD
        customer_name: Nome completo do cliente
        customer_phone: Telefone do cliente com DDD
        customer_address: Endereço completo para entrega
    
    Returns:
        dict: Pedido criado com número, itens e valor total
    """
    try:
        visitor_id = get_visitor_id()
        
        # Primeiro buscar o carrinho
        cart_response = httpx.get(
            f"{CART_SERVICE_URL}/cart/{visitor_id}",
            timeout=10.0
        )
        cart_response.raise_for_status()
        cart = cart_response.json()
        
        if not cart.get('items') or len(cart['items']) == 0:
            return {
                "success": False,
                "error": "Carrinho está vazio. Adicione produtos antes de criar o pedido."
            }
        
        # Criar o pedido
        order_payload = {
            "visitorId": visitor_id,
            "items": cart['items'],
            "deliveryDate": delivery_date,
            "customerName": customer_name,
            "customerPhone": customer_phone,
            "customerAddress": customer_address
        }
        
        response = httpx.post(
            f"{ORDER_SERVICE_URL}/orders",
            json=order_payload,
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "order": response.json(),
            "message": "Pedido criado com sucesso!"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def generate_payment_link(order_id: int, method: str) -> dict:
    """
    Gera link ou QR Code de pagamento para o pedido.
    
    Args:
        order_id: ID do pedido
        method: Método de pagamento ('pix' ou 'boleto')
    
    Returns:
        dict: Link de pagamento ou QR Code Pix
    """
    try:
        if method not in ['pix', 'boleto']:
            return {
                "success": False,
                "error": "Método inválido. Use 'pix' ou 'boleto'."
            }
        
        response = httpx.post(
            f"{PAYMENT_SERVICE_URL}/payments/{method}",
            json={"orderId": order_id},
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "payment": response.json(),
            "message": f"Link de pagamento {method.upper()} gerado com sucesso!"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

---

## 7. Configurando Memória e Storage

### 7.1 Storage com PostgreSQL

O Storage persiste o histórico de sessões. Crie `src/config/storage.py`:

```python
from agno.storage.postgres import PostgresStorage
import os
from dotenv import load_dotenv

load_dotenv()

def get_postgres_storage():
    """
    Configura o Storage PostgreSQL para persistir sessões.
    Compatível com as variáveis de ambiente do projeto Sítio Multitrem.
    """
    db_user = os.getenv('DATABASE_USER', os.getenv('DB_USER', 'postgres'))
    db_pass = os.getenv('DATABASE_PASSWORD', os.getenv('DB_PASSWORD', ''))
    db_host = os.getenv('DATABASE_HOST', os.getenv('DB_HOST', 'localhost'))
    db_port = os.getenv('DATABASE_PORT', os.getenv('DB_PORT', '5432'))
    db_name = os.getenv('DATABASE_NAME', os.getenv('DB_NAME', 'sitio_multitrem'))
    
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    return PostgresStorage(
        table_name="agent_sessions",
        db_url=db_url
    )
```

### 7.2 Memória Persistente (Opcional)

Para lembrar informações do usuário entre sessões. Crie `src/config/memory.py`:

```python
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.models.openai import OpenAIChat
import os
from dotenv import load_dotenv

load_dotenv()

def get_agent_memory():
    """
    Configura a memória persistente para o agente.
    Permite lembrar informações importantes sobre o usuário.
    Compatível com as variáveis de ambiente do projeto Sítio Multitrem.
    """
    db_user = os.getenv('DATABASE_USER', os.getenv('DB_USER', 'postgres'))
    db_pass = os.getenv('DATABASE_PASSWORD', os.getenv('DB_PASSWORD', ''))
    db_host = os.getenv('DATABASE_HOST', os.getenv('DB_HOST', 'localhost'))
    db_port = os.getenv('DATABASE_PORT', os.getenv('DB_PORT', '5432'))
    db_name = os.getenv('DATABASE_NAME', os.getenv('DB_NAME', 'sitio_multitrem'))
    
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # Usar modelo configurado no .env ou padrão
    model_id = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    return Memory(
        model=OpenAIChat(id=model_id),
        db=PostgresMemoryDb(
            table_name="agent_memories",
            db_url=db_url
        )
    )
```

---

## 8. Integrando com os Microsserviços

### 8.1 Criar API FastAPI

Crie o arquivo `src/main.py`:

```python
"""
API Principal do AI-Service com Agno.
Substitui a implementação NestJS por Python/FastAPI.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

from src.agents.sales_agent import create_sales_agent
from src.tools.ecommerce_tools import set_visitor_id

app = FastAPI(
    title="AI Service - Sítio Multitrem",
    description="Serviço de IA com Agno para o assistente de vendas",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    visitorId: str
    message: str
    conversationHistory: Optional[List[dict]] = None
    source: Optional[str] = "web"


class ChatResponse(BaseModel):
    response: str
    actions: List[dict] = []
    cart: Optional[dict] = None
    paymentLink: Optional[str] = None


@app.post("/ai/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Processa uma mensagem do usuário e retorna a resposta do agente.
    """
    try:
        # Definir visitor_id para as tools
        set_visitor_id(request.visitorId)
        
        # Criar agente
        agent = create_sales_agent(request.visitorId)
        
        # Processar mensagem
        result = agent.run(
            request.message,
            user_id=request.visitorId
        )
        
        return ChatResponse(
            response=result.content or "Desculpe, não consegui processar sua mensagem.",
            actions=[],  # TODO: extrair ações das tool calls
            cart=None,
            paymentLink=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ai/conversation/{visitor_id}")
async def get_conversation_history(visitor_id: str):
    """
    Retorna o histórico de conversas do visitante.
    """
    try:
        agent = create_sales_agent(visitor_id)
        # TODO: implementar busca de histórico do storage
        return {"history": [], "visitorId": visitor_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {"status": "healthy", "service": "ai-service-agno"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3007))
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
```

---

## 9. Configurando o Playground

### 9.1 Criar Arquivo do Playground

Crie `src/playground.py`:

```python
"""
Agno Playground - Interface visual para desenvolvimento e testes.
"""

from agno.playground import Playground, serve_playground_app
from src.agents.sales_agent import create_sales_agent
from dotenv import load_dotenv

load_dotenv()

# Criar agente para o playground
agent = create_sales_agent("playground-user")

# Criar app do playground
app = Playground(agents=[agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("src.playground:app", reload=True)
```

### 9.2 Executar o Playground

```powershell
# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Executar playground
python -m src.playground
```

Acesse: `http://localhost:7777/v1`

> ⚠️ **Importante**: Use Chrome, Edge ou Firefox. Brave e Safari podem bloquear funcionalidades.

---

## 10. Testando a Implementação

### 10.1 Teste Básico do Agente

Crie `tests/test_agent.py`:

```python
from src.agents.sales_agent import create_sales_agent
from dotenv import load_dotenv

load_dotenv()

def test_basic_conversation():
    """Testa uma conversa básica com o agente."""
    agent = create_sales_agent("test-user")
    
    # Teste 1: Saudação
    response = agent.run("Olá, bom dia!")
    print(f"Resposta 1: {response.content}\n")
    
    # Teste 2: Listar produtos
    response = agent.run("Quais produtos vocês têm?")
    print(f"Resposta 2: {response.content}\n")
    
    # Teste 3: Pergunta sobre entrega
    response = agent.run("Quais dias vocês entregam?")
    print(f"Resposta 3: {response.content}\n")

if __name__ == "__main__":
    test_basic_conversation()
```

### 10.2 Executar Testes

```powershell
python tests/test_agent.py
```

### 10.3 Testar via API

```powershell
# Iniciar servidor
python -m src.main

# Em outro terminal, testar
curl -X POST http://localhost:3007/ai/chat `
  -H "Content-Type: application/json" `
  -d '{"visitorId": "test123", "message": "Quais produtos vocês têm?"}'
```

---

## 11. Estrutura Final do Projeto

```
ai-service/
├── agno-agent/                    # Nova pasta do agente Agno
│   ├── .env                       # Variáveis de ambiente
│   ├── .venv/                     # Ambiente virtual Python
│   ├── pyproject.toml             # Configuração do projeto
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                # API FastAPI
│   │   ├── playground.py          # Interface visual
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   └── sales_agent.py     # Agente de vendas
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   └── ecommerce_tools.py # Ferramentas do e-commerce
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   └── sales_prompt.py    # System prompt
│   │   └── config/
│   │       ├── __init__.py
│   │       ├── settings.py
│   │       ├── storage.py
│   │       └── memory.py
│   └── tests/
│       └── test_agent.py
├── src/                           # Código NestJS antigo (pode ser removido após migração)
├── package.json
└── README.md
```

---

## 12. Troubleshooting

### Erro: "OPENAI_API_KEY not found"
```powershell
# Verificar se o .env está sendo carregado
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"
```

### Erro: "Connection refused" aos microsserviços
- Verifique se os outros serviços estão rodando (cart-service, product-service, etc.)
- Confirme as URLs no arquivo `.env`

### Erro: "psycopg2 not found"
```powershell
uv add psycopg2-binary
```

### Playground não abre
- Use Chrome, Edge ou Firefox
- Adicione `/v1` ao final da URL
- Verifique se a porta 7777 não está em uso

### Modelo não responde
- Verifique se a chave da OpenAI tem saldo
- Teste com Groq (gratuito) alterando o model:

```python
from agno.models.groq import Groq

agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    # ...
)
```

---

## 🎉 Próximos Passos

Após concluir a instalação:

1. **Adicionar RAG/Knowledge** - Para consultar documentos (cardápio, políticas)
2. **Implementar Memória** - Para lembrar preferências do cliente
3. **Criar Time de Agentes** - Para separar responsabilidades (vendas, suporte, entregas)
4. **Configurar Monitoramento** - Logs e métricas de uso

---

## 📚 Referências

- [Documentação Oficial do Agno](https://docs.agno.com)
- [GitHub do Agno](https://github.com/agno-agi/agno)
- [Curso Asimov Academy](https://asimov.academy)

---

> 📝 **Nota**: Este guia foi criado para o projeto Sítio Multitrem E-commerce.
> Última atualização: Janeiro 2026

