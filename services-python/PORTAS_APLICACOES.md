# Portas das Aplicações Python

Este documento organiza as portas utilizadas por cada aplicação Python **implementada** no projeto, seguindo uma sequência lógica.

## 📋 Resumo das Portas

| Porta | Serviço | Diretório | Status | Descrição |
|-------|---------|-----------|--------|-----------|
| **8000** | Gateway Service | `0_gateway/` | ✅ Implementado | Gateway principal que roteia requisições para outros serviços |
| **8001** | User Service | `1_users/` | ✅ Implementado | Serviço de autenticação e gerenciamento de usuários |
| **8002** | Chatbot Service | `3_chatbot/bot_operations/` | ✅ Implementado | Serviço de chatbot - middleware entre frontend e AI Service |
| **8003** | AI Service | `2_artificial_intelligence/ai_operations/` | ✅ Implementado | Serviço de inteligência artificial |
| **8004-8019** | Reservado | - | 🔜 Reservado | Portas reservadas para serviços futuros |
| **8020** | WhatsApp Service | `4_messages_apps/whatsapp/` | 🔜 Planejado | Serviço de integração com WhatsApp |
| **8021** | Telegram Service | `4_messages_apps/telegram_operations/` | ✅ Implementado | Serviço de integração com Telegram |
| **8022-8029** | Outros Message Apps | `4_messages_apps/` | 🔜 Reservado | Portas reservadas para futuros serviços de mensagens |

---

## 🎯 Organização Lógica das Portas

### Serviços Core (8000-8019)
- **8000**: Gateway Service
- **8001**: User Service
- **8002**: Chatbot Service
- **8003**: AI Service
- **8004-8019**: Reservado para serviços futuros

### Serviços de Mensagens (8020-8029)
- **8020**: WhatsApp Service
- **8021**: Telegram Service
- **8022-8029**: Reservado para futuros serviços de mensagens (Instagram, Facebook Messenger, Discord, etc.)

---

## 🔍 Detalhamento por Serviço

### 1. Gateway Service
- **Porta:** `8000`
- **Diretório:** `0_gateway/`
- **Arquivo Principal:** `0_gateway/main.py`
- **Arquivo de Configuração:** `0_gateway/config.py`
- **URL Padrão:** `http://localhost:8000`
- **Documentação:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`
- **Variável de Ambiente:** `PORT` (padrão: `8000`)
- **Descrição:** Gateway principal que atua como ponto de entrada único, roteando requisições para os demais microserviços. Inclui autenticação, CORS, circuit breaker e load balancing.

### 2. User Service
- **Porta:** `8001`
- **Diretório:** `1_users/`
- **Arquivo Principal:** `1_users/main.py`
- **Arquivo de Configuração:** `1_users/config.py`
- **URL Padrão:** `http://localhost:8001`
- **Base Path:** `/api/v1`
- **Documentação:** `http://localhost:8001/docs`
- **Variável de Ambiente:** `PORT` (padrão: `8001`)
- **Descrição:** Serviço de autenticação e autorização com integração ao Keycloak. Gerencia usuários, perfis, preferências e ACL (Access Control List).

### 3. Chatbot Service
- **Porta:** `8002`
- **Diretório:** `3_chatbot/bot_operations/`
- **Arquivo Principal:** `3_chatbot/bot_operations/main.py`
- **Arquivo de Configuração:** `3_chatbot/bot_operations/config.py`
- **URL Padrão:** `http://localhost:8002`
- **Base Path:** `/api/v1`
- **Documentação:** `http://localhost:8002/docs` (se DEBUG=true)
- **Variável de Ambiente:** `PORT` (padrão: `8002`)
- **Descrição:** Middleware inteligente entre o frontend e o AI Service. Gerencia contexto de conversas, cache, filtros de mensagens e otimização de custos.
- **Dependências:**
  - AI Service (porta 8003)

### 4. AI Service (Artificial Intelligence Service)
- **Porta:** `8003`
- **Diretório:** `2_artificial_intelligence/ai_operations/`
- **Arquivo Principal:** `2_artificial_intelligence/ai_operations/main.py`
- **Arquivo de Configuração:** `2_artificial_intelligence/ai_operations/app/config.py`
- **URL Padrão:** `http://localhost:8003`
- **Base Path:** `/api/v1`
- **Documentação:** `http://localhost:8003/docs`
- **Health Check:** `http://localhost:8003/health`
- **Variável de Ambiente:** `AI_SERVICE_PORT` (padrão: `8003`)
- **Descrição:** Serviço de inteligência artificial que integra com múltiplos provedores (OpenAI, DeepSeek, Ollama). Gerencia analytics, transações, modelos e planos de pricing.

### 5. WhatsApp Service
- **Porta:** `8020`
- **Diretório:** `4_messages_apps/whatsapp/`
- **Status:** 🔜 Planejado
- **Descrição:** Serviço de integração com WhatsApp Business API. Recebe mensagens do WhatsApp e as encaminha para o Chatbot Service.
- **Dependências:**
  - Chatbot Service (porta 8002)

### 6. Telegram Service
- **Porta:** `8021`
- **Diretório:** `4_messages_apps/telegram_operations/`
- **Arquivo Principal:** `4_messages_apps/telegram_operations/main.py`
- **Arquivo de Configuração:** `4_messages_apps/telegram_operations/config.py`
- **URL Padrão:** `http://localhost:8021`
- **Documentação:** `http://localhost:8021/docs`
- **Variável de Ambiente:** `PORT` (padrão: `8021`)
- **Descrição:** Serviço de integração com Telegram Bot API. Recebe mensagens do Telegram e as encaminha para o Chatbot Service.
- **Dependências:**
  - Chatbot Service (porta 8002)

### 7. Outros Message Apps (Reservado)
- **Portas:** `8022-8029`
- **Diretório:** `4_messages_apps/`
- **Status:** 🔜 Reservado para futuros serviços
- **Descrição:** Portas reservadas para futuros serviços de mensagens como:
  - Instagram Direct Messages
  - Facebook Messenger
  - Discord
  - Slack
  - Outros serviços de mensageria

---

## 🔗 Dependências entre Serviços

```
Gateway Service (8000)
  ├── User Service (8001)
  ├── Chatbot Service (8002)
  │   └── AI Service (8003)
  └── Message Apps Services (8020-8029)
      ├── WhatsApp Service (8020)
      │   └── Chatbot Service (8002)
      │       └── AI Service (8003)
      └── Telegram Service (8021)
          └── Chatbot Service (8002)
              └── AI Service (8003)
```

### Fluxo de Comunicação

1. **Frontend → Gateway (8000) → User Service (8001)**
   - Autenticação e gerenciamento de usuários

2. **Frontend → Gateway (8000) → Chatbot Service (8002) → AI Service (8003)**
   - Conversas com chatbot

3. **WhatsApp → WhatsApp Service (8020) → Chatbot Service (8002) → AI Service (8003)**
   - Mensagens do WhatsApp processadas pelo chatbot

4. **Telegram → Telegram Service (8021) → Chatbot Service (8002) → AI Service (8003)**
   - Mensagens do Telegram processadas pelo chatbot

---

## 📝 Notas Importantes

### Serviços Implementados
- ✅ Gateway Service (8000)
- ✅ User Service (8001)
- ✅ Chatbot Service (8002)
- ✅ AI Service (8003)
- ✅ Telegram Service (8021)

### Serviços Planejados
- 🔜 WhatsApp Service (8020)
- 🔜 Outros Message Apps (8022-8029)

### Configuração de Portas
- As portas podem ser alteradas através de variáveis de ambiente
- Consulte os arquivos `.env` ou `env.example` de cada serviço
- O Gateway Service mantém referências às portas dos outros serviços em `config.py`

### Ordem de Inicialização Recomendada

Para iniciar todos os serviços na ordem correta:

1. **AI Service (8003)** - Base para outros serviços
   ```bash
   cd 2_artificial_intelligence/ai_operations
   python main.py
   ```

2. **User Service (8001)** - Autenticação
   ```bash
   cd 1_users
   python main.py
   ```

3. **Chatbot Service (8002)** - Depende do AI Service
   ```bash
   cd 3_chatbot/bot_operations
   python main.py
   ```

4. **Telegram Service (8021)** - Depende do Chatbot Service
   ```bash
   cd 4_messages_apps/telegram_operations
   python main.py
   ```

5. **Gateway Service (8000)** - Depende de todos os outros
   ```bash
   cd 0_gateway
   python main.py
   ```

### Serviços no Gateway Dispatch Router

O `dispatch_router.py` do Gateway Service contém mapeamentos para os serviços implementados no projeto:

- User Service (8001)
- Import/Chatbot Service (8002)
- AI Service (8003)

---

## 🔧 Variáveis de Ambiente

Para alterar as portas, configure as seguintes variáveis de ambiente em cada serviço:

```bash
# Gateway Service (0_gateway/.env)
PORT=8000

# User Service (1_users/.env)
PORT=8001

# Chatbot Service (3_chatbot/bot_operations/.env)
PORT=8002

# AI Service (2_artificial_intelligence/ai_operations/.env)
AI_SERVICE_PORT=8003

# WhatsApp Service (4_messages_apps/whatsapp/.env)
PORT=8020

# Telegram Service (4_messages_apps/telegram_operations/.env)
PORT=8021
```

---

## 🚀 Scripts de Inicialização

Alguns serviços possuem scripts de inicialização:

- **Gateway Service:** `0_gateway/__start__.bat` ou `__start__.ps1` (Windows)
- **Gateway Service:** `0_gateway/start.sh` (Linux/Mac)

---

**Última atualização:** Baseado na análise dos arquivos implementados no projeto atual. Portas reorganizadas em sequência lógica.
