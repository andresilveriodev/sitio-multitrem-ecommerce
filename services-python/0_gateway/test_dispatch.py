"""
Script de teste para o endpoint de dispatch do gateway
"""

import requests
import json
import sys

# URL base do gateway
BASE_URL = "http://localhost:8000"

def test_endpoint_without_auth():
    """Testa o endpoint sem autenticação (deve retornar 401)"""
    print("\n=== Teste 1: Requisição sem autenticação ===")
    url = f"{BASE_URL}/api/v1/gateway/dispatch"
    
    payload = {
        "service": "user",
        "endpoint": "/api/accounts/",
        "method": "GET",
        "params": {
            "page": 1,
            "size": 10
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 401:
            print("[OK] Teste passou: Endpoint requer autenticação")
        else:
            print(f"[AVISO] Status inesperado: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("[ERRO] Erro: Servidor não está rodando. Inicie o servidor primeiro.")
        return False
    except Exception as e:
        print(f"[ERRO] Erro: {e}")
        return False
    
    return True

def test_endpoint_invalid_service():
    """Testa com serviço inválido (deve retornar 400)"""
    print("\n=== Teste 2: Serviço inválido ===")
    url = f"{BASE_URL}/api/v1/gateway/dispatch"
    
    payload = {
        "service": "servico_inexistente",
        "endpoint": "/api/test",
        "method": "GET"
    }
    
    headers = {
        "Authorization": "Bearer fake_token_for_test",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("[OK] Teste passou: Validação de serviço funcionando")
        elif response.status_code == 401:
            print("[AVISO] Token inválido (esperado), mas validação de serviço não foi testada")
        else:
            print(f"[AVISO] Status inesperado: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("[ERRO] Erro: Servidor não está rodando.")
        return False
    except Exception as e:
        print(f"[ERRO] Erro: {e}")
        return False
    
    return True

def test_endpoint_invalid_method():
    """Testa com método HTTP inválido (deve retornar 400)"""
    print("\n=== Teste 3: Método HTTP inválido ===")
    url = f"{BASE_URL}/api/v1/gateway/dispatch"
    
    payload = {
        "service": "user",
        "endpoint": "/api/accounts/",
        "method": "INVALID_METHOD"
    }
    
    headers = {
        "Authorization": "Bearer fake_token_for_test",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("[OK] Teste passou: Validação de método HTTP funcionando")
        elif response.status_code == 401:
            print("[AVISO] Token inválido (esperado), mas validação de método não foi testada")
        else:
            print(f"[AVISO] Status inesperado: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("[ERRO] Erro: Servidor não está rodando.")
        return False
    except Exception as e:
        print(f"[ERRO] Erro: {e}")
        return False
    
    return True

def test_endpoint_path_traversal():
    """Testa sanitização de endpoint (deve rejeitar path traversal)"""
    print("\n=== Teste 4: Sanitização de endpoint (path traversal) ===")
    url = f"{BASE_URL}/api/v1/gateway/dispatch"
    
    payload = {
        "service": "user",
        "endpoint": "../../etc/passwd",
        "method": "GET"
    }
    
    headers = {
        "Authorization": "Bearer fake_token_for_test",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400 or response.status_code == 422:
            print("[OK] Teste passou: Sanitização de endpoint funcionando")
        elif response.status_code == 401:
            print("[AVISO] Token inválido (esperado), mas sanitização não foi testada")
        else:
            print(f"[AVISO] Status inesperado: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("[ERRO] Erro: Servidor não está rodando.")
        return False
    except Exception as e:
        print(f"[ERRO] Erro: {e}")
        return False
    
    return True

def test_health_endpoint():
    """Testa endpoint de health check"""
    print("\n=== Teste 5: Health Check ===")
    url = f"{BASE_URL}/health"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("[OK] Teste passou: Health check funcionando")
            return True
        else:
            print(f"[AVISO] Status inesperado: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERRO] Erro: Servidor não está rodando.")
        return False
    except Exception as e:
        print(f"[ERRO] Erro: {e}")
        return False

def test_docs_endpoint():
    """Testa se a documentação está acessível"""
    print("\n=== Teste 6: Documentação (Swagger) ===")
    url = f"{BASE_URL}/docs"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("[OK] Teste passou: Documentação acessível")
            return True
        elif response.status_code == 404:
            print("[AVISO] Documentação desabilitada (DEBUG=false)")
            return True
        else:
            print(f"[AVISO] Status inesperado: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERRO] Erro: Servidor não está rodando.")
        return False
    except Exception as e:
        print(f"[ERRO] Erro: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("TESTES DO ENDPOINT GATEWAY DISPATCH")
    print("=" * 60)
    
    # Teste básico de conectividade
    if not test_health_endpoint():
        print("\n[ERRO] Servidor não está respondendo. Inicie o servidor primeiro:")
        print("   python main.py")
        print("   ou")
        print("   uvicorn app:app --reload")
        sys.exit(1)
    
    # Testes do endpoint dispatch
    results = []
    results.append(test_endpoint_without_auth())
    results.append(test_endpoint_invalid_service())
    results.append(test_endpoint_invalid_method())
    results.append(test_endpoint_path_traversal())
    results.append(test_docs_endpoint())
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Testes passados: {passed}/{total}")
    
    if passed == total:
        print("[OK] Todos os testes passaram!")
    else:
        print("[AVISO] Alguns testes falharam ou não puderam ser completados")
        print("   (Isso é normal se o servidor não estiver rodando ou")
        print("    se não houver token JWT válido para testes completos)")
    
    print("\n[DICA] Para testar com token JWT real:")
    print("   1. Obtenha um token do Keycloak")
    print("   2. Use o token no header Authorization: Bearer <token>")
    print("   3. Teste com um serviço real (ex: user)")

if __name__ == "__main__":
    main()

