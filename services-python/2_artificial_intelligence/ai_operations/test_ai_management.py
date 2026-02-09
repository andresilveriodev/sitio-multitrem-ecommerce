#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste dos novos endpoints de gerenciamento de IA
"""

import requests
import json
import time

BASE_URL = "http://localhost:8012"

def test_ai_management_endpoints():
    """Testa os novos endpoints de gerenciamento de IA"""
    
    print("🧪 TESTANDO ENDPOINTS DE GERENCIAMENTO DE IA")
    print("=" * 50)
    
    # 1. Teste de health check
    print("\n1. Testando health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
    
    # 2. Teste de modelos de IA
    print("\n2. Testando listagem de modelos...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/models")
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Modelos encontrados: {len(models)}")
            for model in models[:3]:  # Mostra apenas os primeiros 3
                print(f"   - {model['name']} ({model['provider']}) - R$ {model['cost_per_1k_tokens']}/1k tokens")
        else:
            print(f"❌ Erro ao buscar modelos: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar modelos: {e}")
    
    # 3. Teste de planos de assinatura
    print("\n3. Testando planos de assinatura...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/subscriptions")
        if response.status_code == 200:
            plans = response.json()
            print(f"✅ Planos encontrados: {len(plans)}")
            for plan in plans:
                print(f"   - {plan['name']}: R$ {plan['price']}/mês")
        else:
            print(f"❌ Erro ao buscar planos: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar planos: {e}")
    
    # 4. Teste de configurações de IA (usuário 1)
    print("\n4. Testando configurações de IA...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/settings?user_id=1&username=testuser")
        if response.status_code == 200:
            settings = response.json()
            print(f"✅ Configurações do usuário 1:")
            print(f"   - Modelo padrão: {settings['default_model']}")
            print(f"   - Auto fallback: {settings['auto_fallback']}")
        else:
            print(f"❌ Erro ao buscar configurações: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar configurações: {e}")
    
    # 5. Teste de limites de uso (usuário 1)
    print("\n5. Testando limites de uso...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/ai/usage/limits?user_id=1")
        if response.status_code == 200:
            limits = response.json()
            print(f"✅ Limites do usuário 1:")
            print(f"   - Pode usar: {limits['can_use']}")
            if not limits['can_use']:
                print(f"   - Motivo: {limits['reason']}")
            if 'current_usage' in limits:
                usage = limits['current_usage']
                print(f"   - Uso atual: {usage.get('requests_used', 0)} requests, {usage.get('tokens_used', 0)} tokens")
        else:
            print(f"❌ Erro ao buscar limites: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar limites: {e}")
    
    # 6. Teste de assinatura de plano
    print("\n6. Testando assinatura de plano...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/ai/subscriptions/free/subscribe?user_id=1&username=testuser")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Assinatura criada: {result['message']}")
        else:
            print(f"❌ Erro ao assinar plano: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar assinatura: {e}")
    
    # 7. Teste de atualização de configurações
    print("\n7. Testando atualização de configurações...")
    try:
        update_data = {
            "default_model": "gpt-4o-mini",
            "preferred_models": ["gpt-4o-mini", "deepseek", "ollama"]
        }
        response = requests.put(f"{BASE_URL}/api/v1/ai/settings?user_id=1&username=testuser", json=update_data)
        if response.status_code == 200:
            settings = response.json()
            print(f"✅ Configurações atualizadas:")
            print(f"   - Novo modelo padrão: {settings['default_model']}")
        else:
            print(f"❌ Erro ao atualizar configurações: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro ao testar atualização: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 TESTE CONCLUÍDO!")

if __name__ == "__main__":
    # Aguarda um pouco para o servidor inicializar
    print("⏳ Aguardando servidor inicializar...")
    time.sleep(3)
    
    test_ai_management_endpoints()
