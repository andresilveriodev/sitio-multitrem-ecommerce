"""Teste do endpoint dispatch com token valido"""
import requests
import json
import time

GATEWAY_URL = "http://localhost:8000/v1/gateway/dispatch"
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJDTDF3SmtoU0JvTmpuOXRVdzNaRUJTQ2o5VFljVU5ZRC1wX29abTFIRG9ZIn0.eyJleHAiOjE3NjQ0NDIzNDksImlhdCI6MTc2NDQzODc0OSwiYXV0aF90aW1lIjoxNzY0NDM1OTM1LCJqdGkiOiJlYjAzOTNkYi1jNjhjLTQwMDktYTE5MS0zN2QyNWY4YTVjMGMiLCJpc3MiOiJodHRwczovL2F1dGgucmVuZGFjb250aW51YS5jb20vYXV0aC9yZWFsbXMvYXV0aF9zc28iLCJhdWQiOlsicmVkbWluZSIsImF1dGhfY2xpZW50Iiwid3BfZWR1IiwiYWNjb3VudCJdLCJzdWIiOiJmMzcxZjhlMy03OWU0LTRhZmQtOTM5My0xMGMyODQ0Mjc1NTYiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJob21lYnJva2VyLXJlYWN0Iiwibm9uY2UiOiJjMmJmNWFmZC0wNTNkLTQxM2EtOWQ1YS1kN2FmMDdkOGY5YzQiLCJzZXNzaW9uX3N0YXRlIjoiZDQ4ZGVjNzYtNDk0Ni00NzBhLWI0ZTItMWNhNmFlMTY4ZTMxIiwiYWNyIjoiMCIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vMTI3LjAuMC4xOjMwMDAiLCIqIiwiaHR0cDovL2xvY2FsaG9zdDozMDAwIiwiaHR0cHM6Ly9ob21lYnJva2VyLXJlYWN0Lm5ldGxpZnkuYXBwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwidXNlciJdfSwicmVzb3VyY2VfYWNjZXNzIjp7InJlZG1pbmUiOnsicm9sZXMiOlsiQWRtaW4iXX0sImF1dGhfY2xpZW50Ijp7InJvbGVzIjpbInVtYV9wcm90ZWN0aW9uIiwidXNlciJdfSwid3BfZWR1Ijp7InJvbGVzIjpbImN1cnNvX3JjMSJdfSwiaG9tZWJyb2tlci1yZWFjdCI6eyJyb2xlcyI6WyJBZG1pbiJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInNpZCI6ImQ0OGRlYzc2LTQ5NDYtNDcwYS1iNGUyLTFjYTZhZTE2OGUzMSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJuYW1lIjoiQWRyaWFubyBMb3VyZW5jbyBkb3MgU2FudG9zIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiYWRyaWFub2xvdXJlbmNvIiwiZ2l2ZW5fbmFtZSI6IkFkcmlhbm8iLCJsb2NhbGUiOiJwdC1CUiIsImZhbWlseV9uYW1lIjoiTG91cmVuY28gZG9zIFNhbnRvcyIsImVtYWlsIjoiYWRyaWFuby5zYW50b3MuYm1AZ21haWwuY29tIn0.WS9nYo7CgsbeJvKIFOtE-hrRf3BGC80Akxza-HKtAfrrnLJWDj5lbi2LL1hemBL0uOCeOVJGHiXrzAr4L7qH-i7oZKlEsQ-C_9FUGI9FOBFotba8WY2qeHkEGJ1ANuDnoJL0LZNoY9llZYDg10Hf1vN2n-UX9SwcC_L1DLKeWzxnTaWmM3SzuZEpLkZrJo1rw5bZVXPopEPCmUT6b-FEAh2NEeuPeCPAcwulSedQyFBPFpVp5slmpqk2VBePviKrogHPqFz6_gLrgF--lGO-1naNdfEvism-oiXQGAleaEkIC16ehCl65dbyhTa8r_rD7y_mRFgH_mXI3quY6mh20g"

print("=" * 70)
print("TESTE DO ENDPOINT DISPATCH - USER COM TOKEN VALIDO")
print("=" * 70)

# Payload para acessar user
payload = {
    "service": "user",
    "endpoint": "/api/v1/users",
    "method": "GET"
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

print(f"\n1. Testando POST para {GATEWAY_URL}")
print(f"   Service: {payload['service']}")
print(f"   Endpoint: {payload['endpoint']}")
print(f"   Method: {payload['method']}")
print(f"   Token: {TOKEN[:50]}...")
print()

try:
    start_time = time.time()
    response = requests.post(
        GATEWAY_URL,
        json=payload,
        headers=headers,
        timeout=15
    )
    elapsed = time.time() - start_time
    
    print(f"[OK] Resposta recebida em {elapsed:.3f}s")
    print(f"   Status Code: {response.status_code}")
    print()
    print("   Response Body:")
    try:
        response_json = response.json()
        print(f"   {json.dumps(response_json, indent=2, ensure_ascii=False)}")
    except:
        print(f"   {response.text[:1000]}")
    
    print()
    print("=" * 70)
    print("RESULTADO:")
    if response.status_code == 200:
        print("[SUCESSO] Requisicao bem-sucedida!")
        print("   O user service respondeu corretamente.")
    elif response.status_code == 502:
        print("[OK] Gateway funcionando! User service esta offline.")
        print("   A requisicao chegou no gateway, autenticou corretamente,")
        print("   mas o user service nao esta respondendo.")
        if isinstance(response_json, dict) and "detail" in response_json:
            print(f"   Mensagem: {response_json['detail']}")
    elif response.status_code == 401:
        print("[ERRO] Token invalido ou expirado")
        print("   Verifique se o token esta correto e nao expirou.")
    elif response.status_code == 504:
        print("[OK] Gateway funcionando! Timeout ao acessar user service.")
        print("   O user service pode estar sobrecarregado ou muito lento.")
    else:
        print(f"[AVISO] Status inesperado: {response.status_code}")
        if isinstance(response_json, dict) and "detail" in response_json:
            print(f"   Mensagem: {response_json['detail']}")
    
except requests.exceptions.ConnectionError as e:
    print("[ERRO] Nao foi possivel conectar ao gateway")
    print(f"   Verifique se o gateway esta rodando em {GATEWAY_URL}")
    print(f"   Erro: {str(e)}")
except requests.exceptions.Timeout as e:
    print("[ERRO] Timeout ao conectar ao gateway")
    print(f"   Erro: {str(e)}")
except Exception as e:
    print(f"[ERRO] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("=" * 70)

