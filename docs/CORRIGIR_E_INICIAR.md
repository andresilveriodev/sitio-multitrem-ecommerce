# 🔧 Correções Aplicadas + Comandos para Iniciar

## ✅ **Correções Feitas:**

1. ✅ **Agno:** Ambiente virtual precisa ser ativado
2. ✅ **Agno:** Emojis removidos do `my_os.py` (problema de encoding no Windows)
3. ✅ **WhatsApp Service:** Variável `.env` corrigida (`EVOLUTION_INSTANCE`)
4. ✅ **Webhook:** Formato do JSON corrigido

---

## 🚀 **Comandos Corretos para Executar:**

### **TERMINAL 1: Evolution API** (já está rodando ✅)

```powershell
# Verificar se está rodando
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
docker ps --filter "name=evolution"
```

---

### **TERMINAL 2: Agno AgentOS** (NOVO COMANDO)

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\ai-service\agno-agent"

# IMPORTANTE: Ativar o ambiente virtual primeiro!
.\.venv\Scripts\Activate.ps1

# Agora sim, iniciar o Agno
python my_os.py
```

**Aguarde até ver:**
```
============================================================
🚀 SÍTIO MULTITREM - AGENTOS
============================================================
📝 Porta: 7777
🤖 Agentes Disponíveis:
  - Vendedor
  - Agendamento
  - Pagamento
  - Suporte
============================================================
```

**✅ Deixe este terminal aberto!**

---

### **TERMINAL 3: WhatsApp Service** (REINICIAR)

```powershell
# Se ainda estiver rodando, pare com Ctrl+C primeiro

cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"
npm run start:dev
```

**Aguarde até ver:**
```
[Nest] Nest application successfully started
🤖 [Webhooks] AI Service: http://localhost:7777
🤖 [Webhooks] Usando Agno: SIM
```

**✅ Deixe este terminal aberto!**

---

### **TERMINAL 4: Configurar Webhook** (NOVO COMANDO)

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node configure-webhook.js
```

**Deve mostrar:**
```
✅ Webhook configurado com sucesso!
```

---

## 🧪 **Teste Final:**

1. **Abra o WhatsApp** no celular
2. **Envie uma mensagem:**
   ```
   Olá! Quero comprar hortaliças
   ```

3. **Observe os logs:**
   - **Terminal 2 (Agno):** Deve mostrar "Roteando para agente: Vendedor"
   - **Terminal 3 (WhatsApp):** Deve mostrar "Resposta enviada"

4. **Verifique o WhatsApp:**
   - Deve receber uma resposta sobre produtos

---

## 📝 **Resumo das Correções:**

### **1. Agno (Terminal 2)**
**Problema:** `ModuleNotFoundError: No module named 'agno'`  
**Causa:** Ambiente virtual não estava ativado  
**Solução:** Adicionar `.\.venv\Scripts\Activate.ps1` antes de `python my_os.py`

### **2. WhatsApp Service (Terminal 3)**
**Problema:** `Cannot read properties of undefined (reading 'baseUrl')`  
**Causa:** Variável `.env` estava como `EVOLUTION_INSTANCE_NAME` mas o código espera `EVOLUTION_INSTANCE`  
**Solução:** Corrigido automaticamente no `.env`

### **3. Webhook (Terminal 4)**
**Problema:** `instance requires property "webhook"`  
**Causa:** Formato do JSON estava incorreto  
**Solução:** Envolver configurações dentro de `{ webhook: { ... } }`

---

## ✅ **Checklist:**

- [ ] Terminal 1: Evolution API rodando
- [ ] Terminal 2: Agno AgentOS iniciado (com .venv ativado)
- [ ] Terminal 3: WhatsApp Service iniciado
- [ ] Terminal 4: Webhook configurado
- [ ] Teste: Mensagem enviada e resposta recebida

---

**🎯 Agora execute os comandos na ordem acima!**

