# 🤖 Guia Completo - AgentOS Multi-Agente

## 🎯 Arquitetura

```
┌─────────────────────────────────────────────────┐
│         SÍTIO MULTITREM - AGENTOS               │
│         (Multi-Agent System)                    │
└────────────┬────────────────────────────────────┘
             │
     ┌───────┴────────┬─────────────┬──────────────┐
     │                │             │              │
┌────▼────┐    ┌─────▼──────┐  ┌──▼────────┐  ┌──▼──────────┐
│VENDEDOR │    │ AGENDAMENTO│  │ PAGAMENTO │  │   SUPORTE   │
│(Sales)  │    │(Scheduling)│  │ (Payment) │  │  (Support)  │
└─────────┘    └────────────┘  └───────────┘  └─────────────┘
```

## 🚀 Como Rodar

### **1. Instalar Dependências (Já Feito!)**
```powershell
python -m pip install -U agno "fastapi[standard]" uvicorn openai sqlalchemy aiosqlite greenlet
```

### **2. Iniciar o AgentOS**
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\ai-service\agno-agent"
python my_os.py
```

### **3. Acessar**
- **App Interface:** http://localhost:7777
- **API Docs:** http://localhost:7777/docs
- **Config:** http://localhost:7777/config

---

## 🌐 Conectar ao Control Plane (Playground Visual)

### **Passo 1: Manter o AgentOS Rodando**
Deixe `python my_os.py` rodando no terminal.

### **Passo 2: Acessar o Control Plane**
1. Abra: **https://app.agno.com**
2. Crie uma conta ou faça login
3. Clique no dropdown da organização (canto superior direito)
4. Clique no **"+"** ao lado de "Add new OS"

### **Passo 3: Configurar Conexão**
- **Endpoint URL:** `http://localhost:7777`
- **OS Name:** `Sítio Multitrem`
- **Tags:** `development`, `e-commerce`
- Clique em **CONNECT**

### **Passo 4: Conversar com os Agentes**
Após conectar, você verá os 4 agentes disponíveis:
- **Vendedor** - Para vendas
- **Agendamento** - Para entregas
- **Pagamento** - Para pagamentos
- **Suporte** - Para ajuda

---

## 🤖 Agentes Disponíveis

### **1️⃣ Vendedor (Sales Agent)**

**Responsabilidades:**
- ✅ Apresentar produtos e kits
- ✅ Explicar preços e promoções
- ✅ Adicionar/remover itens do carrinho
- ✅ Sugerir produtos complementares
- ✅ Criar pedidos

**Exemplo de conversa:**
```
Você: "Quais produtos vocês têm?"
Vendedor: "🥬 Temos hortaliças frescas colhidas no dia: 
- Alface crespa
- Rúcula
- Couve
- Tomate cereja
E também ovos caipiras fresquinhos! 🥚"
```

---

### **2️⃣ Agendamento (Scheduling Agent)**

**Responsabilidades:**
- ✅ Verificar dias de entrega disponíveis
- ✅ Agendar entregas
- ✅ Reagendar entregas
- ✅ Confirmar endereço

**Exemplo de conversa:**
```
Você: "Quando podem entregar?"
Agendamento: "📅 Entregas disponíveis:
- Quarta-feira: 8h-12h
- Sexta-feira: 8h-12h
- Sábado: 8h-12h
Qual dia prefere?"
```

---

### **3️⃣ Pagamento (Payment Agent)**

**Responsabilidades:**
- ✅ Gerar Pix e Boleto
- ✅ Verificar status de pagamentos
- ✅ Confirmar pagamentos
- ✅ Enviar comprovantes

**Exemplo de conversa:**
```
Você: "Como pagar?"
Pagamento: "💳 Métodos disponíveis:
- PIX (instantâneo)
- Boleto (vencimento 3 dias)
Qual prefere?"
```

---

### **4️⃣ Suporte (Support Agent)**

**Responsabilidades:**
- ✅ Resolver problemas
- ✅ Processar cancelamentos
- ✅ Rastrear pedidos
- ✅ Atualizar cadastro

**Exemplo de conversa:**
```
Você: "Quero cancelar meu pedido"
Suporte: "🆘 Entendo! Vou te ajudar.
Qual o número do seu pedido?"
```

---

## 📁 Estrutura Atual

```
agno-agent/
├── my_os.py                    # ✅ AgentOS principal (4 agentes)
├── sitio_multitrem.db          # Banco de dados SQLite
├── .env                        # Chave da OpenAI
├── .venv/                      # Ambiente virtual Python
└── GUIA_AGENTOS.md            # Este arquivo
```

---

## 🔧 Próximos Passos (Desenvolvimento)

### **FASE 1: Adicionar Ferramentas (Tools)**

Cada agente precisa de ferramentas específicas:

**Vendedor:**
```python
- list_products()
- add_to_cart()
- create_order()
```

**Agendamento:**
```python
- check_delivery_slots()
- schedule_delivery()
```

**Pagamento:**
```python
- generate_pix()
- generate_boleto()
```

**Suporte:**
```python
- track_order()
- cancel_order()
```

### **FASE 2: Integrar com Microsserviços**

Conectar os agentes com:
- Product Service (porta 3001)
- Cart Service (porta 3002)
- Order Service (porta 3003)
- Payment Service (porta 3004)

### **FASE 3: Adicionar Orquestrador (Router)**

Criar um agente que decide qual agente especializado deve responder.

---

## 🧪 Testar

### **Teste 1: Verificar Agentes**
```powershell
curl http://localhost:7777/config
```

### **Teste 2: API Docs**
Abra: http://localhost:7777/docs

### **Teste 3: Conversar**
Use o Control Plane: https://app.agno.com

---

## ⚠️ Dicas Importantes

1. **Use Chrome** para conectar ao Control Plane (Safari pode bloquear)
2. **Porta padrão:** 7777 (não 3007 como antes)
3. **AgentOS** substituiu o `playground.py`
4. **Control Plane** é o novo nome para a interface visual

---

## 📚 Documentação Oficial

- **Criar AgentOS:** https://docs.agno.com/agent-os/creating-your-first-os
- **Conectar:** https://docs.agno.com/agent-os/connecting-your-os
- **Overview:** https://docs.agno.com/agent-os/overview

---

**Criado em:** 06/01/2026
**Versão Agno:** 2.3.23





