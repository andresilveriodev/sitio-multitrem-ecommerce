"""Teste completo do POST para /v1/gateway/dispatch"""
import requests
import json

print("=" * 70)
print("TESTE POST /v1/gateway/dispatch")
print("=" * 70)

url = "http://localhost:8000/v1/gateway/dispatch"
payload = {
    "service": "user",
    "endpoint": "/api/v1/users",
    "method": "GET"
}

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer test_token"
}

print(f"\nURL: {url}")
print(f"Method: POST")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)
    
    print()
    print("=" * 70)
    
    if response.status_code == 401:
        print("[OK] Endpoint esta funcionando!")
        print("   Status 401 e esperado com token invalido.")
        print("   O endpoint esta respondendo corretamente.")
    elif response.status_code == 404:
        print("[ERRO] Endpoint nao encontrado (404)")
        print("   Verifique se o gateway foi reiniciado apos as mudancas.")
    elif response.status_code == 200:
        print("[SUCESSO] Requisicao bem-sucedida!")
    else:
        print(f"[AVISO] Status inesperado: {response.status_code}")
        
except requests.exceptions.ConnectionError as e:
    print("[ERRO] Nao foi possivel conectar ao gateway")
    print(f"   Verifique se o gateway esta rodando em {url}")
    print(f"   Erro: {str(e)}")
except Exception as e:
    print(f"[ERRO] {type(e).__name__}: {str(e)}")

print("=" * 70)






