#Requires -Version 5.1
<#
.SYNOPSIS
  Sobe, para ou reinicia os microservicos Python sem ativar venv.

.DESCRIPTION
  Usa o python.exe de .venv ou venv em cada pasta e abre uma janela por servico.
  Portas: services-python/PORTAS_APLICACOES.md

.EXAMPLE
  .\start-python-services.ps1 -Action restart
  .\start-python-services.ps1 -Only commerce,bot_operations -Action restart
#>
[CmdletBinding()]
param(
    [ValidateSet("start", "stop", "restart")]
    [string]$Action = "start",

    [string[]]$Only = @(),

    [switch]$EnsureVenv
)

$ErrorActionPreference = "Stop"
# Cursor aberto em services-python (recomendado) ou script copiado para a raiz do monorepo.
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot "0_gateway")) {
    $ServicesRoot = $PSScriptRoot
} else {
    $ServicesRoot = Join-Path (Split-Path -Parent $PSScriptRoot) "services-python"
}

$Catalog = @(
    @{
        Id          = "gateway"
        Name        = "Gateway"
        RelPath     = "0_gateway"
        Port        = 8000
        Env         = @{ PORT = "8000" }
    }
    @{
        Id          = "users"
        Name        = "User Service"
        RelPath     = "1_users"
        Port        = 8001
        Env         = @{ PORT = "8001" }
    }
    @{
        Id          = "commerce"
        Name        = "Commerce"
        RelPath     = "5_commerce\commerce_backend"
        Port        = 8002
        Env         = @{ PORT = "8002" }
    }
    @{
        Id          = "commerce_frontend"
        Name        = "Commerce Frontend"
        RelPath     = "5_commerce\commerce_frontend"
        Port        = 8003
        Kind        = "node"
        Env         = @{ PORT = "8003" }
    }
    @{
        Id          = "ai_operations"
        Name        = "AI Operations"
        RelPath     = "2_artificial_intelligence\ai_operations"
        Port        = 8005
        Env         = @{ AI_SERVICE_PORT = "8005"; PORT = "8005" }
    }
    @{
        Id          = "ai_users"
        Name        = "AI Users"
        RelPath     = "2_artificial_intelligence\ai_users"
        Port        = 8006
        Env         = @{ AI_SERVICE_PORT = "8006"; PORT = "8006" }
    }
    @{
        Id          = "bot_users"
        Name        = "Chatbot Users"
        RelPath     = "3_chatbot\bot_users"
        Port        = 8010
        Env         = @{ PORT = "8010" }
    }
    @{
        Id          = "bot_operations"
        Name        = "Chatbot Operations"
        RelPath     = "3_chatbot\bot_operations"
        Port        = 8011
        Env         = @{ PORT = "8011" }
    }
    @{
        Id          = "telegram_operations"
        Name        = "Telegram Operations"
        RelPath     = "4_messages_apps\telegram_operations"
        Port        = 8021
        Env         = @{ PORT = "8021" }
    }
)

function Write-Info([string]$Message) { Write-Host $Message -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host $Message -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host $Message -ForegroundColor Yellow }
function Write-Err([string]$Message) { Write-Host $Message -ForegroundColor Red }

function Get-SelectedServices {
    if (-not $Only -or $Only.Count -eq 0) {
        return $Catalog
    }
    $wanted = @()
    foreach ($item in $Only) {
        $parts = $item -split "," | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ }
        $wanted += $parts
    }
    $selected = @()
    foreach ($id in $wanted) {
        $match = $Catalog | Where-Object { $_.Id -eq $id }
        if (-not $match) {
            $valid = ($Catalog | ForEach-Object { $_.Id }) -join ", "
            throw "Servico desconhecido: '$id'. Use: $valid"
        }
        $selected += $match
    }
    return $selected
}

function Get-ListenPids([int]$Port) {
    $pids = @()
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        foreach ($conn in $conns) {
            if ($conn.OwningProcess) { $pids += [int]$conn.OwningProcess }
        }
    } catch {
        $lines = netstat -ano | Select-String ":$Port\s+.+LISTENING"
        foreach ($line in $lines) {
            $procId = ($line.ToString().Trim() -split "\s+")[-1]
            if ($procId -match "^\d+$") { $pids += [int]$procId }
        }
    }
    return $pids | Select-Object -Unique
}

function Stop-ServicePort([int]$Port, [string]$Name) {
    $pids = Get-ListenPids -Port $Port
    if (-not $pids) {
        Write-Host "  [$Name] porta $Port livre"
        return
    }
    foreach ($procId in $pids) {
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Warn "  [$Name] encerrou PID $procId ($($proc.ProcessName)) na porta $Port"
        } catch {
            Write-Warn "  [$Name] nao foi possivel encerrar PID $procId : $_"
        }
    }
}

function Get-SystemPython {
    foreach ($cmd in @("py", "python")) {
        $exe = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($exe) { return $exe.Source }
    }
    throw "Python nao encontrado no PATH. Instale Python ou o launcher 'py'."
}

function Resolve-VenvPython([string]$Dir) {
    $candidates = @(
        (Join-Path $Dir ".venv\Scripts\python.exe"),
        (Join-Path $Dir "venv\Scripts\python.exe")
    )
    foreach ($path in $candidates) {
        if (Test-Path -LiteralPath $path) { return $path }
    }
    return $null
}

function Initialize-ServiceVenv([string]$Dir, [string]$Name) {
    $python = Resolve-VenvPython -Dir $Dir
    if ($python) { return $python }

    if (-not $EnsureVenv) {
        throw "[$Name] venv nao encontrado em '$Dir' (.venv ou venv). Rode de novo com -EnsureVenv"
    }

    $sysPython = Get-SystemPython
    $venvDir = Join-Path $Dir ".venv"
    Write-Info "  [$Name] criando $venvDir"
    & $sysPython -m venv $venvDir
    if ($LASTEXITCODE -ne 0) { throw "[$Name] falha ao criar venv" }

    $python = Join-Path $venvDir "Scripts\python.exe"
    $req = Join-Path $Dir "requirements.txt"
    if (Test-Path -LiteralPath $req) {
        Write-Info "  [$Name] instalando requirements.txt"
        & $python -m pip install --upgrade pip
        & $python -m pip install -r $req
        if ($LASTEXITCODE -ne 0) { throw "[$Name] falha no pip install" }
    } else {
        Write-Warn "  [$Name] requirements.txt ausente"
    }
    return $python
}

function Copy-MissingDotEnv([string]$Dir, [string]$Name) {
    $envFile = Join-Path $Dir ".env"
    $example = Join-Path $Dir "env.example"
    if ((Test-Path -LiteralPath $envFile) -or -not (Test-Path -LiteralPath $example)) {
        return
    }
    Copy-Item -LiteralPath $example -Destination $envFile
    Write-Warn "  [$Name] .env criado a partir de env.example (revise secrets/URLs)"
}

function Escape-PsSingle([string]$Value) {
    return $Value.Replace("'", "''")
}

function Start-ServiceWindow {
    param(
        [hashtable]$Service,
        [string]$Dir,
        [string]$Python
    )

    Copy-MissingDotEnv -Dir $Dir -Name $Service.Name

    $title = "$($Service.Name) :$($Service.Port)"
    $envAssign = @()
    foreach ($key in $Service.Env.Keys) {
        $envAssign += "`$env:$key = '$(Escape-PsSingle $Service.Env[$key])'"
    }
    $envBlock = $envAssign -join "; "

    $dirEsc = Escape-PsSingle $Dir
    $pyEsc = Escape-PsSingle $Python
    $titleEsc = Escape-PsSingle $title

    $command = @"
`$Host.UI.RawUI.WindowTitle = '$titleEsc'
Set-Location -LiteralPath '$dirEsc'
$envBlock
Write-Host ''
Write-Host '== $titleEsc ==' -ForegroundColor Green
Write-Host 'Python: $pyEsc'
Write-Host 'Docs:   http://localhost:$($Service.Port)/docs'
Write-Host 'Ctrl+C para parar este servico.'
Write-Host ''
& '$pyEsc' main.py
Write-Host ''
Write-Host 'Processo encerrou. Feche a janela ou pressione Enter.' -ForegroundColor Yellow
Read-Host
"@

    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-NoExit",
        "-Command", $command
    ) | Out-Null

    Write-Ok "  [$($Service.Name)] http://localhost:$($Service.Port)  ($Python)"
}

function Start-NodeWindow {
    param(
        [hashtable]$Service,
        [string]$Dir
    )

    if (-not (Test-Path -LiteralPath (Join-Path $Dir "package.json"))) {
        throw "package.json nao encontrado em $Dir"
    }
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npm) { throw "npm nao encontrado no PATH" }

    $title = "$($Service.Name) :$($Service.Port)"
    $dirEsc = Escape-PsSingle $Dir
    $titleEsc = Escape-PsSingle $title
    $install = ""
    if (-not (Test-Path -LiteralPath (Join-Path $Dir "node_modules"))) {
        $install = "npm install`r`nif (`$LASTEXITCODE -ne 0) { throw 'npm install falhou' }`r`n"
    }

    $command = @"
`$Host.UI.RawUI.WindowTitle = '$titleEsc'
Set-Location -LiteralPath '$dirEsc'
Write-Host ''
Write-Host '== $titleEsc ==' -ForegroundColor Green
Write-Host 'Tela: http://localhost:$($Service.Port)'
Write-Host 'Ctrl+C para parar este servico.'
Write-Host ''
$install
npm run dev
Write-Host ''
Write-Host 'Processo encerrou. Feche a janela ou pressione Enter.' -ForegroundColor Yellow
Read-Host
"@

    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-NoExit",
        "-Command", $command
    ) | Out-Null

    Write-Ok "  [$($Service.Name)] http://localhost:$($Service.Port)  (npm run dev)"
}

$selected = @(Get-SelectedServices)

Write-Host ""
Write-Host "Sitio Multitrem - servicos Python ($Action)" -ForegroundColor Green
Write-Host ("=" * 52)
Write-Host ""

if ($Action -eq "stop" -or $Action -eq "restart") {
    Write-Info "Encerrando portas..."
    foreach ($svc in $selected) {
        Stop-ServicePort -Port $svc.Port -Name $svc.Name
    }
    if ($Action -eq "restart") { Start-Sleep -Seconds 1 }
}

if ($Action -eq "stop") {
    Write-Ok "`nConcluido."
    exit 0
}

Write-Info "Iniciando servicos (uma janela cada, sem Activate.ps1)..."
$failed = @()
foreach ($svc in $selected) {
    $dir = Join-Path $ServicesRoot $svc.RelPath
    if ($svc.Kind -eq "node") {
        try {
            Start-NodeWindow -Service $svc -Dir $dir
        } catch {
            Write-Err "  [$($svc.Name)] $_"
            $failed += $svc.Id
        }
        continue
    }
    if (-not (Test-Path -LiteralPath (Join-Path $dir "main.py"))) {
        Write-Err "  [$($svc.Name)] main.py nao encontrado em $dir"
        $failed += $svc.Id
        continue
    }
    try {
        $python = Initialize-ServiceVenv -Dir $dir -Name $svc.Name
        Start-ServiceWindow -Service $svc -Dir $dir -Python $python
    } catch {
        Write-Err "  [$($svc.Name)] $_"
        $failed += $svc.Id
    }
}

Write-Host ""
if ($failed.Count -gt 0) {
    Write-Err "Falhou: $($failed -join ', ')"
    exit 1
}
Write-Ok "Pronto. Feche as janelas ou rode: .\scripts\start-python-services.ps1 -Action stop"
$ids = ($selected | ForEach-Object { $_.Id }) -join ", "
Write-Host "Servicos: $ids"
Write-Host ""
