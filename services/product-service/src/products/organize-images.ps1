# Script para organizar imagens dos produtos
# Move imagens de services/product-service/src/products para frontend/public/images/products
# e mapeia pelos slugs dos produtos

$sourceDir = Join-Path $PSScriptRoot "."
$targetDir = Join-Path $PSScriptRoot "../../../frontend/public/images/products"

# Criar pasta de destino se nao existir
if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Write-Host "Pasta criada: $targetDir" -ForegroundColor Green
}

# Funcao para normalizar nome do arquivo para slug
function Get-SlugFromFileName {
    param([string]$fileName)
    
    # Remove extensao
    $nameWithoutExt = [System.IO.Path]::GetFileNameWithoutExtension($fileName)
    
    # Normaliza: remove espacos, acentos, converte para minusculas
    $normalized = $nameWithoutExt -replace '\s+', '-' -replace '[áàâã]', 'a' -replace '[éèê]', 'e' -replace '[íìî]', 'i' -replace '[óòôõ]', 'o' -replace '[úùû]', 'u' -replace '[ç]', 'c'
    $normalized = $normalized.ToLower()
    
    # Mapeamentos especificos
    # Alface
    $normalized = $normalized -replace '^alface-americana$', 'alface-americana'
    $normalized = $normalized -replace '^alface_americana$', 'alface-americana'
    $normalized = $normalized -replace '^alface-crespa$', 'alface-crespa'
    $normalized = $normalized -replace '^alface_crespa$', 'alface-crespa'
    # Hortaliças
    $normalized = $normalized -replace '^cebolinha$', 'cebolinha'
    $normalized = $normalized -replace '^coentro$', 'coentro'
    $normalized = $normalized -replace '^salsa$', 'salsa'
    $normalized = $normalized -replace '^rucula$', 'rucula'
    # Ovos Caipiras
    $normalized = $normalized -replace '^ovos-caipiras-12-unidades$', '12-ovos-caipiras'
    $normalized = $normalized -replace '^ovos_caipiras_12_unidades$', '12-ovos-caipiras'
    $normalized = $normalized -replace '^12-ovos$', '12-ovos-caipiras'
    $normalized = $normalized -replace '^ovos-12$', '12-ovos-caipiras'
    $normalized = $normalized -replace '^ovos-caipiras-20-unidades$', '20-ovos-caipiras'
    $normalized = $normalized -replace '^ovos_caipiras_20_unidades$', '20-ovos-caipiras'
    $normalized = $normalized -replace '^20-ovos$', '20-ovos-caipiras'
    $normalized = $normalized -replace '^ovos-20$', '20-ovos-caipiras'
    $normalized = $normalized -replace '^ovos-caipiras-30-unidades$', '30-ovos-caipiras'
    $normalized = $normalized -replace '^ovos_caipiras_30_unidades$', '30-ovos-caipiras'
    $normalized = $normalized -replace '^30-ovos$', '30-ovos-caipiras'
    $normalized = $normalized -replace '^ovos-30$', '30-ovos-caipiras'
    # Kits
    $normalized = $normalized -replace '^kit-1$', 'kit-1-pessoa'
    $normalized = $normalized -replace '^kit-2$', 'kit-2-pessoas'
    $normalized = $normalized -replace '^kit-3$', 'kit-3-pessoas'
    $normalized = $normalized -replace '^kit-4$', 'kit-4-pessoas'
    $normalized = $normalized -replace '^kit-5$', 'kit-5-pessoas'
    # Combos
    $normalized = $normalized -replace '^combo-familia$', 'combo-familia-2'
    
    return $normalized
}

# Buscar todas as imagens
$imageExtensions = @('.jpg', '.jpeg', '.png', '.webp', '.gif', '.JPG', '.JPEG', '.PNG', '.WEBP', '.GIF')
$images = Get-ChildItem -Path $sourceDir -File | Where-Object { $imageExtensions -contains $_.Extension }

if ($images.Count -eq 0) {
    Write-Host "Nenhuma imagem encontrada em: $sourceDir" -ForegroundColor Yellow
    Write-Host "Coloque as imagens na pasta: $sourceDir" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Encontradas $($images.Count) imagem(ns):" -ForegroundColor Cyan

$movedCount = 0
foreach ($image in $images) {
    $slug = Get-SlugFromFileName $image.Name
    $newFileName = "$slug$($image.Extension)"
    $targetPath = Join-Path $targetDir $newFileName
    
    try {
        Copy-Item -Path $image.FullName -Destination $targetPath -Force
        Write-Host "  $($image.Name) -> /images/products/$newFileName" -ForegroundColor Green
        $movedCount++
    } catch {
        Write-Host "  Erro ao copiar $($image.Name): $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "$movedCount imagem(ns) organizada(s) em: $targetDir" -ForegroundColor Green
Write-Host ""
Write-Host "As imagens agora estao disponiveis em:" -ForegroundColor Cyan
Write-Host "   /images/products/[slug-do-produto].[extensao]" -ForegroundColor White
