import httpx
import json

# Testa o endpoint /ai/generate diretamente
API_BASE_URL = "http://localhost:8012"
ENDPOINT = f"{API_BASE_URL}/ai/generate"

# Dados da requisição (formato externo como o chatbot service envia)
request_data = {
    "user_id": "f371f8e3-79e4-4afd-9393-10c284427556",
    "message": "quero falar com o gpt hoje 2",
    "context_summary": "",
    "metadata": {
        "source": "chatbot_service",
        "timestamp": "2025-11-19T04:54:45.842830"
    },
    "user_preferences": {
        "language": "pt-BR",
        "response_style": "concise",
        "auto_cache": True,
        "max_context_length": 1000,
        "conversation_preferences": {}
    }
}

print("=" * 80)
print("TESTE DIRETO DO ENDPOINT /ai/generate")
print("=" * 80)
print(f"URL: {ENDPOINT}")
print(f"Request Data: {json.dumps(request_data, indent=2)}")
print("=" * 80)

try:
    with httpx.Client(timeout=30.0) as client:
        print("\n[*] Enviando requisição...")
        response = client.post(
            ENDPOINT,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n[*] Status Code: {response.status_code}")
        print(f"[*] Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"\n[*] Response JSON:")
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(f"\n[*] Response Text:")
            print(response.text)
        
        if response.status_code == 200:
            print("\n[OK] Requisicao bem-sucedida!")
        else:
            print(f"\n[ERRO] Requisicao falhou com status {response.status_code}")
            
except httpx.ConnectError:
    print("\n[ERRO] Nao foi possivel conectar ao servidor")
    print("       Verifique se o servidor esta rodando em http://localhost:8012")
except httpx.TimeoutException:
    print("\n[ERRO] Timeout na requisicao")
except Exception as e:
    print(f"\n[ERRO] Erro inesperado: {e}")
    import traceback
    print(traceback.format_exc())

print("\n" + "=" * 80)

