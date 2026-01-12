# 🚀 Comandos para Iniciar a Integração Completa

## 📋 Copie e cole estes comandos em sequência

---

## **TERMINAL 1: Evolution API**

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
docker-compose up -d
docker ps --filter "name=evolution"
```

**Aguarde até ver os 3 containers rodando** ✅

---

## **TERMINAL 2: Agno AgentOS**

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\ai-service\agno-agent"
python my_os.py
```

**Aguarde até ver:**
```
🚀 SÍTIO MULTITREM - AGENTOS
🤖 Agentes Disponíveis:
  - Vendedor
  - Agendamento
  - Pagamento
  - Suporte
```

**Deixe este terminal aberto!** ✅

---

## **TERMINAL 3: WhatsApp Service**

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"
npm run start:dev
```

**Aguarde até ver:**
```
[Nest] Nest application successfully started
🤖 [Webhooks] AI Service: http://localhost:7777
🤖 [Webhooks] Usando Agno: SIM
```

**Deixe este terminal aberto!** ✅

---

## **TERMINAL 4: Configurar Webhook**

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node configure-webhook.js
```

**Deve mostrar:**
```
✅ Webhook configurado com sucesso!
```

**Pode fechar este terminal** ✅

---

## 🧪 **TESTE: Enviar Mensagem**

1. Abra o WhatsApp no celular
2. Envie uma mensagem para o número conectado:
   ```
   Olá! Quero comprar hortaliças
   ```

3. **Observe os logs:**
   - **Terminal 2 (Agno):** Deve mostrar "Roteando para agente: Vendedor"
   - **Terminal 3 (WhatsApp):** Deve mostrar "Resposta enviada"

4. **Verifique o WhatsApp:**
   - Deve receber uma resposta sobre produtos do Sítio Multitrem

---

## ✅ **Tudo Funcionando!**

Se você recebeu a resposta no WhatsApp, a integração está completa! 🎉

---

## 📝 **Próximos Testes**

Teste os outros agentes:

### **Agendamento:**
```
"Quando vocês fazem entrega?"
```

### **Pagamento:**
```
"Como faço para pagar?"
```

### **Suporte:**
```
"Preciso de ajuda com meu pedido"
```

---

## 🛑 **Para Parar Tudo**

```powershell
# Terminal 3 (WhatsApp Service)
Ctrl+C

# Terminal 2 (Agno)
Ctrl+C

# Terminal 1 (Evolution API)
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
docker-compose down
```

---

## 📚 **Documentação Completa**

- **Guia de Integração:** `services/whatsapp-service/GUIA_INTEGRACAO_AGNO.md`
- **Resumo:** `services/whatsapp-service/RESUMO_INTEGRACAO.md`
- **Evolution API:** `services/evolution-api/INSTALACAO_COMPLETA.md`
- **Agno AgentOS:** `services/ai-service/agno-agent/GUIA_AGENTOS.md`

---

**🎯 Dica:** Salve este arquivo para iniciar rapidamente no futuro!





