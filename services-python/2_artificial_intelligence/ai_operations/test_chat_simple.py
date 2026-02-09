import httpx
import json

# Teste do endpoint /ai/chat simples
API_BASE_URL = "http://localhost:8012"
ENDPOINT = f"{API_BASE_URL}/ai/chat"

print("=" * 80)
print("TESTE ENDPOINT /ai/chat SIMPLES")
print("=" * 80)

request_data = {
    "message": "Oi, tudo bem?"
}

print(f"Request: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
print(f"URL: {ENDPOINT}")
print("-" * 80)

try:
    with httpx.Client(timeout=30.0) as client:
        print("\n[*] Enviando requisição...")
        response = client.post(
            ENDPOINT,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n[*] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("[OK] SUCESSO!")
            result = response.json()
            print(f"\nResponse JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print(f"\nResposta da IA: {result.get('reply', '')}")
        else:
            print(f"[ERRO] Falhou com status {response.status_code}")
            print(f"Response: {response.text}")
            
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





