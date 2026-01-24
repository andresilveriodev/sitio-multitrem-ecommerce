# ============================================
# 🔧 APLICAR CONFIGURAÇÃO ENV UNIFICADA
# ============================================

Write-Host "🔧 Aplicando Configuração ENV Unificada para Docker..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Verificar se estamos no diretório correto
$currentDir = Get-Location
Write-Host "📂 Diretório atual: $currentDir" -ForegroundColor Yellow

# Verificar se o arquivo unificado existe
if (-not (Test-Path "env.docker.unified")) {
    Write-Host "❌ ERRO: Arquivo env.docker.unified não encontrado!" -ForegroundColor Red
    Write-Host "   Execute este script no diretório raiz do projeto." -ForegroundColor Red
    exit 1
}

Write-Host "" -ForegroundColor White

# ============================================
# PASSO 1: Configurar .env principal
# ============================================
Write-Host "📋 PASSO 1: Configurando .env principal..." -ForegroundColor Green

try {
    Copy-Item "env.docker.unified" ".env" -Force
    Write-Host "✅ Arquivo .env principal criado com sucesso!" -ForegroundColor Green
} catch {
    Write-Host "❌ ERRO ao criar .env principal: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ============================================
# PASSO 2: Configurar .env do AI Agent  
# ============================================
Write-Host "" -ForegroundColor White
Write-Host "🤖 PASSO 2: Configurando .env do AI Agent..." -ForegroundColor Green

$aiAgentPath = "services\ai-service\agno_agente_horta_multitrem"

if (Test-Path $aiAgentPath) {
    try {
        Copy-Item "$aiAgentPath\env.docker" "$aiAgentPath\.env" -Force
        Write-Host "✅ Arquivo .env do AI Agent configurado!" -ForegroundColor Green
    } catch {
        Write-Host "❌ ERRO ao configurar .env do AI Agent: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  Diretório do AI Agent não encontrado: $aiAgentPath" -ForegroundColor Yellow
}

# ============================================
# PASSO 3: Verificar configurações
# ============================================
Write-Host "" -ForegroundColor White
Write-Host "🔍 PASSO 3: Verificando configurações..." -ForegroundColor Green

# Verificar se .env foi criado
if (Test-Path ".env") {
    $envSize = (Get-Item ".env").Length
    Write-Host "✅ Arquivo .env criado: $envSize bytes" -ForegroundColor Green
    
    # Verificar se contém configurações essenciais
    $envContent = Get-Content ".env" -Raw
    
    $checks = @(
        @{Name="OPENAI_API_KEY"; Pattern="OPENAI_API_KEY=sk-"; Status=""},
        @{Name="EVOLUTION_API_KEY"; Pattern="EVOLUTION_API_KEY=W7F"; Status=""},
        @{Name="DATABASE_URL"; Pattern="DATABASE_URL=postgresql://"; Status=""},
        @{Name="REDIS_URL"; Pattern="REDIS_URL=redis://"; Status=""}
    )
    
    Write-Host "" -ForegroundColor White
    Write-Host "📊 Status das configurações:" -ForegroundColor Cyan
    
    foreach ($check in $checks) {
        if ($envContent -match [regex]::Escape($check.Pattern)) {
            Write-Host "   ✅ $($check.Name)" -ForegroundColor Green
        } else {
            Write-Host "   ❌ $($check.Name)" -ForegroundColor Red
        }
    }
} else {
    Write-Host "❌ ERRO: Arquivo .env não foi criado!" -ForegroundColor Red
}

# ============================================
# PASSO 4: Próximos passos
# ============================================
Write-Host "" -ForegroundColor White
Write-Host "📝 PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host "1. ⚠️  Edite o arquivo .env e configure:" -ForegroundColor Yellow
Write-Host "   • MERCADOPAGO_ACCESS_TOKEN=seu_token_mercadopago" -ForegroundColor Yellow
Write-Host "   • JWT_SECRET=seu_jwt_secret_seguro" -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "2. 🐳 Execute o Docker:" -ForegroundColor Yellow
Write-Host "   docker-compose up -d" -ForegroundColor Gray
Write-Host "" -ForegroundColor White
Write-Host "3. 🔍 Verifique os logs:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f" -ForegroundColor Gray

Write-Host "" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "🎉 CONFIGURAÇÃO UNIFICADA APLICADA!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

# Perguntar se quer abrir o arquivo .env para edição
Write-Host "" -ForegroundColor White
$openEnv = Read-Host "💡 Deseja abrir o arquivo .env para editar as chaves? (y/n)"

if ($openEnv -eq "y" -or $openEnv -eq "Y" -or $openEnv -eq "yes") {
    try {
        notepad .env
        Write-Host "📝 Arquivo .env aberto no Notepad!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Não foi possível abrir o Notepad. Edite manualmente o arquivo .env" -ForegroundColor Yellow
    }
}