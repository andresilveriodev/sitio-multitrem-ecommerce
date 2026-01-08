# 🔍 Diagnóstico: Mensagens não chegam no WhatsApp

## ❌ Problemas Identificados

### 1. Redis - Senha Incorreta
**Erro**: `WRONGPASS invalid username-password pair`

**Causa**: O WhatsApp Service está tentando conectar ao Redis com senha, mas o Redis do Docker não tem senha configurada.

**Solução**:
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"

# Remover senha do Redis no .env
(Get-Content .env) -replace 'REDIS_PASSWORD=.*', 'REDIS_PASSWORD=' | Set-Content .env

# Reiniciar o WhatsApp Service (Ctrl+C no terminal e rodar novamente)
npm run start:dev
```

### 2. Webhook - URL Incorreta
**Erro**: Evolution API está tentando enviar para `localhost:3006` em vez de `host.docker.internal:3006`

**Causa**: O container Docker da Evolution API não consegue acessar `localhost` do Windows.

**Solução**: Já configuramos o webhook corretamente, mas o Evolution API ainda tem a configuração antiga em cache.

## ✅ Soluções Aplicadas

### 1. Remover Senha do Redis
```powershell
cd services/whatsapp-service
$content = Get-Content .env -Raw
$content = $content -replace 'REDIS_PASSWORD=.*', 'REDIS_PASSWORD='
Set-Content .env $content
```

### 2. Reiniciar Evolution API
```powershell
docker restart evolution_api
```

### 3. Reconfigurar Webhook
```powershell
cd services/evolution-api
node configure-webhook.js
```

## 🧪 Como Testar

### Teste 1: Verificar se WhatsApp Service está funcionando
```powershell
cd services/evolution-api
node test-webhook-direct.js
```

**Resultado Esperado**: `"processed": true` e mensagem de resposta do Agno

### Teste 2: Enviar mensagem real pelo WhatsApp
1. Abra o WhatsApp conectado à Evolution API
2. Envie uma mensagem de teste: "Olá! Quero comprar hortaliças"
3. Aguarde a resposta do robô

### Teste 3: Verificar logs
**Terminal do WhatsApp Service** (porta 3006):
```
📥 Webhook recebido!
🤖 Roteando para agente: Vendedor
✅ Resposta enviada para WhatsApp
```

**Terminal do Agno AgentOS** (porta 7777):
```
Processando mensagem: Olá! Quero comprar hortaliças
Agente: Vendedor
```

## 📋 Checklist de Verificação

- [ ] Redis sem senha no `.env` do WhatsApp Service
- [ ] WhatsApp Service reiniciado após mudança no `.env`
- [ ] Evolution API reiniciada (`docker restart evolution_api`)
- [ ] Webhook reconfigurado com `host.docker.internal:3006`
- [ ] Teste direto funcionando (`test-webhook-direct.js`)
- [ ] Agno AgentOS rodando (porta 7777)
- [ ] WhatsApp Service rodando (porta 3006)
- [ ] WhatsApp conectado na Evolution API

## 🔧 Comandos Rápidos

### Reiniciar tudo do zero:
```powershell
# 1. Parar WhatsApp Service (Ctrl+C no terminal)

# 2. Reiniciar Evolution API
docker restart evolution_api

# 3. Aguardar 10 segundos
Start-Sleep -Seconds 10

# 4. Reconfigurar webhook
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
node configure-webhook.js

# 5. Iniciar WhatsApp Service
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\whatsapp-service"
npm run start:dev
```

### Ver logs em tempo real:
```powershell
# Evolution API
docker logs evolution_api -f --tail 50

# WhatsApp Service
# (já está visível no terminal onde rodou npm run start:dev)

# Agno AgentOS
# (já está visível no terminal onde rodou python my_os.py)
```

## 🎯 Próximos Passos

1. **Aplicar as correções**:
   - Remover senha do Redis
   - Reiniciar WhatsApp Service

2. **Testar**:
   - Rodar `test-webhook-direct.js`
   - Enviar mensagem real pelo WhatsApp

3. **Verificar logs**:
   - Conferir se não há mais erros de Redis
   - Conferir se o webhook está sendo recebido
   - Conferir se o Agno está processando

4. **Reportar resultado**:
   - Se funcionar: 🎉 Sucesso!
   - Se não funcionar: Compartilhar os logs para análise



