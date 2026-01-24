# ============================================
# 🔍 VERIFICAR CONFIGURAÇÃO ENV UNIFICADA
# ============================================

Write-Host "🔍 Verificando Configuração ENV Unificada..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Função para verificar se uma linha existe no arquivo
function Test-EnvVariable {
    param(
        [string]$FilePath,
        [string]$VariableName,
        [string]$Pattern = ""
    )
    
    if (-not (Test-Path $FilePath)) {
        return @{Status="ERRO"; Message="Arquivo não encontrado"}
    }
    
    $content = Get-Content $FilePath -Raw
    
    if ($Pattern -ne "") {
        if ($content -match [regex]::Escape($Pattern)) {
            return @{Status="OK"; Message="Configurada"}
        } else {
            return @{Status="AVISO"; Message="Não configurada ou padrão não encontrado"}
        }
    } else {
        if ($content -match "^$VariableName=.+$") {
            return @{Status="OK"; Message="Presente"}
        } else {
            return @{Status="ERRO"; Message="Ausente"}
        }
    }
}

# ============================================
# VERIFICAR ARQUIVO .ENV PRINCIPAL
# ============================================
Write-Host "📋 Verificando .env principal..." -ForegroundColor Green
Write-Host "" -ForegroundColor White

$mainEnvChecks = @(
    @{Name="OPENAI_API_KEY"; Pattern="OPENAI_API_KEY=sk-"; Description="Chave OpenAI"},
    @{Name="EVOLUTION_API_KEY"; Pattern="EVOLUTION_API_KEY=W7F"; Description="Chave Evolution API"},
    @{Name="DATABASE_URL"; Pattern="DATABASE_URL=postgresql://sitio_user"; Description="URL PostgreSQL Sitio"},
    @{Name="REDIS_URL"; Pattern="REDIS_URL=redis://:sitio_redis_pass"; Description="URL Redis Sitio"},
    @{Name="MERCADOPAGO_ACCESS_TOKEN"; Pattern="MERCADOPAGO_ACCESS_TOKEN=seu_token"; Description="Token Mercado Pago"},
    @{Name="JWT_SECRET"; Pattern="JWT_SECRET=meu_jwt_secret"; Description="JWT Secret"},
    @{Name="WEBHOOK_GLOBAL_URL"; Pattern="http://whatsapp-service:3006"; Description="Webhook URL Docker"},
    @{Name="AI_SERVICE_URL"; Pattern="http://ai-service:3007"; Description="AI Service URL Docker"}
)

foreach ($check in $mainEnvChecks) {
    $result = Test-EnvVariable -FilePath ".env" -VariableName $check.Name -Pattern $check.Pattern
    
    switch ($result.Status) {
        "OK" { Write-Host "   ✅ $($check.Description): $($result.Message)" -ForegroundColor Green }
        "AVISO" { Write-Host "   ⚠️  $($check.Description): $($result.Message)" -ForegroundColor Yellow }
        "ERRO" { Write-Host "   ❌ $($check.Description): $($result.Message)" -ForegroundColor Red }
    }
}

# ============================================
# VERIFICAR ARQUIVO .ENV AI AGENT
# ============================================
Write-Host "" -ForegroundColor White
Write-Host "🤖 Verificando .env AI Agent..." -ForegroundColor Green
Write-Host "" -ForegroundColor White

$aiEnvPath = "services\ai-service\agno_agente_horta_multitrem\.env"
$aiEnvChecks = @(
    @{Name="OPENAI_API_KEY"; Pattern="OPENAI_API_KEY=sk-"; Description="Chave OpenAI AI Agent"},
    @{Name="GOOGLE_CREDENTIALS_PATH"; Pattern="client_secret_"; Description="Credenciais Google"},
    @{Name="DATABASE_URL"; Pattern="postgresql://sitio_user"; Description="Database URL"}
)

foreach ($check in $aiEnvChecks) {
    $result = Test-EnvVariable -FilePath $aiEnvPath -VariableName $check.Name -Pattern $check.Pattern
    
    switch ($result.Status) {
        "OK" { Write-Host "   ✅ $($check.Description): $($result.Message)" -ForegroundColor Green }
        "AVISO" { Write-Host "   ⚠️  $($check.Description): $($result.Message)" -ForegroundColor Yellow }
        "ERRO" { Write-Host "   ❌ $($check.Description): $($result.Message)" -ForegroundColor Red }
    }
}

# ============================================
# VERIFICAR DOCKER COMPOSE
# ============================================
Write-Host "" -ForegroundColor White
Write-Host "🐳 Verificando Docker Compose..." -ForegroundColor Green
Write-Host "" -ForegroundColor White

if (Test-Path "docker-compose.yml") {
    Write-Host "   ✅ docker-compose.yml encontrado" -ForegroundColor Green
    
    # Verificar se Docker está rodando
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Docker Desktop está rodando" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Docker Desktop não está rodando" -ForegroundColor Red
        }
    } catch {
        Write-Host "   ❌ Docker não está instalado ou não está no PATH" -ForegroundColor Red
    }
} else {
    Write-Host "   ❌ docker-compose.yml não encontrado" -ForegroundColor Red
}

# ============================================
# VERIFICAR PORTAS
# ============================================
Write-Host "" -ForegroundColor White
Write-Host "🚪 Verificando portas em uso..." -ForegroundColor Green
Write-Host "" -ForegroundColor White

$ports = @(3000, 8000, 3001, 3002, 3003, 3004, 3005, 3006, 3007, 5432, 6379, 8080, 8081)

foreach ($port in $ports) {
    try {
        $connection = Test-NetConnection -ComputerName "localhost" -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet
        if ($connection.TcpTestSucceeded) {
            Write-Host "   ⚠️  Porta $port está em uso" -ForegroundColor Yellow
        } else {
            Write-Host "   ✅ Porta $port disponível" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ✅ Porta $port disponível" -ForegroundColor Green
    }
}

# ============================================
# RESUMO E PRÓXIMOS PASSOS
# ============================================
Write-Host "" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "📊 RESUMO DA VERIFICAÇÃO" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

Write-Host "" -ForegroundColor White
Write-Host "🎯 AÇÕES NECESSÁRIAS:" -ForegroundColor Yellow

# Verificar se precisa configurar chaves
$needsConfig = @()

$envContent = ""
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
}

if ($envContent -match "MERCADOPAGO_ACCESS_TOKEN=seu_token") {
    $needsConfig += "Mercado Pago Token"
}

if ($envContent -match "JWT_SECRET=meu_jwt_secret") {
    $needsConfig += "JWT Secret"
}

if ($needsConfig.Count -gt 0) {
    Write-Host "   ⚠️  Configure as seguintes chaves no arquivo .env:" -ForegroundColor Yellow
    foreach ($config in $needsConfig) {
        Write-Host "      • $config" -ForegroundColor Yellow
    }
    Write-Host "" -ForegroundColor White
} else {
    Write-Host "   ✅ Todas as chaves essenciais estão configuradas!" -ForegroundColor Green
}

Write-Host "🚀 COMANDOS PARA TESTAR:" -ForegroundColor Cyan
Write-Host "   docker-compose up -d postgres redis" -ForegroundColor Gray
Write-Host "   docker-compose logs postgres redis" -ForegroundColor Gray
Write-Host "   docker-compose up -d" -ForegroundColor Gray

Write-Host "" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "🎉 VERIFICAÇÃO CONCLUÍDA!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan