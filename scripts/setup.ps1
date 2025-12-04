# Script de setup do projeto Sítio Multitrem (PowerShell)
# Verifica dependências e configura o ambiente

Write-Host "🌿 Sítio Multitrem - Setup" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green
Write-Host ""

# Verificar Node.js
Write-Host "Verificando Node.js... " -NoNewline
try {
    $nodeVersion = node -v
    Write-Host "✓ $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js não encontrado. Instale Node.js 18+" -ForegroundColor Red
    exit 1
}

# Verificar npm
Write-Host "Verificando npm... " -NoNewline
try {
    $npmVersion = npm -v
    Write-Host "✓ $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ npm não encontrado" -ForegroundColor Red
    exit 1
}

# Verificar PostgreSQL
Write-Host "Verificando PostgreSQL... " -NoNewline
try {
    $pgVersion = psql --version
    Write-Host "✓ PostgreSQL encontrado" -ForegroundColor Green
} catch {
    Write-Host "⚠ PostgreSQL não encontrado. Você precisará instalá-lo." -ForegroundColor Yellow
}

# Verificar Redis
Write-Host "Verificando Redis... " -NoNewline
try {
    $redisVersion = redis-cli --version
    Write-Host "✓ Redis encontrado" -ForegroundColor Green
} catch {
    Write-Host "⚠ Redis não encontrado. Você precisará instalá-lo." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 Instalando dependências..." -ForegroundColor Cyan
npm install

Write-Host ""
Write-Host "🔨 Construindo shared package..." -ForegroundColor Cyan
Set-Location shared
npm install
npm run build
Set-Location ..

Write-Host ""
Write-Host "📋 Copiando arquivos .env.example..." -ForegroundColor Cyan

# Copiar .env.example para .env em cada serviço (se não existir)
$services = @("product-service", "cart-service", "order-service", "payment-service", "auth-service", "whatsapp-service", "ai-service", "gateway")

foreach ($service in $services) {
    $envExample = "services\$service\.env.example"
    $envFile = "services\$service\.env"
    
    if (Test-Path $envExample) {
        if (-not (Test-Path $envFile)) {
            Copy-Item $envExample $envFile
            Write-Host "  ✓ Criado $envFile" -ForegroundColor Green
        }
    }
}

# Copiar .env.example do frontend (se existir)
if (Test-Path "frontend\.env.example") {
    if (-not (Test-Path "frontend\.env")) {
        Copy-Item "frontend\.env.example" "frontend\.env"
        Write-Host "  ✓ Criado frontend\.env" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "✓ Setup concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Configure as variáveis de ambiente nos arquivos .env"
Write-Host "2. Inicie PostgreSQL e Redis"
Write-Host "3. Execute: npm run dev"
Write-Host ""




