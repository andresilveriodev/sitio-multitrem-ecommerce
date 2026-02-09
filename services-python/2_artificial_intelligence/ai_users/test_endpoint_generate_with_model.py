import httpx
import json

# Testa o endpoint /ai/generate com modelo explícito
API_BASE_URL = "http://localhost:8012"
ENDPOINT = f"{API_BASE_URL}/ai/generate"

# Teste 1: Com provider e model explícitos
print("=" * 80)
print("TESTE 1: Com provider e model explicitos")
print("=" * 80)

request_data_1 = {
    "user_id": "f371f8e3-79e4-4afd-9393-10c284427556",
    "message": "teste simples",
    "provider": "openai",
    "model": "gpt-4o-mini"
}

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(ENDPOINT, json=request_data_1)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Erro: {e}")

print("\n" + "=" * 80)
print("TESTE 2: Formato completo (como chatbot service)")
print("=" * 80)

request_data_2 = {
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
    },
    "provider": "openai",
    "model": "gpt-4o-mini"
}

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(ENDPOINT, json=request_data_2)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response JSON: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"Response: {response.text}")
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    print(traceback.format_exc())

print("\n" + "=" * 80)





