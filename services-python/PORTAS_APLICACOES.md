# Portas das Aplicações Python

Este documento organiza as portas utilizadas por cada aplicação Python **implementada** no projeto, seguindo uma sequência lógica.

## ⚡ Referência Rápida

| Porta | Serviço | Status |
|-------|---------|--------|
| 8000 | Gateway Service | ✅ |
| 8001 | User Service | ✅ |
| 8002 | Commerce Service | ✅ |
| 8005 | AI Service Operations | ✅ |
| 8006 | AI Service Users | ✅ |
| 8010 | Chatbot Users Service | ✅ |
| 8011 | Chatbot Operations Service | ✅ |
| 8020 | WhatsApp Service | 🔜 |
| 8021 | Telegram Service Operations (Colaboradores) | ✅ |

---

## 📋 Resumo das Portas

| Porta | Serviço | Diretório | Status | Descrição |
|-------|---------|-----------|--------|-----------|
| **8000** | Gateway Service | `0_gateway/` | ✅ Implementado | Gateway principal que roteia requisições para outros serviços |
| **8001** | User Service | `1_users/` | ✅ Implementado | Serviço de autenticação e gerenciamento de usuários |
| **8002** | Commerce Service | `5_commerce/` | ✅ Implementado | Serviço de processamento de pedidos do e-commerce |
| **8003-8004** | Reservado | - | 🔜 Reservado | Portas reservadas para serviços futuros |
| **8005** | AI Service | `2_artificial_intelligence/ai_operations/` | ✅ Implementado | Serviço de inteligência artificial |
| **8006-8009** | Reservado | - | 🔜 Reservado | Portas reservadas para serviços futuros |
| **8010** | Chatbot Users Service | `3_chatbot/bot_users/` | ✅ Implementado | Serviço de chatbot para usuários - middleware entre frontend e AI Service |
| **8011** | Chatbot Operations Service | `3_chatbot/bot_operations/` | ✅ Implementado | Serviço de chatbot para operações - middleware entre frontend e AI Service |
| **8012-8019** | Reservado | - | 🔜 Reservado | Portas reservadas para serviços futuros |
| **8020** | WhatsApp Service | `4_messages_apps/whatsapp/` | 🔜 Planejado | Serviço de integração com WhatsApp |
| **8021** | Telegram Service | `4_messages_apps/telegram_operations/` | ✅ Implementado | Serviço de integração com Telegram |
| **8022-8029** | Outros Message Apps | `4_messages_apps/` | 🔜 Reservado | Portas reservadas para futuros serviços de mensagens |

---

## 🎯 Organização Lógica das Portas

### Serviços Core (8000-8019)
- **8000**: Gateway Service
- **8001**: User Service
- **8002**: Commerce Service
- **8005**: Ai Service
- **8010**: Chatbot Users Service
- **8011**: Chatbot Operations Service


### Serviços de Mensagens (8020-8029)
- **8020**: WhatsApp Service
- **8021**: Telegram Service
- **8022-8029**: Reservado para futuros serviços de mensagens (Instagram, Facebook Messenger, Discord, etc.)

---

## 🔍 Detalhamento por Serviço

### Serviços Core

#### 1. Gateway Service (Porta 8000)
- **Porta:** `8000`
- **Diretório:** `0_gateway/`
- **Arquivo Principal:** `0_gateway/main.py`
- **Arquivo de Configuração:** `0_gateway/config.py`
- **URL Padrão:** `http://localhost:8000`
- **Documentação:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`
- **Variável de Ambiente:** `PORT` (padrão: `8000`)
- **Descrição:** Gateway principal que atua como ponto de entrada único, roteando requisições para os demais microserviços. Inclui autenticação, CORS, circuit breaker e load balancing.

#### 2. User Service (Porta 8001)
- **Porta:** `8001`
- **Diretório:** `1_users/`
- **Arquivo Principal:** `1_users/main.py`
- **Arquivo de Configuração:** `1_users/config.py`
- **URL Padrão:** `http://localhost:8001`
- **Base Path:** `/api/v1`
- **Documentação:** `http://localhost:8001/docs`
- **Variável de Ambiente:** `PORT` (padrão: `8001`)
- **Descrição:** Serviço de autenticação e autorização com integração ao Keycloak. Gerencia usuários, perfis, preferências e ACL (Access Control List).

#### 3. AI Service (Porta 8005)
- **Porta:** `8005`
- **Diretório:** `2_artificial_intelligence/ai_operations/`
- **Arquivo Principal:** `2_artificial_intelligence/ai_operations/main.py`
- **Arquivo de Configuração:** `2_artificial_intelligence/ai_operations/app/config.py`
- **URL Padrão:** `http://localhost:8005`
- **Base Path:** `/api/v1`
- **Documentação:** `http://localhost:8005/docs`
- **Health Check:** `http://localhost:8005/health`
- **Variável de Ambiente:** `AI_SERVICE_PORT` (padrão: `8005`)
- **Descrição:** Serviço de inteligência artificial que integra com múltiplos provedores (OpenAI, DeepSeek, Ollama). Gerencia analytics, transações, modelos e planos de pricing.

#### 5. Portas Reservadas (8006-8009)
- **Portas:** `8006-8009`
- **Status:** 🔜 Reservado para futuros serviços
- **Descrição:** Portas reservadas para expansão de serviços core do sistema.

#### 6. Chatbot Users Service (Porta 8010)
- **Porta:** `8010`
- **Diretório:** `3_chatbot/bot_users/`
- **Arquivo Principal:** `3_chatbot/bot_users/main.py`
- **Arquivo de Configuração:** `3_chatbot/bot_users/config.py`
- **URL Padrão:** `http://localhost:8010`
- **Base Path:** `/api/v1`
- **Documentação:** `http://localhost:8010/docs` (se DEBUG=true)
- **Variável de Ambiente:** `PORT` (padrão: `8010`)
- **Descrição:** Serviço de chatbot para usuários (E-commerce). Middleware inteligente entre o frontend e o AI Service. Gerencia contexto de conversas, cache, filtros de mensagens e otimização de custos.
- **Dependências:**
  - AI Service (porta 8005)

#### 7. Chatbot Operations Service (Porta 8011)
- **Porta:** `8011`
- **Diretório:** `3_chatbot/bot_operations/`
- **Arquivo Principal:** `3_chatbot/bot_operations/main.py`
- **Arquivo de Configuração:** `3_chatbot/bot_operations/config.py`
- **URL Padrão:** `http://localhost:8011`
- **Base Path:** `/api/v1`
- **Documentação:** `http://localhost:8011/docs` (se DEBUG=true)
- **Variável de Ambiente:** `PORT` (padrão: `8011`)
- **Descrição:** Serviço de chatbot para operações (B3-Trader). Middleware inteligente entre o frontend e o AI Service. Gerencia contexto de conversas, cache, filtros de mensagens, integração com Market Data Service e otimização de custos.
- **Dependências:**
  - AI Service (porta 8005)
  - Market Data Service (configurado na porta 8000, pode estar no Gateway)

#### 8. Portas Reservadas (8012-8019)
- **Portas:** `8012-8019`
- **Status:** 🔜 Reservado para futuros serviços
- **Descrição:** Portas reservadas para expansão de serviços core do sistema.

### Serviços de Mensagens

#### 9. WhatsApp Service (Porta 8020)
- **Porta:** `8020`
- **Diretório:** `4_messages_apps/whatsapp/`
- **Status:** 🔜 Planejado
- **Variável de Ambiente:** `PORT` (padrão: `8020`)
- **Descrição:** Serviço de integração com WhatsApp Business API. Recebe mensagens do WhatsApp e as encaminha para o Chatbot Service.
- **Dependências:**
  - Chatbot Users Service (porta 8010)

#### 10. Telegram Service (Porta 8021)
- **Porta:** `8021`
- **Diretório:** `4_messages_apps/telegram_operations/`
- **Arquivo Principal:** `4_messages_apps/telegram_operations/main.py`
- **Arquivo de Configuração:** `4_messages_apps/telegram_operations/config.py`
- **URL Padrão:** `http://localhost:8021`
- **Documentação:** `http://localhost:8021/docs`
- **Variável de Ambiente:** `PORT` (padrão: `8021`)
- **Descrição:** Serviço de integração com Telegram Bot API. Recebe mensagens do Telegram e as encaminha para o Chatbot Service.
- **Dependências:**
  - Chatbot Users Service (porta 8010)

#### 11. Outros Message Apps (Portas 8022-8029)
- **Portas:** `8022-8029`
- **Diretório:** `4_messages_apps/`
- **Status:** 🔜 Reservado para futuros serviços
- **Descrição:** Portas reservadas para futuros serviços de mensagens como:
  - Instagram Direct Messages
  - Facebook Messenger
  - Discord
  - Slack
  - Outros serviços de mensageria

#### 3. Commerce Service (Porta 8002)
- **Porta:** `8002`
- **Diretório:** `5_commerce/`
- **Arquivo Principal:** `5_commerce/main.py`
- **Arquivo de Configuração:** `5_commerce/config.py`
- **URL Padrão:** `http://localhost:8002`
- **Base Path:** `/api/v1`
- **Documentação:** `http://localhost:8002/docs`
- **Health Check:** `http://localhost:8002/health`
- **Variável de Ambiente:** `PORT` (padrão: `8002`)
- **Descrição:** Serviço de processamento de pedidos do e-commerce Sítio Multitrem. Gerencia produtos, clientes, pedidos, pagamentos e entregas.

---

## 🔗 Dependências entre Serviços

```
Gateway Service (8000)
  ├── User Service (8001)
  ├── E-Commerce (8002)
  ├── AI Service (8005)
  ├── Chatbot Users Service (8010)
  │   └── AI Service (8005)
  ├── Chatbot Operations Service (8011)
  │   ├── AI Service (8005)
  │   └── Market Data Service (8000)
  └── Message Apps Services (8020-8029)
      ├── WhatsApp Service (8020)
      │   └── Chatbot Users Service (8010)
      │       └── AI Service (8005)
      └── Telegram Service (8021)
          └── Chatbot Users Service (8010)
              └── AI Service (8005)
```

### Fluxo de Comunicação

1. **Frontend → Gateway (8000) → User Service (8001)**
   - Autenticação e gerenciamento de usuários

2. **Frontend → Gateway (8000) → Commerce Service (8002)**
   - Gerenciamento de produtos, pedidos, pagamentos e entregas

3. **Frontend → Gateway (8000) → Chatbot Users Service (8010) → AI Service (8005)**
   - Conversas com chatbot (usuários)

4. **Frontend → Gateway (8000) → Chatbot Operations Service (8011) → AI Service (8005)**
   - Conversas com chatbot (operações)

5. **WhatsApp → WhatsApp Service (8020) → Chatbot Users Service (8010) → AI Service (8005)**
   - Mensagens do WhatsApp processadas pelo chatbot

6. **Telegram → Telegram Service (8021) → Chatbot Users Service (8010) → AI Service (8005)**
   - Mensagens do Telegram processadas pelo chatbot

---

## 📝 Notas Importantes

### Serviços Implementados
- ✅ Gateway Service (8000)
- ✅ User Service (8001)
- ✅ Commerce Service (8002)
- ✅ AI Service (8005)
- ✅ Chatbot Users Service (8010)
- ✅ Chatbot Operations Service (8011)
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

#### 1. Serviços Base (sem dependências)
**AI Service (8005)** - Base para outros serviços
```bash
cd 2_artificial_intelligence/ai_operations
python main.py
```

**User Service (8001)** - Autenticação
```bash
cd 1_users
python main.py
```

#### 2. Serviços Dependentes
**Chatbot Users Service (8010)** - Depende do AI Service
```bash
cd 3_chatbot/bot_users
python main.py
```

**Chatbot Operations Service (8011)** - Depende do AI Service e Market Data Service
```bash
cd 3_chatbot/bot_operations
python main.py
```

**Telegram Service (8021)** - Depende do Chatbot Users Service
```bash
cd 4_messages_apps/telegram_operations
python main.py
```

#### 3. Gateway (último a iniciar)
**Gateway Service (8000)** - Depende de todos os outros
```bash
cd 0_gateway
python main.py
```

### Serviços no Gateway Dispatch Router

O `dispatch_router.py` do Gateway Service contém mapeamentos para os serviços implementados no projeto:

- User Service (8001)
- AI Service (8005)
- Import/Chatbot Users Service (8010)
- Chatbot Operations Service (8011)

---

## 🔧 Variáveis de Ambiente

Para alterar as portas, configure as seguintes variáveis de ambiente em cada serviço:

### Serviços Core
```bash
# Gateway Service (0_gateway/.env)
PORT=8000

# User Service (1_users/.env)
PORT=8001

# Commerce Service (5_commerce/.env)
PORT=8002

# AI Service (2_artificial_intelligence/ai_operations/.env)
AI_SERVICE_PORT=8005

# Chatbot Users Service (3_chatbot/bot_users/.env)
PORT=8010

# Chatbot Operations Service (3_chatbot/bot_operations/.env)
PORT=8011
```

### Serviços de Mensagens
```bash
# WhatsApp Service (4_messages_apps/whatsapp/.env)
PORT=8020

# Telegram Service (4_messages_apps/telegram_operations/.env)
PORT=8021

# Commerce Service (5_commerce/.env)
PORT=8002
```

---

## 🚀 Scripts de Inicialização

Alguns serviços possuem scripts de inicialização:

- **Gateway Service:** `0_gateway/__start__.bat` ou `__start__.ps1` (Windows)
- **Gateway Service:** `0_gateway/start.sh` (Linux/Mac)

---

**Última atualização:** Baseado na análise dos arquivos implementados no projeto atual. Portas reorganizadas em sequência lógica.
