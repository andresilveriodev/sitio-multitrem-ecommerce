# Script PowerShell para executar o sistema rapidamente
# Execute este script com: .\EXECUTAR_AGORA.ps1

# Adicionar UV ao PATH (se necessário)
$env:Path = "C:\Users\ilumi\.local\bin;$env:Path"

# Navegar até a pasta do projeto
Set-Location "c:\Users\ilumi\Desktop\En\Adriano\Criando Agentes de IA com Agno (1)\agente_horta_multitrem"

Write-Host "🌱 Sistema de Agentes - Horta Orgânica" -ForegroundColor Green
Write-Host ""

# Verificar se o arquivo .env existe
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Arquivo .env não encontrado. Criando a partir do exemplo..." -ForegroundColor Yellow
    Copy-Item env.example .env
    Write-Host "✅ Arquivo .env criado!" -ForegroundColor Green
    Write-Host "⚠️  IMPORTANTE: Edite o arquivo .env e adicione sua OPENAI_API_KEY" -ForegroundColor Red
    Write-Host ""
    Write-Host "Pressione Enter após configurar o .env para continuar..."
    Read-Host
}

# Verificar se o banco de dados existe
if (-not (Test-Path "tmp\data.db")) {
    Write-Host "📊 Inicializando banco de dados..." -ForegroundColor Cyan
    uv run python init_db.py
    Write-Host ""
}

# Executar o script de exemplos
Write-Host "🚀 Executando exemplos de uso..." -ForegroundColor Cyan
Write-Host ""
uv run python exemplos_uso.py
