# Script de inicialização do Telegram Operations Service
# Ativa o ambiente virtual e inicia o servidor Uvicorn

Write-Host "🚀 Iniciando Telegram Operations Service..." -ForegroundColor Green

# Verificar se estamos no diretório correto
$currentDir = Get-Location
if (-not $currentDir.Path.EndsWith("telegram_operations")) {
    Write-Host "⚠️  Aviso: Execute este script a partir do diretório telegram_operations" -ForegroundColor Yellow
    Write-Host "📁 Diretório atual: $($currentDir.Path)" -ForegroundColor Yellow
}

# Verificar se existe ambiente virtual
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Ambiente virtual não encontrado!" -ForegroundColor Red
    Write-Host "💡 Criando ambiente virtual..." -ForegroundColor Yellow
    
    # Criar ambiente virtual
    python -m venv venv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro ao criar ambiente virtual" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Ambiente virtual criado com sucesso!" -ForegroundColor Green
    Write-Host "💡 Instalando dependências..." -ForegroundColor Yellow
    
    # Ativar e instalar dependências
    & .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro ao instalar dependências" -ForegroundColor Red
        exit 1
    }
}

# Ativar ambiente virtual
Write-Host "🔧 Ativando ambiente virtual..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Verificar se a ativação foi bem-sucedida
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao ativar ambiente virtual" -ForegroundColor Red
    exit 1
}

# Verificar se existe arquivo .env
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Arquivo .env não encontrado!" -ForegroundColor Yellow
    if (Test-Path "env.example") {
        Write-Host "💡 Copiando env.example para .env..." -ForegroundColor Yellow
        Copy-Item "env.example" ".env"
        Write-Host "✅ Arquivo .env criado. Configure as variáveis necessárias!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Arquivo env.example não encontrado. Configure manualmente o .env" -ForegroundColor Yellow
    }
}

# Iniciar aplicação Uvicorn
Write-Host "🚀 Iniciando servidor Uvicorn na porta 8021..." -ForegroundColor Green
Write-Host "📖 Documentação disponível em: http://localhost:8021/docs" -ForegroundColor Cyan
Write-Host "🔍 Health check: http://localhost:8021/health" -ForegroundColor Cyan
Write-Host "📱 Telegram Service: http://localhost:8021" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Yellow
Write-Host ""

python main.py
