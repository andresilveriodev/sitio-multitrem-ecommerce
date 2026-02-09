import httpx
import json

# Teste final do endpoint /ai/generate após correções
API_BASE_URL = "http://localhost:8012"
ENDPOINT = f"{API_BASE_URL}/ai/generate"

print("=" * 80)
print("TESTE FINAL - ENDPOINT /ai/generate")
print("=" * 80)
print("\nIMPORTANTE: Certifique-se de que o servidor foi reiniciado")
print("para aplicar as mudancas no codigo!\n")

# Teste 1: Formato simples
print("TESTE 1: Formato simples com provider e model explicitos")
print("-" * 80)

request_data_1 = {
    "message": "teste simples",
    "provider": "openai",
    "model": "gpt-4o-mini"
}

try:
    with httpx.Client(timeout=30.0) as client:
        response = client.post(ENDPOINT, json=request_data_1)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("[OK] SUCESSO!")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"[ERRO] Falhou com status {response.status_code}")
            print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"[ERRO] Excecao: {e}")

# Teste 2: Formato completo (como chatbot service)
print("\n" + "=" * 80)
print("TESTE 2: Formato completo (como chatbot service)")
print("-" * 80)

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
            print("[OK] SUCESSO!")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            print(f"\nResposta da IA: {result.get('response', '')[:200]}...")
        else:
            print(f"[ERRO] Falhou com status {response.status_code}")
            print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"[ERRO] Excecao: {e}")
    import traceback
    print(traceback.format_exc())

print("\n" + "=" * 80)





