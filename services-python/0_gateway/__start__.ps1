# Script de inicialização do Gateway Service
# Ativa o ambiente virtual e inicia o servidor Uvicorn

Write-Host "🚀 Iniciando Gateway Service..." -ForegroundColor Green

# Ativar ambiente virtual
Write-Host "🔧 Ativando ambiente virtual..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Verificar se a ativação foi bem-sucedida
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao ativar ambiente virtual" -ForegroundColor Red
    exit 1
}

# Iniciar aplicação Uvicorn
Write-Host "🚀 Iniciando servidor Uvicorn na porta 8000..." -ForegroundColor Green
Write-Host "📖 Documentação disponível em: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔍 Health check: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000







