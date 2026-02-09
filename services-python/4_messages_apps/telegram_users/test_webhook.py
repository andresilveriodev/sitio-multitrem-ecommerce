"""
Script para testar o webhook do Telegram localmente
Simula uma mensagem do Telegram
"""

import requests
import json

# Configurações
TELEGRAM_SERVICE_URL = "http://localhost:8021"
WEBHOOK_ENDPOINT = f"{TELEGRAM_SERVICE_URL}/telegram/webhook"

# Dados de teste (simulando mensagem do Telegram)
test_update = {
    "update_id": 123456,
    "message": {
        "message_id": 1,
        "from": {
            "id": 987654321,
            "is_bot": False,
            "first_name": "Teste",
            "last_name": "Usuario",
            "username": "teste_user",
            "language_code": "pt"
        },
        "chat": {
            "id": 987654321,
            "first_name": "Teste",
            "last_name": "Usuario",
            "username": "teste_user",
            "type": "private"
        },
        "date": 1234567890,
        "text": "Olá, esta é uma mensagem de teste!"
    }
}


def test_webhook():
    """Testa o webhook enviando uma mensagem simulada"""
    print("🧪 Testando webhook do Telegram...")
    print(f"📡 Enviando para: {WEBHOOK_ENDPOINT}")
    print(f"📝 Mensagem: {test_update['message']['text']}")
    print()
    
    try:
        response = requests.post(
            WEBHOOK_ENDPOINT,
            json=test_update,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📥 Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✅ Webhook funcionando! Verifique os logs do serviço.")
        else:
            print(f"\n⚠️ Webhook retornou status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao serviço.")
        print("   Verifique se o Telegram Service está rodando na porta 8021")
    except requests.exceptions.Timeout:
        print("❌ Erro: Timeout ao conectar ao serviço")
    except Exception as e:
        print(f"❌ Erro: {e}")


def test_service_status():
    """Testa se o serviço está rodando"""
    print("🔍 Verificando status do serviço...")
    
    try:
        response = requests.get(f"{TELEGRAM_SERVICE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Serviço está rodando!")
            print(f"   {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"⚠️ Serviço retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Serviço não está rodando ou não está acessível")
        print("   Inicie o serviço com: python main.py")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_webhook_info():
    """Obtém informações sobre o webhook configurado"""
    print("\n🔍 Verificando informações do webhook...")
    
    try:
        response = requests.get(f"{TELEGRAM_SERVICE_URL}/telegram/webhook-info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Informações do webhook:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"⚠️ Erro ao obter informações: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE DE WEBHOOK DO TELEGRAM SERVICE")
    print("=" * 60)
    print()
    
    # Testar se serviço está rodando
    if not test_service_status():
        print("\n❌ Serviço não está rodando. Inicie o serviço primeiro.")
        exit(1)
    
    print()
    
    # Testar webhook info
    test_webhook_info()
    
    print()
    print("-" * 60)
    print()
    
    # Testar webhook
    test_webhook()
    
    print()
    print("=" * 60)
    print("💡 Dica: Verifique os logs do serviço para ver o processamento")
    print("=" * 60)
