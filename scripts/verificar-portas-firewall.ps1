# Script para verificar portas abertas no Firewall do Windows

Write-Host "`n=== VERIFICANDO PORTAS NO FIREWALL ===" -ForegroundColor Cyan

# Lista de portas do sistema
$portas = @(
    @{Nome="Frontend Next.js"; Porta=3000},
    @{Nome="API Gateway"; Porta=8000},
    @{Nome="Product Service"; Porta=3001},
    @{Nome="Cart Service"; Porta=3002},
    @{Nome="Order Service"; Porta=3003},
    @{Nome="Payment Service"; Porta=3004},
    @{Nome="Auth Service"; Porta=3005},
    @{Nome="WhatsApp Service"; Porta=3006},
    @{Nome="AI Service"; Porta=3007},
    @{Nome="PostgreSQL"; Porta=5432},
    @{Nome="Redis"; Porta=6379},
    @{Nome="Keycloak"; Porta=8080},
    @{Nome="Evolution API"; Porta=8081}
)

Write-Host "`nVerificando regras do Firewall..." -ForegroundColor Yellow
$regras = Get-NetFirewallRule -DisplayName "Sitio Multitrem*" -ErrorAction SilentlyContinue

if ($regras) {
    Write-Host "`n[OK] Regras encontradas no Firewall:" -ForegroundColor Green
    $regras | Format-Table DisplayName, Enabled, Direction, Action -AutoSize
} else {
    Write-Host "`n[AVISO] Nenhuma regra do Sitio Multitrem encontrada no Firewall." -ForegroundColor Yellow
    Write-Host "Execute o script 'abrir-portas-firewall.ps1' como Administrador para criar as regras." -ForegroundColor Cyan
}

Write-Host "`nVerificando se as portas estao em uso..." -ForegroundColor Yellow
Write-Host ""

foreach ($porta in $portas) {
    $conexoes = Get-NetTCPConnection -LocalPort $porta.Porta -ErrorAction SilentlyContinue
    
    if ($conexoes) {
        $status = $conexoes | Select-Object -First 1 -ExpandProperty State
        Write-Host "  [OK] Porta $($porta.Porta) ($($porta.Nome)): $status" -ForegroundColor Green
    } else {
        Write-Host "  [-] Porta $($porta.Porta) ($($porta.Nome)): Nao em uso" -ForegroundColor Gray
    }
}

Write-Host "`n=== CONCLUSÃO ===" -ForegroundColor Cyan
Write-Host "Verificação concluída!" -ForegroundColor White

