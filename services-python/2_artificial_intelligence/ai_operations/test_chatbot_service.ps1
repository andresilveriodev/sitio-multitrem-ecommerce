# Teste do GPT-4.1-nano via Chatbot Service
# PowerShell Script

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TESTE GPT-4.1-nano VIA CHATBOT SERVICE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8012"

# Passo 1: Criar conversa
Write-Host "[*] Passo 1: Criando conversa..." -ForegroundColor Yellow
try {
    $createBody = @{
        user_id = 1
        username = "test_user"
        title = "Teste GPT-4.1-nano"
    } | ConvertTo-Json

    $createResponse = Invoke-RestMethod -Uri "$baseUrl/chatbot/conversations" `
        -Method POST `
        -ContentType "application/json" `
        -Body $createBody

    $conversationId = $createResponse.id
    Write-Host "[OK] Conversa criada: ID $conversationId" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "[ERRO] Falha ao criar conversa: $_" -ForegroundColor Red
    exit 1
}

# Passo 2: Enviar mensagem com GPT-4.1-nano
Write-Host "[*] Passo 2: Enviando mensagem com GPT-4.1-nano..." -ForegroundColor Yellow
Write-Host "Mensagem: 'Olá! Você está funcionando com GPT-4.1-nano?'" -ForegroundColor White
Write-Host "Provider: openai" -ForegroundColor White
Write-Host "Model: gpt-4.1-nano" -ForegroundColor White
Write-Host ""

try {
    $chatBody = @{
        conversation_id = $conversationId
        message = "Olá! Você está funcionando com GPT-4.1-nano?"
        provider = "openai"
        model = "gpt-4.1-nano"
    } | ConvertTo-Json

    $chatResponse = Invoke-RestMethod -Uri "$baseUrl/chatbot/chat" `
        -Method POST `
        -ContentType "application/json" `
        -Body $chatBody

    Write-Host "[OK] SUCESSO!" -ForegroundColor Green
    Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host "Conversa ID: $($chatResponse.conversation_id)" -ForegroundColor White
    Write-Host "Mensagem do usuário: $($chatResponse.user_message)" -ForegroundColor White
    Write-Host ""
    Write-Host "Resposta da IA:" -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host $chatResponse.ai_response -ForegroundColor Green
    Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[OK] GPT-4.1-nano está FUNCIONANDO via Chatbot Service!" -ForegroundColor Green
}
catch {
    Write-Host "[ERRO] Falha na requisição: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Resposta do servidor: $responseBody" -ForegroundColor Red
    }
    exit 1
}





