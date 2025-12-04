# Script para criar o banco de dados sitio_multitrem no PostgreSQL
# Execute este script após instalar o PostgreSQL

param(
    [string]$PgVersion = "15",
    [string]$DbName = "sitio_multitrem",
    [string]$DbUser = "postgres"
)

Write-Host "`n=== CRIAR BANCO DE DADOS SITIO_MULTITREM ===" -ForegroundColor Cyan
Write-Host ""

# Caminhos possíveis do PostgreSQL
$possiblePaths = @(
    "C:\Program Files\PostgreSQL\$PgVersion\bin",
    "C:\Program Files (x86)\PostgreSQL\$PgVersion\bin",
    "C:\PostgreSQL\$PgVersion\bin"
)

$psqlPath = $null

# Procurar psql.exe
foreach ($path in $possiblePaths) {
    $testPath = Join-Path $path "psql.exe"
    if (Test-Path $testPath) {
        $psqlPath = $testPath
        Write-Host "✓ PostgreSQL encontrado em: $path" -ForegroundColor Green
        break
    }
}

# Se não encontrou, tentar encontrar automaticamente
if (-not $psqlPath) {
    Write-Host "Procurando PostgreSQL instalado..." -ForegroundColor Yellow
    
    $pgDirs = Get-ChildItem "C:\Program Files" -Filter "PostgreSQL*" -Directory -ErrorAction SilentlyContinue
    if ($pgDirs) {
        foreach ($pgDir in $pgDirs) {
            $binPath = Join-Path $pgDir.FullName "bin\psql.exe"
            if (Test-Path $binPath) {
                $psqlPath = $binPath
                Write-Host "✓ PostgreSQL encontrado em: $($pgDir.FullName)" -ForegroundColor Green
                break
            }
        }
    }
}

# Se ainda não encontrou, pedir ao usuário
if (-not $psqlPath) {
    Write-Host "✗ PostgreSQL não encontrado automaticamente." -ForegroundColor Red
    Write-Host "`nPor favor, informe o caminho completo do psql.exe:" -ForegroundColor Yellow
    Write-Host "Exemplo: C:\Program Files\PostgreSQL\15\bin\psql.exe" -ForegroundColor Gray
    $customPath = Read-Host "Caminho"
    
    if (Test-Path $customPath) {
        $psqlPath = $customPath
    } else {
        Write-Host "✗ Caminho inválido. Encerrando." -ForegroundColor Red
        exit 1
    }
}

# Verificar se o serviço PostgreSQL está rodando
Write-Host "`nVerificando se o serviço PostgreSQL está rodando..." -ForegroundColor Yellow
$pgService = Get-Service -Name "*postgresql*" -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Running' }

if (-not $pgService) {
    Write-Host "⚠ Serviço PostgreSQL não está rodando." -ForegroundColor Yellow
    Write-Host "Tentando iniciar..." -ForegroundColor Yellow
    
    $allPgServices = Get-Service -Name "*postgresql*" -ErrorAction SilentlyContinue
    if ($allPgServices) {
        foreach ($svc in $allPgServices) {
            try {
                Start-Service $svc.Name -ErrorAction Stop
                Write-Host "✓ Serviço $($svc.Name) iniciado" -ForegroundColor Green
                Start-Sleep -Seconds 3
                break
            } catch {
                Write-Host "✗ Erro ao iniciar serviço: $($svc.Name)" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "✗ Nenhum serviço PostgreSQL encontrado." -ForegroundColor Red
        Write-Host "Por favor, inicie o PostgreSQL manualmente e tente novamente." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "✓ Serviço PostgreSQL está rodando" -ForegroundColor Green
}

# Solicitar senha
Write-Host "`nDigite a senha do usuário '$DbUser':" -ForegroundColor Yellow
$securePassword = Read-Host -AsSecureString
$password = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
)

# Configurar variável de ambiente para o psql
$env:PGPASSWORD = $password

# Verificar se o banco já existe
Write-Host "`nVerificando se o banco '$DbName' já existe..." -ForegroundColor Yellow
$checkDb = & $psqlPath -U $DbUser -lqt 2>&1 | Select-String $DbName

if ($checkDb) {
    Write-Host "⚠ O banco de dados '$DbName' já existe." -ForegroundColor Yellow
    $response = Read-Host "Deseja recriar? (s/N)"
    if ($response -eq 's' -or $response -eq 'S') {
        Write-Host "Removendo banco existente..." -ForegroundColor Yellow
        & $psqlPath -U $DbUser -c "DROP DATABASE IF EXISTS $DbName;" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Banco removido" -ForegroundColor Green
        }
    } else {
        Write-Host "Mantendo banco existente." -ForegroundColor Gray
        exit 0
    }
}

# Criar banco de dados
Write-Host "`nCriando banco de dados '$DbName'..." -ForegroundColor Yellow
$result = & $psqlPath -U $DbUser -c "CREATE DATABASE $DbName;" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Banco de dados '$DbName' criado com sucesso!" -ForegroundColor Green
    
    # Verificar criação
    Write-Host "`nVerificando banco de dados..." -ForegroundColor Yellow
    $verify = & $psqlPath -U $DbUser -d $DbName -c "SELECT version();" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Conexão com o banco testada com sucesso!" -ForegroundColor Green
        Write-Host "`n=== CONFIGURAÇÃO CONCLUÍDA ===" -ForegroundColor Green
        Write-Host "`nPróximos passos:" -ForegroundColor Yellow
        Write-Host "1. Atualize os arquivos .env com a senha do PostgreSQL:"
        Write-Host "   - services\product-service\.env"
        Write-Host "   - services\order-service\.env"
        Write-Host "   - services\payment-service\.env"
        Write-Host "`n2. Altere DB_PASSWORD em cada arquivo .env" -ForegroundColor White
    } else {
        Write-Host "⚠ Banco criado, mas houve erro ao testar conexão." -ForegroundColor Yellow
        Write-Host "Verifique a senha e tente novamente." -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ Erro ao criar banco de dados:" -ForegroundColor Red
    Write-Host $result -ForegroundColor Red
    
    if ($result -match "password authentication failed") {
        Write-Host "`n⚠ Erro: Senha incorreta." -ForegroundColor Yellow
        Write-Host "Verifique a senha do usuário '$DbUser'." -ForegroundColor Yellow
    } elseif ($result -match "already exists") {
        Write-Host "`n⚠ O banco já existe. Use a opção de recriar." -ForegroundColor Yellow
    }
}

# Limpar senha da memória
$env:PGPASSWORD = $null
$password = $null

Write-Host "`nPressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

