# Script para iniciar o projeto em modo desenvolvimento (PowerShell)
# Inicia PostgreSQL, Redis e todos os serviços

Write-Host "🌿 Sítio Multitrem - Iniciando Desenvolvimento" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""

# Verificar se PostgreSQL está rodando
Write-Host "Verificando PostgreSQL... " -NoNewline
try {
    $pgTest = pg_isready 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Rodando" -ForegroundColor Green
    } else {
        Write-Host "⚠ Não está rodando. Inicie o PostgreSQL antes de continuar." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ pg_isready não encontrado. Verifique manualmente." -ForegroundColor Yellow
}

# Verificar se Redis está rodando
Write-Host "Verificando Redis... " -NoNewline
try {
    $redisTest = redis-cli ping 2>&1
    if ($redisTest -eq "PONG") {
        Write-Host "✓ Rodando" -ForegroundColor Green
    } else {
        Write-Host "⚠ Não está rodando. Inicie o Redis antes de continuar." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ redis-cli não encontrado. Verifique manualmente." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 Iniciando serviços..." -ForegroundColor Cyan
Write-Host ""

# Iniciar todos os serviços
npm run dev













