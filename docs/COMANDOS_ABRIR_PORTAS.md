# 🔓 Comandos para Abrir Portas no Windows

Este documento contém os comandos para abrir todas as portas necessárias no Firewall do Windows.

## 🚀 Método Rápido (Recomendado)

Use o script PowerShell automatizado:

```powershell
# Execute como Administrador
PowerShell -ExecutionPolicy Bypass -File .\scripts\abrir-portas-firewall.ps1
```

---

## 📝 Método Manual (Comandos Individuais)

Se preferir abrir as portas manualmente, execute cada comando abaixo **como Administrador** no PowerShell:

### Frontend
```powershell
New-NetFirewallRule -DisplayName "Sitio Multitrem - Frontend Next.js" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow
```

### Gateway
```powershell
New-NetFirewallRule -DisplayName "Sitio Multitrem - API Gateway" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

### Microserviços
```powershell
# Product Service
New-NetFirewallRule -DisplayName "Sitio Multitrem - Product Service" -Direction Inbound -Protocol TCP -LocalPort 3001 -Action Allow

# Cart Service
New-NetFirewallRule -DisplayName "Sitio Multitrem - Cart Service" -Direction Inbound -Protocol TCP -LocalPort 3002 -Action Allow

# Order Service
New-NetFirewallRule -DisplayName "Sitio Multitrem - Order Service" -Direction Inbound -Protocol TCP -LocalPort 3003 -Action Allow

# Payment Service
New-NetFirewallRule -DisplayName "Sitio Multitrem - Payment Service" -Direction Inbound -Protocol TCP -LocalPort 3004 -Action Allow

# Auth Service
New-NetFirewallRule -DisplayName "Sitio Multitrem - Auth Service" -Direction Inbound -Protocol TCP -LocalPort 3005 -Action Allow

# WhatsApp Service
New-NetFirewallRule -DisplayName "Sitio Multitrem - WhatsApp Service" -Direction Inbound -Protocol TCP -LocalPort 3006 -Action Allow

# AI Service
New-NetFirewallRule -DisplayName "Sitio Multitrem - AI Service" -Direction Inbound -Protocol TCP -LocalPort 3007 -Action Allow
```

### Bancos de Dados
```powershell
# PostgreSQL
New-NetFirewallRule -DisplayName "Sitio Multitrem - PostgreSQL" -Direction Inbound -Protocol TCP -LocalPort 5432 -Action Allow

# Redis
New-NetFirewallRule -DisplayName "Sitio Multitrem - Redis" -Direction Inbound -Protocol TCP -LocalPort 6379 -Action Allow
```

### Opcionais
```powershell
# Keycloak
New-NetFirewallRule -DisplayName "Sitio Multitrem - Keycloak" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow

# Evolution API
New-NetFirewallRule -DisplayName "Sitio Multitrem - Evolution API" -Direction Inbound -Protocol TCP -LocalPort 8081 -Action Allow
```

---

## 🔍 Verificar Portas Abertas

### Verificar regras criadas
```powershell
Get-NetFirewallRule -DisplayName "Sitio Multitrem*" | Format-Table DisplayName, Enabled, Direction, Action
```

### Verificar se portas estão em uso
```powershell
# Verificar porta específica
Get-NetTCPConnection -LocalPort 3000

# Verificar todas as portas do sistema
Get-NetTCPConnection | Where-Object {$_.LocalPort -in @(3000,3001,3002,3003,3004,3005,3006,3007,8000,5432,6379,8080,8081)} | Format-Table LocalPort, State, OwningProcess
```

### Usar o script de verificação
```powershell
.\scripts\verificar-portas-firewall.ps1
```

---

## 🗑️ Remover Portas

### Remover todas as regras do Sítio Multitrem
```powershell
Get-NetFirewallRule -DisplayName "Sitio Multitrem*" | Remove-NetFirewallRule
```

### Remover regra específica
```powershell
Remove-NetFirewallRule -DisplayName "Sitio Multitrem - Frontend Next.js"
```

### Usar o script de remoção
```powershell
# Execute como Administrador
PowerShell -ExecutionPolicy Bypass -File .\scripts\remover-portas-firewall.ps1
```

---

## ⚠️ Importante

1. **Privilégios de Administrador**: Os comandos `New-NetFirewallRule` e `Remove-NetFirewallRule` precisam ser executados como Administrador.

2. **Como executar como Administrador**:
   - Clique com botão direito no PowerShell
   - Selecione "Executar como Administrador"
   - Ou use: `Start-Process powershell -Verb RunAs`

3. **Desenvolvimento Local**: Em desenvolvimento local, normalmente não é necessário abrir portas no firewall, pois o Windows permite conexões locais por padrão.

4. **Produção**: Em servidores ou máquinas com firewall restritivo, você precisa abrir essas portas.

---

## 🐛 Solução de Problemas

### Erro: "Access Denied"
- **Causa**: Não está executando como Administrador
- **Solução**: Execute o PowerShell como Administrador

### Erro: "Rule already exists"
- **Causa**: A regra já existe no firewall
- **Solução**: Ignore o erro ou remova a regra existente primeiro

### Porta ainda bloqueada após criar regra
- **Causa**: Pode haver outra regra bloqueando ou o serviço não está rodando
- **Solução**: 
  1. Verifique se o serviço está rodando na porta
  2. Verifique outras regras de firewall que possam estar bloqueando
  3. Reinicie o serviço

---

## 📚 Comandos Úteis Adicionais

### Listar todas as regras de firewall
```powershell
Get-NetFirewallRule | Format-Table DisplayName, Enabled, Direction, Action
```

### Habilitar/Desabilitar regra específica
```powershell
# Desabilitar
Disable-NetFirewallRule -DisplayName "Sitio Multitrem - Frontend Next.js"

# Habilitar
Enable-NetFirewallRule -DisplayName "Sitio Multitrem - Frontend Next.js"
```

### Verificar status do Firewall
```powershell
Get-NetFirewallProfile | Format-Table Name, Enabled
```

---

**Última atualização**: 2024



