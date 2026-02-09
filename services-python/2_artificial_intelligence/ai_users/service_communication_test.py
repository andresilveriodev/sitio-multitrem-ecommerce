#!/usr/bin/env python3
import asyncio
import httpx
import json
from typing import Dict, Any

class ServiceCommunicationTester:
    def __init__(self, ai_service_url: str = "http://localhost:8012"):
        self.ai_service_url = ai_service_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def test_ai_service_health(self) -> Dict[str, Any]:
        """Testa se o AI Service está respondendo"""
        try:
            response = await self.client.get(f"{self.ai_service_url}/health")
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "AI Service is healthy"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Health check failed with status {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def test_analytics_endpoints(self, user_id: int = 1) -> Dict[str, Any]:
        """Testa endpoints de analytics"""
        results = {}
        
        # Teste de estatísticas do usuário
        try:
            response = await self.client.get(f"{self.ai_service_url}/analytics/users/{user_id}/stats")
            results["user_stats"] = {
                "status": "success",
                "code": response.status_code,
                "data": response.json()
            }
        except Exception as e:
            results["user_stats"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Teste de análise de custos
        try:
            response = await self.client.get(f"{self.ai_service_url}/analytics/cost/analysis?user_id={user_id}")
            results["cost_analysis"] = {
                "status": "success",
                "code": response.status_code,
                "data": response.json()
            }
        except Exception as e:
            results["cost_analysis"] = {
                "status": "error",
                "error": str(e)
            }
        
        return results
    
    async def test_chatbot_endpoints(self, user_id: int = 1) -> Dict[str, Any]:
        """Testa endpoints de chatbot"""
        results = {}
        
        # Teste de conversas do usuário
        try:
            response = await self.client.get(f"{self.ai_service_url}/chatbot/users/{user_id}/conversations")
            results["user_conversations"] = {
                "status": "success",
                "code": response.status_code,
                "data": response.json()
            }
        except Exception as e:
            results["user_conversations"] = {
                "status": "error",
                "error": str(e)
            }
        
        return results
    
    async def test_ai_endpoints(self) -> Dict[str, Any]:
        """Testa endpoints de AI"""
        results = {}
        
        # Teste de modelos disponíveis
        try:
            response = await self.client.get(f"{self.ai_service_url}/ai/models")
            results["available_models"] = {
                "status": "success",
                "code": response.status_code,
                "data": response.json()
            }
        except Exception as e:
            results["available_models"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Teste de providers
        try:
            response = await self.client.get(f"{self.ai_service_url}/ai/providers")
            results["providers"] = {
                "status": "success",
                "code": response.status_code,
                "data": response.json()
            }
        except Exception as e:
            results["providers"] = {
                "status": "error",
                "error": str(e)
            }
        
        return results
    
    async def run_all_tests(self, user_id: int = 1) -> Dict[str, Any]:
        """Executa todos os testes"""
        print("🧪 Iniciando testes de comunicação entre serviços...")
        print("=" * 60)
        
        results = {
            "timestamp": asyncio.get_event_loop().time(),
            "ai_service_url": self.ai_service_url,
            "tests": {}
        }
        
        # Teste de saúde
        print("🔍 Testando saúde do AI Service...")
        health_result = await self.test_ai_service_health()
        results["tests"]["health"] = health_result
        
        # Teste de analytics
        print("📊 Testando endpoints de analytics...")
        results["tests"]["analytics"] = await self.test_analytics_endpoints(user_id)
        
        # Teste de chatbot
        print("🤖 Testando endpoints de chatbot...")
        results["tests"]["chatbot"] = await self.test_chatbot_endpoints(user_id)
        
        # Teste de AI
        print("⚙️ Testando endpoints de AI...")
        results["tests"]["ai"] = await self.test_ai_endpoints()
        
        # Resumo
        print("\n" + "=" * 60)
        print("📋 RESUMO DOS TESTES:")
        print("-" * 50)
        
        total_tests = 0
        successful_tests = 0
        
        for category, category_tests in results["tests"].items():
            print(f"\n{category.upper()}:")
            if category == "health":
                # Teste de health é um resultado único
                total_tests += 1
                if isinstance(category_tests, dict) and category_tests.get("status") == "success":
                    successful_tests += 1
                    print(f"  ✅ Health Check: OK")
                else:
                    error_msg = category_tests.get('error', 'Unknown') if isinstance(category_tests, dict) else str(category_tests)
                    print(f"  ❌ Health Check: ERRO - {error_msg}")
            elif isinstance(category_tests, dict):
                for test_name, test_result in category_tests.items():
                    total_tests += 1
                    if isinstance(test_result, dict) and test_result.get("status") == "success":
                        successful_tests += 1
                        print(f"  ✅ {test_name}: OK")
                    else:
                        error_msg = test_result.get('error', 'Unknown') if isinstance(test_result, dict) else str(test_result)
                        print(f"  ❌ {test_name}: ERRO - {error_msg}")
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎯 Taxa de Sucesso: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        
        if success_rate == 100:
            print("🎉 TODOS OS TESTES PASSARAM! Comunicação entre serviços OK!")
        elif success_rate >= 80:
            print("⚠️ Maioria dos testes passou, mas há alguns problemas.")
        else:
            print("❌ Muitos testes falharam. Verificar conectividade.")
        
        await self.client.aclose()
        return results

async def main():
    tester = ServiceCommunicationTester()
    results = await tester.run_all_tests()
    
    # Salvar resultados em arquivo
    with open("service_communication_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Resultados salvos em: service_communication_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
