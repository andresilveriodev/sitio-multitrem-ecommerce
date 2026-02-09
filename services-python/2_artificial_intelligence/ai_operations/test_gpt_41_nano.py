#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do modelo GPT-4.1-nano
Verifica se o modelo está funcionando corretamente
"""

import httpx
import json
import sys
from datetime import datetime

# Configuração da API
API_BASE_URL = "http://localhost:8012"
ENDPOINT = f"{API_BASE_URL}/ai/generate"
HEADERS = {"Content-Type": "application/json"}

def test_gpt_41_nano():
    """
    Testa o modelo gpt-4.1-nano com uma mensagem simples
    """
    print("=" * 60)
    print("TESTE DO MODELO GPT-4.1-NANO")
    print("=" * 60)
    print(f"URL: {ENDPOINT}")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Mensagem de teste
    test_message = "Olá! Você está funcionando? Responda apenas 'Sim, estou funcionando!' se conseguir processar esta mensagem."
    
    # Payload conforme a API espera (formato messages)
    data = {
        "messages": [
            {
                "role": "user",
                "content": test_message
            }
        ],
        "provider": "openai",
        "model": "gpt-4.1-nano",
        "max_tokens": 200,
        "temperature": 1.0  # gpt-4.1-nano requer temperature=1.0
    }
    
    print("[*] Enviando requisicao...")
    print(f"Mensagem: {test_message}")
    print(f"Modelo: gpt-4.1-nano")
    print(f"Provider: openai")
    print()
    
    try:
        # Faz a requisição
        with httpx.Client(timeout=30.0) as client:
            response = client.post(ENDPOINT, json=data, headers=HEADERS)
        
        print(f"[*] Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            
            print("[OK] SUCESSO! Resposta recebida:")
            print("-" * 60)
            print(f"Provider: {result.get('provider', 'N/A')}")
            print(f"Model: {result.get('model', 'N/A')}")
            print(f"Usage: {result.get('usage', {})}")
            print()
            print("Resposta da IA:")
            print("-" * 60)
            response_text = result.get('response', 'Resposta vazia')
            print(response_text)
            print("-" * 60)
            print()
            print(f"[OK] Modelo gpt-4.1-nano esta FUNCIONANDO!")
            print(f"[*] Tamanho da resposta: {len(response_text)} caracteres")
            
            return True
            
        else:
            print("[ERRO] ERRO na requisicao:")
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
            try:
                error_detail = response.json()
                print(f"Detalhes: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                pass
            
            return False
            
    except httpx.ConnectError:
        print("[ERRO] ERRO: Nao foi possivel conectar a API")
        print(f"Verifique se a aplicacao esta rodando em {API_BASE_URL}")
        return False
        
    except httpx.TimeoutException:
        print("[ERRO] ERRO: Timeout na requisicao (mais de 30 segundos)")
        return False
        
    except Exception as e:
        print(f"[ERRO] ERRO inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gpt_41_nano()
    sys.exit(0 if success else 1)

