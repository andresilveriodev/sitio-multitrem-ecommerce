# Script para limpar histórico de conversas do AI Service no Redis

param(
    [string]$RedisHost = "redis-11736.crce216.sa-east-1-2.ec2.cloud.redislabs.com",
    [int]$RedisPort = 11736,
    [string]$RedisPassword = "M2vC2HM0wWtmXVVl8dEmwZ4iFlXAocpJ",
    [string]$VisitorId = ""
)

Write-Host "`n=== LIMPAR HISTÓRICO DO AI SERVICE ===" -ForegroundColor Cyan
Write-Host ""

# Instalar ioredis se necessário (via npm)
$hasIoredis = Get-Command node -ErrorAction SilentlyContinue

if (-not $hasIoredis) {
    Write-Host "✗ Node.js não encontrado. Instale Node.js primeiro." -ForegroundColor Red
    exit 1
}

# Criar script temporário para limpar histórico
$tempScript = @"
const Redis = require('ioredis');

const redis = new Redis({
  host: '$RedisHost',
  port: $RedisPort,
  password: '$RedisPassword',
});

async function clearHistory() {
  try {
    await redis.connect();
    console.log('✓ Conectado ao Redis');
    
    // Buscar todas as chaves de conversa
    const keys = await redis.keys('ai:conversation:*');
    console.log(`\nEncontradas \${keys.length} conversas`);
    
    if (keys.length === 0) {
      console.log('Nenhuma conversa encontrada.');
      await redis.quit();
      return;
    }
    
    // Se visitorId foi especificado, limpar apenas essa
    if ('$VisitorId') {
      const key = \`ai:conversation:$VisitorId\`;
      const exists = await redis.exists(key);
      if (exists) {
        await redis.del(key);
        console.log(\`✓ Histórico limpo para: $VisitorId\`);
      } else {
        console.log(\`✗ Conversa não encontrada: $VisitorId\`);
      }
    } else {
      // Limpar todas
      console.log('\nLimpando todas as conversas...');
      for (const key of keys) {
        await redis.del(key);
        console.log(\`✓ Limpo: \${key}\`);
      }
      console.log(\`\n✓ Total: \${keys.length} conversas limpas\`);
    }
    
    await redis.quit();
    console.log('\n✓ Concluído!');
  } catch (error) {
    console.error('✗ Erro:', error.message);
    process.exit(1);
  }
}

clearHistory();
"@

$tempFile = Join-Path $env:TEMP "clear-ai-history-$(Get-Random).js"
$tempScript | Out-File -FilePath $tempFile -Encoding UTF8

Write-Host "Executando limpeza..." -ForegroundColor Yellow
if ($VisitorId) {
    Write-Host "Limpar apenas: $VisitorId" -ForegroundColor Cyan
} else {
    Write-Host "Limpar TODAS as conversas" -ForegroundColor Yellow
    $confirm = Read-Host "Continuar? (s/N)"
    if ($confirm -ne 's' -and $confirm -ne 'S') {
        Remove-Item $tempFile -ErrorAction SilentlyContinue
        Write-Host "Cancelado." -ForegroundColor Gray
        exit 0
    }
}

try {
    node $tempFile
    Write-Host "`n✓ Limpeza concluída!" -ForegroundColor Green
} catch {
    Write-Host "`n✗ Erro ao executar: $_" -ForegroundColor Red
} finally {
    Remove-Item $tempFile -ErrorAction SilentlyContinue
}

Write-Host "`nPressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")































