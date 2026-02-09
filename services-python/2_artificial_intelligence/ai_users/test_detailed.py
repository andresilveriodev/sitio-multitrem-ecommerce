#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste detalhado dos endpoints para verificar erros específicos
"""

import requests
import json
import time

BASE_URL = "http://localhost:8012"

def test_detailed_endpoints():
    """Testa os endpoints com detalhes dos erros"""
    
    print("🔍 TESTE DETALHADO DOS ENDPOINTS")
    print("=" * 50)
    
    # 1. Teste de health check
    print("\n1. Testando health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
    
    # 2. Teste de modelos de IA com detalhes do erro
    print("\n2. Testando listagem de modelos...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/models")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Modelos encontrados: {len(models)}")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao testar modelos: {e}")
    
    # 3. Teste de planos de assinatura com detalhes do erro
    print("\n3. Testando planos de assinatura...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/subscriptions")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            plans = response.json()
            print(f"✅ Planos encontrados: {len(plans)}")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao testar planos: {e}")
    
    # 4. Teste de configurações de IA com detalhes do erro
    print("\n4. Testando configurações de IA...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/settings?user_id=1&username=testuser")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            settings = response.json()
            print(f"✅ Configurações: {settings}")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao testar configurações: {e}")
    
    # 5. Teste de limites de uso com detalhes do erro
    print("\n5. Testando limites de uso...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/usage/limits?user_id=1")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            limits = response.json()
            print(f"✅ Limites: {limits}")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao testar limites: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 TESTE DETALHADO CONCLUÍDO!")

if __name__ == "__main__":
    test_detailed_endpoints()
