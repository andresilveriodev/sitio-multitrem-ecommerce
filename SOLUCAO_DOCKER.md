# 🐳 Solução: Docker Desktop Não Está Rodando

## ❌ Problema Identificado

```
unable to get image 'evoapicloud/evolution-api:latest': error during connect
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

**Causa**: Docker Desktop não está iniciado no Windows.

---

## ✅ Solução Rápida

### Opção 1: Iniciar Docker Desktop (Recomendado)

1. **Procure por "Docker Desktop" no menu Iniciar**
2. **Clique para abrir**
3. **Aguarde** até o ícone da Docker ficar verde na bandeja do sistema
4. **Verifique** se está rodando:

```powershell
docker ps
```

**Resultado esperado**: Lista de containers (pode estar vazia, mas não deve dar erro)

### Depois que o Docker iniciar:

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"

# Iniciar Evolution API
docker-compose up -d

# Aguardar 15 segundos
Start-Sleep -Seconds 15

# Configurar webhook
node configure-webhook.js
```

---

## 🔍 Verificar se Docker Está Rodando

### Comando 1: Verificar serviço
```powershell
Get-Process "*docker*" | Select-Object Name, Id, CPU
```

**Resultado esperado** (se rodando):
```
Name                    Id     CPU
----                    --     ---
Docker Desktop      12345   12.34
com.docker.backend  12346    5.67
```

### Comando 2: Verificar containers
```powershell
docker ps
```

**Resultado esperado** (se rodando):
```
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

**Erro se NÃO estiver rodando**:
```
error during connect: ... The system cannot find the file specified.
```

---

## 📋 Passo a Passo Completo

### 1️⃣ Iniciar Docker Desktop

**No Windows:**
- Pressione `Win + S`
- Digite "Docker Desktop"
- Clique no aplicativo
- **AGUARDE** 30-60 segundos até inicializar

**Sinais de que está pronto:**
- ✅ Ícone da Docker na bandeja (system tray) fica **verde**
- ✅ Ao passar o mouse: "Docker Desktop is running"

### 2️⃣ Verificar Docker

```powershell
# Teste simples
docker --version

# Deve retornar algo como:
# Docker version 24.0.7, build afdd53b
```

### 3️⃣ Iniciar Evolution API

```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"
docker-compose up -d
```

**Resultado esperado**:
```
Creating network "evolution-net" with driver "bridge"
Creating evolution_postgres ... done
Creating evolution_redis    ... done
Creating evolution_api      ... done
Creating evolution_frontend ... done
```

### 4️⃣ Verificar se Está Rodando

```powershell
docker ps
```

**Resultado esperado**:
```
CONTAINER ID   IMAGE                              STATUS         PORTS                    NAMES
abc123def456   evoapicloud/evolution-api:latest   Up 10 seconds  127.0.0.1:8080->8080/tcp evolution_api
```

### 5️⃣ Aguardar Inicialização

```powershell
# Aguardar 15 segundos
Start-Sleep -Seconds 15

# Ou ver os logs em tempo real
docker logs evolution_api -f --tail 50
```

**Aguarde ver**:
```
> evolution-api@2.3.7 start:prod
> node dist/main

Environment variables loaded from .env
```

### 6️⃣ Configurar Webhook

```powershell
node configure-webhook.js
```

**Resultado esperado**:
```
✅ Webhook configurado com sucesso!

📋 Detalhes da configuração:
  URL: http://host.docker.internal:3006/webhooks/whatsapp
  Eventos:
    - MESSAGES_UPSERT (novas mensagens)
    - MESSAGES_UPDATE (atualizações)
    - CONNECTION_UPDATE (status da conexão)

🎉 Pronto! Agora as mensagens do WhatsApp serão enviadas para o WhatsApp Service!
```

---

## ⚠️ Opção 2: Se Docker Desktop Não Estiver Instalado

Se você **não tem** Docker Desktop instalado:

### Baixar e Instalar:

1. **Download**: https://www.docker.com/products/docker-desktop/
2. **Instalar**: Execute o instalador
3. **Reiniciar**: Reinicie o computador (se solicitado)
4. **Iniciar**: Abra o Docker Desktop
5. **Aguardar**: Primeira inicialização pode levar 1-2 minutos

---

## 🚀 Script Automatizado

Salve como `verificar-e-iniciar-docker.ps1`:

```powershell
# Script: Verificar e Iniciar Docker + Evolution API
# Autor: Sistema Sítio Multitrem

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  VERIFICANDO DOCKER" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Docker está rodando
$dockerProcess = Get-Process "*docker*" -ErrorAction SilentlyContinue

if ($dockerProcess) {
    Write-Host "✅ Docker Desktop está rodando!" -ForegroundColor Green
} else {
    Write-Host "❌ Docker Desktop NÃO está rodando!" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Iniciando Docker Desktop..." -ForegroundColor Yellow
    
    # Tentar iniciar Docker Desktop
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
    
    Write-Host "⏳ Aguardando Docker inicializar (30 segundos)..." -ForegroundColor Gray
    Start-Sleep -Seconds 30
    
    # Verificar novamente
    $dockerProcess = Get-Process "*docker*" -ErrorAction SilentlyContinue
    
    if ($dockerProcess) {
        Write-Host "✅ Docker Desktop iniciado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "❌ Não foi possível iniciar Docker Desktop automaticamente." -ForegroundColor Red
        Write-Host "   Por favor, inicie manualmente pelo menu Iniciar." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Pressione Enter após iniciar o Docker Desktop"
    }
}

Write-Host ""

# Testar Docker
Write-Host "🧪 Testando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker não responde. Aguarde mais alguns segundos..." -ForegroundColor Red
    Start-Sleep -Seconds 10
}

Write-Host ""

# Iniciar Evolution API
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  INICIANDO EVOLUTION API" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02\services\evolution-api"

Write-Host "📦 Iniciando containers..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "⏳ Aguardando inicialização (15 segundos)..." -ForegroundColor Gray
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "🔗 Configurando webhook..." -ForegroundColor Yellow
node configure-webhook.js

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ✅ CONCLUÍDO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Yellow
Write-Host "   1. Verificar se Evolution API está rodando:" -ForegroundColor White
Write-Host "      docker ps" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Acessar frontend:" -ForegroundColor White
Write-Host "      http://localhost:3001" -ForegroundColor Cyan
Write-Host ""
Write-Host "   3. Iniciar Agno e WhatsApp Service" -ForegroundColor White
Write-Host "      (veja GUIA_COMPLETO_INICIAR.md)" -ForegroundColor Gray
Write-Host ""
```

**Para executar**:
```powershell
cd "C:\Users\ilumi\Desktop\En\Adriano\E-commerce 02"
.\verificar-e-iniciar-docker.ps1
```

---

## 📊 Verificações Pós-Inicialização

### 1. Verificar containers:
```powershell
docker ps
```

Deve mostrar 4 containers:
- ✅ `evolution_api`
- ✅ `evolution_postgres`
- ✅ `evolution_redis`
- ✅ `evolution_frontend`

### 2. Verificar logs:
```powershell
docker logs evolution_api --tail 30
```

### 3. Testar API:
```powershell
curl http://localhost:8080
```

Deve retornar JSON com status da API.

### 4. Testar Frontend:
Abra no navegador: **http://localhost:3001**

---

## 🆘 Problemas Comuns

### Problema: "Docker Desktop não inicia"
**Soluções**:
1. Reinicie o computador
2. Verifique se virtualização está habilitada na BIOS
3. Reinstale o Docker Desktop

### Problema: "docker-compose: comando não encontrado"
**Solução**:
```powershell
# Use docker compose (sem hífen)
docker compose up -d
```

### Problema: "Porta 8080 já está em uso"
**Solução**:
```powershell
# Ver o que está usando a porta
netstat -ano | findstr :8080

# Matar o processo (substitua PID)
taskkill /PID <PID> /F
```

### Problema: "Containers não iniciam"
**Solução**:
```powershell
# Parar tudo
docker-compose down

# Remover volumes (CUIDADO: apaga dados)
docker-compose down -v

# Iniciar novamente
docker-compose up -d
```

---

## ✅ Checklist Final

- [ ] Docker Desktop instalado
- [ ] Docker Desktop iniciado (ícone verde na bandeja)
- [ ] `docker --version` funciona
- [ ] `docker ps` funciona (sem erros)
- [ ] Evolution API rodando (`docker ps` mostra 4 containers)
- [ ] Webhook configurado (sem erros)
- [ ] Frontend acessível em http://localhost:3001

**Pronto para continuar!** 🚀



