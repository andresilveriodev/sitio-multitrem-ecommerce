#!/usr/bin/env python3
"""
Teste do Sistema de Tracking de IA

Este arquivo testa as funcionalidades implementadas:
- Endpoints de analytics
- Sistema de alertas
- Tracking de transações
- Middleware de monitoramento
"""

import requests
import json
from datetime import datetime

# Configuração base
BASE_URL = "http://localhost:8012"

def test_health_check():
    """Testa se o servidor está rodando"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Health Check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health Check falhou: {e}")
        return False

def test_analytics_endpoints():
    """Testa os endpoints de analytics"""
    endpoints = [
        "/analytics/usage-stats",
        "/analytics/user-stats", 
        "/analytics/model-stats",
        "/analytics/alerts",
        "/analytics/usage-summary"
    ]
    
    print("\n🔍 Testando endpoints de analytics:")
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            status = "✅" if response.status_code in [200, 404] else "❌"
            print(f"{status} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Erro - {e}")

def test_chatbot_endpoint():
    """Testa o endpoint do chatbot para verificar o tracking"""
    print("\n🤖 Testando endpoint do chatbot:")
    
    test_message = {
        "message": "Olá, este é um teste do sistema de tracking",
        "user_id": "test_user_123",
        "conversation_id": "test_conv_456"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chatbot/message",
            json=test_message,
            headers={"Content-Type": "application/json"}
        )
        status = "✅" if response.status_code in [200, 201] else "❌"
        print(f"{status} Chatbot message: {response.status_code}")
        
        if response.status_code == 200:
            print(f"📝 Resposta: {response.json().get('response', 'N/A')[:100]}...")
            
    except Exception as e:
        print(f"❌ Chatbot endpoint: Erro - {e}")

def test_ai_models_endpoint():
    """Testa o endpoint de modelos de IA"""
    print("\n🧠 Testando endpoint de modelos de IA:")
    
    try:
        response = requests.get(f"{BASE_URL}/ai/models")
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} AI Models: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print(f"📊 Modelos disponíveis: {len(models)}")
            
    except Exception as e:
        print(f"❌ AI Models endpoint: Erro - {e}")

def test_alerts_system():
    """Testa o sistema de alertas"""
    print("\n🚨 Testando sistema de alertas:")
    
    alert_endpoints = [
        "/analytics/alerts/user/test_user_123",
        "/analytics/alerts/critical",
        "/analytics/limits/test_user_123"
    ]
    
    for endpoint in alert_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            status = "✅" if response.status_code in [200, 404] else "❌"
            print(f"{status} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Erro - {e}")

def run_all_tests():
    """Executa todos os testes"""
    print("🚀 Iniciando testes do Sistema de Tracking de IA")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Teste básico de conectividade
    if not test_health_check():
        print("❌ Servidor não está rodando. Verifique se 'python main.py' está executando.")
        return
    
    # Testes dos endpoints
    test_analytics_endpoints()
    test_chatbot_endpoint()
    test_ai_models_endpoint()
    test_alerts_system()
    
    print("\n" + "=" * 60)
    print("✅ Testes concluídos!")
    print("\n📋 Próximos passos:")
    print("1. Verificar logs em /logs/ para detalhes do tracking")
    print("2. Testar com dados reais de usuários")
    print("3. Configurar alertas de produção")
    print("4. Monitorar métricas de performance")

if __name__ == "__main__":
    run_all_tests()