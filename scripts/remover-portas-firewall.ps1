# Script para remover regras de firewall do Sítio Multitrem
# Execute como Administrador: PowerShell -ExecutionPolicy Bypass -File .\scripts\remover-portas-firewall.ps1

Write-Host "`n=== REMOVENDO PORTAS DO FIREWALL DO WINDOWS ===" -ForegroundColor Cyan
Write-Host "Este script requer privilégios de Administrador!`n" -ForegroundColor Yellow

# Verificar se está executando como Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERRO: Este script precisa ser executado como Administrador!" -ForegroundColor Red
    Write-Host "Clique com botão direito no PowerShell e selecione 'Executar como Administrador'" -ForegroundColor Yellow
    exit 1
}

# Buscar todas as regras do Sítio Multitrem
$regras = Get-NetFirewallRule -DisplayName "Sitio Multitrem*" -ErrorAction SilentlyContinue

if (-not $regras) {
    Write-Host "⚠ Nenhuma regra do Sítio Multitrem encontrada no Firewall." -ForegroundColor Yellow
    exit 0
}

Write-Host "`n📋 Regras encontradas:" -ForegroundColor Yellow
$regras | Format-Table DisplayName, Enabled, Direction, Action -AutoSize

Write-Host "`n⚠ ATENÇÃO: Você está prestes a remover as seguintes regras:" -ForegroundColor Red
foreach ($regra in $regras) {
    Write-Host "  - $($regra.DisplayName)" -ForegroundColor Yellow
}

$confirmacao = Read-Host "`nDeseja continuar? (S/N)"

if ($confirmacao -ne "S" -and $confirmacao -ne "s") {
    Write-Host "`nOperação cancelada." -ForegroundColor Yellow
    exit 0
}

Write-Host "`n🗑 Removendo regras..." -ForegroundColor Cyan

$removidas = 0
foreach ($regra in $regras) {
    try {
        Remove-NetFirewallRule -DisplayName $regra.DisplayName -ErrorAction Stop
        Write-Host "  ✅ Removida: $($regra.DisplayName)" -ForegroundColor Green
        $removidas++
    } catch {
        Write-Host "  ❌ Erro ao remover $($regra.DisplayName): $_" -ForegroundColor Red
    }
}

Write-Host "`n=== CONCLUSÃO ===" -ForegroundColor Green
Write-Host "$removidas regra(s) removida(s) com sucesso!" -ForegroundColor White






























