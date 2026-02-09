#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Completo da API B3 FastAPI AI - Frontend
Este script testa todos os endpoints e modelos disponíveis
para validação completa do sistema antes do uso em produção.
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configuração da API
API_BASE_URL = "http://localhost:8012"  # Porta configurada no .env
HEADERS = {"Content-Type": "application/json"}

class APITester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def log_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Registra resultado de um teste"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASSOU"
        else:
            self.failed_tests += 1
            status = "❌ FALHOU"
        
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": time.strftime('%H:%M:%S')
        }
        self.results.append(result)
        print(f"{status} - {test_name}")
        if not success:
            print(f"   Erro: {details.get('error', 'Erro desconhecido')}")
    
    def test_health_check(self):
        """Testa endpoint de saúde"""
        try:
            response = requests.get(f"{API_BASE_URL}/chatbot/health", headers=HEADERS, timeout=10)
            success = response.status_code == 200
            details = {
                "status_code": response.status_code,
                "response": response.json() if success else response.text
            }
            self.log_result("Health Check", success, details)
        except Exception as e:
            self.log_result("Health Check", False, {"error": str(e)})
    
    def test_providers_endpoint(self):
        """Testa endpoint de provedores"""
        try:
            response = requests.get(f"{API_BASE_URL}/ai/providers", headers=HEADERS, timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            details = {
                "status_code": response.status_code,
                "providers_count": len(data.get('providers', [])),
                "default_provider": data.get('default_provider'),
                "supported_providers": data.get('supported_providers', [])
            }
            self.log_result("Providers Endpoint", success, details)
            return data if success else None
        except Exception as e:
            self.log_result("Providers Endpoint", False, {"error": str(e)})
            return None
    
    def test_models_endpoint(self):
        """Testa endpoint de modelos"""
        try:
            response = requests.get(f"{API_BASE_URL}/ai/models?provider=openai", headers=HEADERS, timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            details = {
                "status_code": response.status_code,
                "provider": data.get('provider'),
                "models_count": len(data.get('models', [])),
                "models": data.get('models', []),
                "default_model": data.get('default_model')
            }
            self.log_result("Models Endpoint (OpenAI)", success, details)
            return data.get('models', []) if success else []
        except Exception as e:
            self.log_result("Models Endpoint (OpenAI)", False, {"error": str(e)})
            return []
    
    def test_ai_generation(self, model: str, test_message: str):
        """Testa geração de resposta com um modelo específico"""
        try:
            data = {
                "messages": [
                    {"role": "user", "content": test_message}
                ],
                "provider": "openai",
                "model": model,
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            response = requests.post(f"{API_BASE_URL}/ai/generate", json=data, headers=HEADERS, timeout=30)
            success = response.status_code == 200
            result = response.json() if success else {}
            
            details = {
                "status_code": response.status_code,
                "model_used": result.get('model'),
                "provider_used": result.get('provider'),
                "usage": result.get('usage'),
                "response_length": len(str(result.get('response', ''))),
                "has_response": bool(result.get('response'))
            }
            
            if not success:
                details["error"] = response.text
            
            self.log_result(f"AI Generation - {model}", success, details)
            return result if success else None
        except Exception as e:
            self.log_result(f"AI Generation - {model}", False, {"error": str(e)})
            return None
    
    def test_streaming(self, model: str):
        """Testa streaming com um modelo específico"""
        try:
            data = {
                "messages": [
                    {"role": "user", "content": "Conte até 5 em português"}
                ],
                "provider": "openai",
                "model": model,
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            response = requests.post(f"{API_BASE_URL}/ai/generate/stream", json=data, headers=HEADERS, timeout=30, stream=True)
            success = response.status_code == 200
            
            chunks_received = 0
            total_content = ""
            
            if success:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                json_str = line_str[6:]  # Remove 'data: ' prefix
                                if json_str.strip() == '':
                                    continue
                                chunk_data = json.loads(json_str)
                                if 'content' in chunk_data and chunk_data['content'] != '[DONE]':
                                    total_content += chunk_data['content']
                                    chunks_received += 1
                                elif chunk_data.get('content') == '[DONE]':
                                    break
                            except json.JSONDecodeError:
                                continue
            
            details = {
                "status_code": response.status_code,
                "chunks_received": chunks_received,
                "total_content_length": len(total_content),
                "has_content": bool(total_content.strip())
            }
            
            if not success:
                details["error"] = response.text
            
            self.log_result(f"Streaming - {model}", success and chunks_received > 0, details)
        except Exception as e:
            self.log_result(f"Streaming - {model}", False, {"error": str(e)})
    
    def run_comprehensive_tests(self):
        """Executa todos os testes"""
        print("🚀 INICIANDO TESTES COMPLETOS DA API B3 FastAPI AI")
        print(f"🕐 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Base URL: {API_BASE_URL}")
        print("="*60)
        
        # 1. Teste de saúde
        print("\n📋 1. TESTE DE SAÚDE")
        self.test_health_check()
        
        # 2. Teste de provedores
        print("\n📋 2. TESTE DE PROVEDORES")
        providers_data = self.test_providers_endpoint()
        
        # 3. Teste de modelos
        print("\n📋 3. TESTE DE MODELOS")
        available_models = self.test_models_endpoint()
        
        # 4. Testes de geração de IA
        print("\n📋 4. TESTES DE GERAÇÃO DE IA")
        test_messages = [
            "Olá, qual é o seu nome?",
            "Analise: Compra 100 PETR4 a R$ 35,50",
            "Explique o que é stop loss"
        ]
        
        for model in available_models:
            for i, message in enumerate(test_messages):
                if i == 0:  # Só testa a primeira mensagem para cada modelo
                    self.test_ai_generation(model, message)
                    break
        
        # 5. Testes de streaming
        print("\n📋 5. TESTES DE STREAMING")
        for model in available_models[:2]:  # Testa apenas os 2 primeiros modelos
            self.test_streaming(model)
        
        # Relatório final
        self.print_final_report()
    
    def print_final_report(self):
        """Imprime relatório final dos testes"""
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL DOS TESTES")
        print("="*60)
        print(f"Total de testes: {self.total_tests}")
        print(f"✅ Testes aprovados: {self.passed_tests}")
        print(f"❌ Testes falharam: {self.failed_tests}")
        print(f"📈 Taxa de sucesso: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        if self.failed_tests > 0:
            print("\n❌ TESTES QUE FALHARAM:")
            for result in self.results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details'].get('error', 'Erro desconhecido')}")
        
        print("\n🎯 RESUMO DOS MODELOS TESTADOS:")
        model_tests = [r for r in self.results if 'AI Generation' in r['test']]
        for test in model_tests:
            model_name = test['test'].replace('AI Generation - ', '')
            status = "✅" if test['success'] else "❌"
            print(f"   {status} {model_name}")
        
        print("\n" + "="*60)
        print("🏁 TESTES CONCLUÍDOS!")
        
        if self.passed_tests == self.total_tests:
            print("🎉 TODOS OS TESTES PASSARAM! API está pronta para uso.")
        elif self.passed_tests >= self.total_tests * 0.8:
            print("⚠️ Maioria dos testes passou. Verifique os erros antes de usar em produção.")
        else:
            print("🚨 Muitos testes falharam. API precisa de correções antes do uso.")

def main():
    """Função principal"""
    tester = APITester()
    tester.run_comprehensive_tests()

if __name__ == "__main__":
    main()