# Script para testar conexão com PostgreSQL e ajudar a configurar a senha correta

param(
    [string]$PgVersion = "18",
    [string]$DbUser = "postgres",
    [string]$DbName = "sitio_multitrem"
)

Write-Host "`n=== TESTE DE CONEXÃO POSTGRESQL ===" -ForegroundColor Cyan
Write-Host ""

# Procurar psql.exe
$possiblePaths = @(
    "C:\Program Files\PostgreSQL\$PgVersion\bin",
    "C:\Program Files (x86)\PostgreSQL\$PgVersion\bin",
    "C:\PostgreSQL\$PgVersion\bin"
)

$psqlPath = $null

foreach ($path in $possiblePaths) {
    $testPath = Join-Path $path "psql.exe"
    if (Test-Path $testPath) {
        $psqlPath = $testPath
        Write-Host "✓ PostgreSQL encontrado em: $path" -ForegroundColor Green
        break
    }
}

# Se não encontrou, procurar automaticamente
if (-not $psqlPath) {
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

if (-not $psqlPath) {
    Write-Host "✗ PostgreSQL não encontrado." -ForegroundColor Red
    Write-Host "Por favor, informe o caminho do psql.exe:" -ForegroundColor Yellow
    $customPath = Read-Host "Caminho"
    if (Test-Path $customPath) {
        $psqlPath = $customPath
    } else {
        Write-Host "✗ Caminho inválido." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n=== TESTE DE CONEXÃO ===" -ForegroundColor Yellow
Write-Host "Vamos testar a conexão com diferentes senhas comuns..." -ForegroundColor Gray
Write-Host ""

# Senhas comuns para testar
$commonPasswords = @("postgres", "admin", "root", "123456", "")

$correctPassword = $null

foreach ($testPassword in $commonPasswords) {
    Write-Host "Testando senha: $($testPassword -eq '' ? '(vazia)' : '***')..." -ForegroundColor Gray -NoNewline
    
    $env:PGPASSWORD = $testPassword
    $result = & $psqlPath -U $DbUser -d postgres -c "SELECT version();" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓ SUCESSO!" -ForegroundColor Green
        $correctPassword = $testPassword
        break
    } else {
        Write-Host " ✗ Falhou" -ForegroundColor Red
    }
}

# Se nenhuma senha comum funcionou, pedir ao usuário
if (-not $correctPassword) {
    Write-Host "`nNenhuma senha comum funcionou." -ForegroundColor Yellow
    Write-Host "Por favor, digite a senha que você definiu durante a instalação:" -ForegroundColor Yellow
    $securePassword = Read-Host -AsSecureString
    $correctPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    )
    
    $env:PGPASSWORD = $correctPassword
    $result = & $psqlPath -U $DbUser -d postgres -c "SELECT version();" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Senha correta! Conexão estabelecida." -ForegroundColor Green
    } else {
        Write-Host "✗ Senha incorreta. Tente novamente." -ForegroundColor Red
        exit 1
    }
}

# Verificar se o banco existe
Write-Host "`nVerificando banco de dados '$DbName'..." -ForegroundColor Yellow
$env:PGPASSWORD = $correctPassword
$dbExists = & $psqlPath -U $DbUser -lqt 2>&1 | Select-String $DbName

if (-not $dbExists) {
    Write-Host "⚠ Banco '$DbName' não existe." -ForegroundColor Yellow
    $create = Read-Host "Deseja criar agora? (S/n)"
    if ($create -ne 'n' -and $create -ne 'N') {
        Write-Host "Criando banco de dados..." -ForegroundColor Yellow
        & $psqlPath -U $DbUser -c "CREATE DATABASE $DbName;" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Banco criado com sucesso!" -ForegroundColor Green
        } else {
            Write-Host "✗ Erro ao criar banco." -ForegroundColor Red
        }
    }
} else {
    Write-Host "✓ Banco '$DbName' existe." -ForegroundColor Green
}

# Atualizar arquivos .env
Write-Host "`n=== ATUALIZANDO ARQUIVOS .env ===" -ForegroundColor Yellow

$services = @(
    "services\product-service\.env",
    "services\order-service\.env",
    "services\payment-service\.env"
)

foreach ($envFile in $services) {
    if (Test-Path $envFile) {
        Write-Host "Atualizando: $envFile" -ForegroundColor Gray
        $content = Get-Content $envFile
        $newContent = $content | ForEach-Object {
            if ($_ -match "^DB_PASSWORD=") {
                "DB_PASSWORD=$correctPassword"
            } elseif ($_ -match "^DB_DATABASE=" -and $envFile -match "order|payment") {
                "DB_DATABASE=$DbName"
            } elseif ($_ -match "^DB_NAME=" -and $envFile -match "product") {
                "DB_NAME=$DbName"
            } else {
                $_
            }
        }
        $newContent | Set-Content $envFile -Encoding UTF8
        Write-Host "  ✓ Atualizado" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Arquivo não encontrado: $envFile" -ForegroundColor Yellow
    }
}

# Limpar senha
$env:PGPASSWORD = $null
$correctPassword = $null

Write-Host "`n=== CONCLUÍDO ===" -ForegroundColor Green
Write-Host "✓ Senha configurada nos arquivos .env" -ForegroundColor Green
Write-Host "✓ Você pode agora iniciar os serviços" -ForegroundColor Green
Write-Host "`nPressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")






