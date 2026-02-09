"""
Teste simples do webhook - simula mensagem do Telegram
"""

import requests
import json

# URL do serviço
SERVICE_URL = "http://localhost:8021"

# Simular mensagem do Telegram
test_message = {
    "update_id": 123456,
    "message": {
        "message_id": 1,
        "from": {
            "id": 987654321,
            "is_bot": False,
            "first_name": "Teste",
            "username": "teste_user"
        },
        "chat": {
            "id": 987654321,
            "first_name": "Teste",
            "username": "teste_user",
            "type": "private"
        },
        "date": 1234567890,
        "text": "Teste de mensagem"
    }
}

print("=" * 60)
print("TESTE DE WEBHOOK DO TELEGRAM")
print("=" * 60)
print()

# 1. Verificar se serviço está rodando
print("1. Verificando se o servico esta rodando...")
try:
    response = requests.get(f"{SERVICE_URL}/", timeout=5)
    if response.status_code == 200:
        print("   OK - Servico rodando")
        print(f"   Resposta: {response.json()}")
    else:
        print(f"   ERRO - Status: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ERRO - Nao foi possivel conectar: {e}")
    print("   Certifique-se de que o servico esta rodando na porta 8021")
    exit(1)

print()

# 2. Testar webhook
print("2. Enviando mensagem de teste para o webhook...")
print(f"   Endpoint: {SERVICE_URL}/telegram/webhook")
print(f"   Mensagem: {test_message['message']['text']}")
print()

try:
    response = requests.post(
        f"{SERVICE_URL}/telegram/webhook",
        json=test_message,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        print()
        print("   SUCESSO - Webhook recebeu a mensagem!")
        print("   Verifique os logs do servico para ver o processamento")
    else:
        print()
        print(f"   ATENCAO - Webhook retornou status {response.status_code}")
        
except Exception as e:
    print(f"   ERRO - {e}")

print()
print("=" * 60)
print("Teste concluido!")
print("=" * 60)
