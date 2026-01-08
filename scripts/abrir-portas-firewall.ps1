# Script para abrir portas no Firewall do Windows
# Execute como Administrador: PowerShell -ExecutionPolicy Bypass -File .\scripts\abrir-portas-firewall.ps1

Write-Host "`n=== ABRINDO PORTAS NO FIREWALL DO WINDOWS ===" -ForegroundColor Cyan
Write-Host "Este script requer privilegios de Administrador!`n" -ForegroundColor Yellow

# Verificar se está executando como Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERRO: Este script precisa ser executado como Administrador!" -ForegroundColor Red
    Write-Host "Clique com botão direito no PowerShell e selecione 'Executar como Administrador'" -ForegroundColor Yellow
    exit 1
}

# Função para adicionar regra de firewall
function Add-FirewallRule {
    param(
        [string]$Name,
        [int]$Port,
        [string]$Protocol = "TCP",
        [string]$Description = ""
    )
    
    $ruleName = "Sitio Multitrem - $Name"
    
    # Verificar se a regra já existe
    $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    
    if ($existingRule) {
        Write-Host "  [AVISO] Regra ja existe: $ruleName" -ForegroundColor Yellow
        return
    }
    
    try {
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Direction Inbound `
            -Protocol $Protocol `
            -LocalPort $Port `
            -Action Allow `
            -Description $Description `
            -ErrorAction Stop
        
        Write-Host "  [OK] Porta $Port ($Name) aberta com sucesso!" -ForegroundColor Green
    } catch {
        Write-Host "  [ERRO] Erro ao abrir porta $Port ($Name): $_" -ForegroundColor Red
    }
}

Write-Host "`nAbrindo portas do Frontend..." -ForegroundColor Cyan
Add-FirewallRule -Name "Frontend Next.js" -Port 3000 -Description "Frontend Next.js do Sitio Multitrem"

Write-Host "`nAbrindo portas do Gateway..." -ForegroundColor Cyan
Add-FirewallRule -Name "API Gateway" -Port 8000 -Description "API Gateway do Sitio Multitrem"

Write-Host "`nAbrindo portas dos Microservicos..." -ForegroundColor Cyan
Add-FirewallRule -Name "Product Service" -Port 3001 -Description "Product Service - Gerenciamento de produtos"
Add-FirewallRule -Name "Cart Service" -Port 3002 -Description "Cart Service - Gerenciamento de carrinho"
Add-FirewallRule -Name "Order Service" -Port 3003 -Description "Order Service - Gerenciamento de pedidos"
Add-FirewallRule -Name "Payment Service" -Port 3004 -Description "Payment Service - Processamento de pagamentos"
Add-FirewallRule -Name "Auth Service" -Port 3005 -Description "Auth Service - Autenticacao e autorizacao"
Add-FirewallRule -Name "WhatsApp Service" -Port 3006 -Description "WhatsApp Service - Integracao com WhatsApp"
Add-FirewallRule -Name "AI Service" -Port 3007 -Description "AI Service - Assistente de vendas com IA"

Write-Host "`nAbrindo portas dos Bancos de Dados..." -ForegroundColor Cyan
Add-FirewallRule -Name "PostgreSQL" -Port 5432 -Description "PostgreSQL - Banco de dados principal"
Add-FirewallRule -Name "Redis" -Port 6379 -Description "Redis - Cache e armazenamento de sessoes"

Write-Host "`nAbrindo portas Opcionais..." -ForegroundColor Cyan
Add-FirewallRule -Name "Keycloak" -Port 8080 -Description "Keycloak - Servidor de autenticação (opcional)"
Add-FirewallRule -Name "Evolution API" -Port 8081 -Description "Evolution API - Integração WhatsApp (opcional)"

Write-Host "`n=== CONCLUSÃO ===" -ForegroundColor Green
Write-Host "Todas as portas foram configuradas no Firewall do Windows!" -ForegroundColor White
Write-Host "`nPara verificar as regras criadas, execute:" -ForegroundColor Yellow
$cmd1 = "Get-NetFirewallRule -DisplayName 'Sitio Multitrem*' | Format-Table DisplayName, Enabled, Direction, Action"
Write-Host "  $cmd1" -ForegroundColor Cyan
Write-Host "`nPara remover todas as regras, execute:" -ForegroundColor Yellow
$cmd2 = "Get-NetFirewallRule -DisplayName 'Sitio Multitrem*' | Remove-NetFirewallRule"
Write-Host "  $cmd2" -ForegroundColor Cyan

