#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste detalhado do modelo GPT-4.1-nano
Verifica configuração e testa o modelo
"""

import httpx
import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da API
API_BASE_URL = "http://localhost:8012"
ENDPOINT = f"{API_BASE_URL}/ai/generate"
HEADERS = {"Content-Type": "application/json"}

def check_api_key():
    """Verifica se a API key está configurada"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERRO] OPENAI_API_KEY nao esta configurada no arquivo .env")
        return False
    print(f"[OK] OPENAI_API_KEY encontrada (primeiros 10 chars: {api_key[:10]}...)")
    return True

def test_model(model_name, temperature=0.7):
    """Testa um modelo específico"""
    print(f"\n{'='*60}")
    print(f"Testando modelo: {model_name}")
    print(f"{'='*60}")
    
    test_message = "Responda apenas: OK"
    
    data = {
        "messages": [
            {
                "role": "user",
                "content": test_message
            }
        ],
        "provider": "openai",
        "model": model_name,
        "max_tokens": 50,
        "temperature": temperature
    }
    
    print(f"[*] Enviando requisicao...")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(ENDPOINT, json=data, headers=HEADERS)
        
        print(f"[*] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', 'Resposta vazia')
            print(f"[OK] SUCESSO!")
            print(f"Modelo usado: {result.get('model', 'N/A')}")
            print(f"Resposta: {response_text}")
            return True
        else:
            print(f"[ERRO] Falhou com status {response.status_code}")
            print(f"Resposta: {response.text[:500]}")
            
            # Tenta obter detalhes do erro
            try:
                error_detail = response.json()
                print(f"Detalhes: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                pass
            
            return False
            
    except httpx.ConnectError:
        print(f"[ERRO] Nao foi possivel conectar a API em {API_BASE_URL}")
        return False
    except httpx.TimeoutException:
        print(f"[ERRO] Timeout na requisicao")
        return False
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("TESTE DETALHADO DO MODELO GPT-4.1-NANO")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verifica API key
    if not check_api_key():
        print("\n[AVISO] Continuando mesmo sem API key (pode estar no .env da aplicacao)")
    
    # Testa modelos em ordem
    models_to_test = [
        ("gpt-4o-mini", 0.7),  # Modelo padrão conhecido
        ("gpt-4.1-nano", 1.0),  # Modelo que queremos testar
    ]
    
    results = {}
    
    for model_name, temp in models_to_test:
        results[model_name] = test_model(model_name, temp)
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for model_name, success in results.items():
        status = "[OK] FUNCIONANDO" if success else "[ERRO] FALHOU"
        print(f"{model_name}: {status}")
    
    print()
    
    if results.get("gpt-4.1-nano"):
        print("[OK] Modelo gpt-4.1-nano esta FUNCIONANDO!")
        return 0
    else:
        print("[ERRO] Modelo gpt-4.1-nano NAO esta funcionando")
        print("\nPossiveis causas:")
        print("1. Modelo nao existe na API da OpenAI")
        print("2. API key nao tem acesso ao modelo")
        print("3. Erro na configuracao do servico")
        return 1

if __name__ == "__main__":
    sys.exit(main())





