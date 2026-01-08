# 🤖 Guia de Integração: WhatsApp + Evolution API + Agno AgentOS

## 📋 Visão Geral

Este guia documenta a integração completa entre:
- **Evolution API** (porta 8080) - Conexão com WhatsApp Web
- **WhatsApp Service** (porta 3006) - Processamento de mensagens
- **Agno AgentOS** (porta 7777) - Inteligência Artificial Multi-Agente

---

## 🏗️ Arquitetura

```
┌─────────────────┐
│  WhatsApp Web   │
└────────┬────────┘
         │ mensagens
         ▼
┌─────────────────┐
│ Evolution API   │ (porta 8080)
│  (Docker)       │
└────────┬────────┘
         │ webhook
         ▼
┌─────────────────┐
│ WhatsApp Service│ (porta 3006)
│   (NestJS)      │
└────────┬────────┘
         │ encaminha
         ▼
┌─────────────────┐
│  Agno AgentOS   │ (porta 7777)
│   (Python)      │
│                 │
│  🤖 Vendedor    │
│  📅 Agendamento │
│  💰 Pagamento   │
│  🆘 Suporte     │
└────────┬────────┘
         │ resposta
         ▼
    (volta para WhatsApp)
```

---

## ✅ Pré-requisitos

### 1. **Evolution API**
- ✅ Docker rodando
- ✅ Evolution API iniciada
- ✅ Instância WhatsApp criada
- ✅ QR Code escaneado
- ✅ WhatsApp conectado

**Verificar:**
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
docker-compose ps
node test-api.js
```

### 2. **Agno AgentOS**
- ✅ Python 3.9+ instalado
- ✅ Dependências instaladas
- ✅ OPENAI_API_KEY configurada

**Verificar:**
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\ai-service\agno-agent"
python --version
# Deve mostrar Python 3.9 ou superior
```

### 3. **WhatsApp Service**
- ✅ Node.js 20+ instalado
- ✅ Dependências instaladas
- ✅ .env configurado

**Verificar:**
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"
node --version
# Deve mostrar v20.0.0 ou superior
```

---

## 🚀 Passo a Passo para Iniciar

### **PASSO 1: Iniciar Evolution API**

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
docker-compose up -d
```

**Verificar:**
```powershell
docker ps --filter "name=evolution"
```

Deve mostrar:
- `evolution_api` - Up
- `evolution_postgres` - Up
- `evolution_redis` - Up

---

### **PASSO 2: Iniciar Agno AgentOS**

**Terminal 1:**
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\ai-service\agno-agent"

# Ativar ambiente virtual (se usar)
.\.venv\Scripts\Activate.ps1

# Iniciar Agno
python my_os.py
```

**Aguarde até ver:**
```
============================================================
🚀 SÍTIO MULTITREM - AGENTOS
============================================================
📝 Porta: 7777 (padrão AgentOS)
🌐 App Interface: http://localhost:7777
📚 API Docs: http://localhost:7777/docs
⚙️  Config: http://localhost:7777/config

🤖 Agentes Disponíveis:
  - Vendedor - Vendas e produtos
  - Agendamento - Entregas e horários
  - Pagamento - Pix e boleto
  - Suporte - Ajuda e problemas
============================================================
```

**✅ Agno está pronto!**

---

### **PASSO 3: Iniciar WhatsApp Service**

**Terminal 2:**
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"

# Iniciar em modo desenvolvimento
npm run start:dev
```

**Aguarde até ver:**
```
[Nest] LOG [NestFactory] Starting Nest application...
[Nest] LOG [InstanceLoader] AppModule dependencies initialized
[Nest] LOG [InstanceLoader] ConfigModule dependencies initialized
[Nest] LOG [InstanceLoader] WhatsAppModule dependencies initialized
[Nest] LOG [InstanceLoader] AgnoModule dependencies initialized
[Nest] LOG [InstanceLoader] WebhooksModule dependencies initialized
[Nest] LOG [NestApplication] Nest application successfully started
🤖 [Webhooks] AI Service: http://localhost:7777
🤖 [Webhooks] Usando Agno: SIM
```

**✅ WhatsApp Service está pronto!**

---

### **PASSO 4: Configurar Webhook**

**Terminal 3:**
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node configure-webhook.js
```

**Deve mostrar:**
```
✅ Webhook configurado com sucesso!

📋 Detalhes da configuração:
  URL: http://localhost:3006/webhooks/whatsapp
  Eventos:
    - MESSAGES_UPSERT (novas mensagens)
    - MESSAGES_UPDATE (atualizações)
    - CONNECTION_UPDATE (status da conexão)

🎉 Pronto! Agora as mensagens do WhatsApp serão enviadas para o WhatsApp Service!
```

**✅ Webhook configurado!**

---

## 🧪 Testes

### **Teste 1: Verificar Serviços**

```powershell
# Evolution API
curl http://localhost:8080

# Agno AgentOS
curl http://localhost:7777/health

# WhatsApp Service
curl http://localhost:3006/health
```

Todos devem retornar status 200.

---

### **Teste 2: Enviar Mensagem de Teste**

1. **Abra o WhatsApp** no celular conectado
2. **Envie uma mensagem** para o número conectado:
   ```
   Olá! Quero comprar hortaliças
   ```

3. **Observe os logs:**

**Terminal 1 (Agno):**
```
🤖 [Agno] Roteando para agente: Vendedor
📝 [Agno] Mensagem: Olá! Quero comprar hortaliças...
✅ [Agno] Resposta recebida do agente Vendedor
```

**Terminal 2 (WhatsApp Service):**
```
🤖 [Webhooks] Usando Agno AgentOS
🤖 [Agno] Roteando para agente: Vendedor
✅ [Webhooks] Resposta enviada para 5511999999999
```

4. **Verifique o WhatsApp:**
   - Deve receber uma resposta do agente Vendedor
   - Resposta deve ser sobre produtos do Sítio Multitrem

---

### **Teste 3: Testar Roteamento de Agentes**

Envie diferentes mensagens para testar o roteamento:

#### **Vendedor:**
```
"Quais produtos vocês têm?"
"Quanto custa a alface?"
"Quero comprar ovos"
```

#### **Agendamento:**
```
"Quando vocês entregam?"
"Quero agendar uma entrega"
"Qual o horário de entrega?"
```

#### **Pagamento:**
```
"Como faço para pagar?"
"Aceita Pix?"
"Quero pagar com boleto"
```

#### **Suporte:**
```
"Preciso de ajuda"
"Quero cancelar meu pedido"
"Onde está minha entrega?"
```

---

## 📊 Monitoramento

### **Logs do Agno AgentOS**

```powershell
# Ver logs em tempo real
# Terminal 1 já mostra os logs
```

**O que observar:**
- `🤖 [Agno] Roteando para agente: X` - Qual agente foi escolhido
- `✅ [Agno] Resposta recebida` - Resposta gerada com sucesso

---

### **Logs do WhatsApp Service**

```powershell
# Ver logs em tempo real
# Terminal 2 já mostra os logs
```

**O que observar:**
- `🤖 [Webhooks] Usando Agno AgentOS` - Confirmação de uso do Agno
- `✅ [Webhooks] Resposta enviada` - Mensagem enviada com sucesso

---

### **Logs da Evolution API**

```powershell
docker logs evolution_api --tail 50 -f
```

**O que observar:**
- `[MESSAGES_UPSERT]` - Nova mensagem recebida
- `[WEBHOOK]` - Webhook enviado para WhatsApp Service

---

## 🐛 Troubleshooting

### **Problema 1: Agno não responde**

**Sintomas:**
- Mensagem chega mas não há resposta
- Logs mostram erro de conexão

**Solução:**
```powershell
# 1. Verificar se Agno está rodando
curl http://localhost:7777/health

# 2. Verificar logs do Agno (Terminal 1)
# Deve mostrar: "Roteando para agente: X"

# 3. Reiniciar Agno
# Ctrl+C no Terminal 1
python my_os.py
```

---

### **Problema 2: WhatsApp Service não recebe mensagens**

**Sintomas:**
- Mensagem enviada no WhatsApp
- Nada acontece nos logs

**Solução:**
```powershell
# 1. Verificar webhook
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node configure-webhook.js

# 2. Verificar se WhatsApp Service está rodando
curl http://localhost:3006/health

# 3. Ver logs da Evolution API
docker logs evolution_api --tail 50
```

---

### **Problema 3: Erro "Agno AgentOS não está rodando"**

**Sintomas:**
- Logs mostram: `❌ [Agno] AgentOS não está rodando!`

**Solução:**
```powershell
# 1. Verificar se Agno está rodando
curl http://localhost:7777/health

# 2. Se não estiver, iniciar:
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\ai-service\agno-agent"
python my_os.py
```

---

### **Problema 4: Erro de roteamento**

**Sintomas:**
- Mensagem vai para o agente errado

**Solução:**
Edite o arquivo `services/whatsapp-service/src/agno/agno.service.ts`:

```typescript
private routeToAgent(message: string, conversationHistory?: any[]): string {
  const lowerMessage = message.toLowerCase()

  // Adicione ou ajuste as palavras-chave aqui
  if (lowerMessage.includes('pagar') || lowerMessage.includes('pix')) {
    return 'Pagamento'
  }
  
  // ... outras regras ...
}
```

---

## 📝 Checklist de Funcionamento

Use este checklist para verificar se tudo está funcionando:

- [ ] Evolution API rodando (porta 8080)
- [ ] WhatsApp conectado (QR Code escaneado)
- [ ] Agno AgentOS rodando (porta 7777)
- [ ] WhatsApp Service rodando (porta 3006)
- [ ] Webhook configurado
- [ ] Mensagem de teste enviada
- [ ] Resposta recebida no WhatsApp
- [ ] Logs mostram roteamento correto
- [ ] Todos os 4 agentes testados

---

## 🎯 Fluxo Completo de uma Mensagem

1. **Usuário envia mensagem** no WhatsApp
2. **WhatsApp Web** recebe a mensagem
3. **Evolution API** captura a mensagem
4. **Evolution API** envia webhook para `http://localhost:3006/webhooks/whatsapp`
5. **WhatsApp Service** recebe o webhook
6. **WebhooksService** processa a mensagem
7. **AgnoService** roteia para o agente correto
8. **Agno AgentOS** processa com o agente escolhido
9. **Agente** (Vendedor/Agendamento/Pagamento/Suporte) gera resposta
10. **Agno** retorna resposta para WhatsApp Service
11. **WhatsApp Service** formata a resposta
12. **WhatsApp Service** envia para Evolution API
13. **Evolution API** envia para WhatsApp Web
14. **Usuário recebe** a resposta no WhatsApp

---

## 🔧 Comandos Úteis

### **Iniciar Tudo**

```powershell
# Terminal 1: Evolution API
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
docker-compose up -d

# Terminal 2: Agno AgentOS
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\ai-service\agno-agent"
python my_os.py

# Terminal 3: WhatsApp Service
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"
npm run start:dev

# Terminal 4: Configurar Webhook
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node configure-webhook.js
```

### **Parar Tudo**

```powershell
# Parar WhatsApp Service (Terminal 3)
Ctrl+C

# Parar Agno (Terminal 2)
Ctrl+C

# Parar Evolution API
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
docker-compose down
```

### **Ver Logs**

```powershell
# Evolution API
docker logs evolution_api --tail 50 -f

# Agno AgentOS
# Ver no Terminal 2

# WhatsApp Service
# Ver no Terminal 3
```

---

## 📚 Referências

- **Evolution API:** `services/evolution-api/INSTALACAO_COMPLETA.md`
- **Agno AgentOS:** `services/ai-service/agno-agent/GUIA_AGENTOS.md`
- **WhatsApp Service:** `services/whatsapp-service/INTEGRACAO_EVOLUTION.md`

---

## ✅ Status da Integração

| Componente | Status | Porta |
|------------|--------|-------|
| Evolution API | ✅ Funcionando | 8080 |
| Agno AgentOS | ✅ Funcionando | 7777 |
| WhatsApp Service | ✅ Funcionando | 3006 |
| Integração | ✅ Completa | - |

---

**🎉 Integração completa e funcionando!**

Para qualquer dúvida, consulte os logs ou a documentação de cada componente.

---

**📅 Data de criação:** 07/01/2026  
**✍️ Autor:** Documentação da integração WhatsApp + Agno  
**🔖 Versão:** 1.0





