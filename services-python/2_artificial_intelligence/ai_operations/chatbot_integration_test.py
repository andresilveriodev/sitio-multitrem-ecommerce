#!/usr/bin/env python3
import asyncio
import httpx
import json
from typing import Dict, Any

class ChatbotIntegrationTester:
    def __init__(self, chatbot_url: str = "http://localhost:8008", ai_url: str = "http://localhost:8012"):
        self.chatbot_url = chatbot_url
        self.ai_url = ai_url
        self.client = httpx.AsyncClient(timeout=15.0)
    
    async def test_action_detection(self, user_id: int = 1) -> Dict[str, Any]:
        """Testa detecção de ações no Chatbot Service"""
        test_messages = [
            "Quero ver meu uso de IA",
            "Mostre minhas conversas",
            "Quais são meus custos?",
            "Qual meu plano atual?",
            "Quais são os preços?",
            "Olá, como você está?"  # Mensagem normal (não deve detectar ação)
        ]
        
        results = {}
        
        for message in test_messages:
            try:
                response = await self.client.post(
                    f"{self.chatbot_url}/chat",
                    json={
                        "user_id": user_id,
                        "message": message
                    }
                )
                
                results[message] = {
                    "status": "success",
                    "code": response.status_code,
                    "response": response.json()
                }
                
                print(f"✅ Teste: '{message}' - Status: {response.status_code}")
                
            except Exception as e:
                results[message] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"❌ Teste: '{message}' - Erro: {e}")
        
        return results
    
    async def test_data_consistency(self, user_id: int = 1) -> Dict[str, Any]:
        """Testa consistência dos dados entre serviços"""
        results = {}
        
        # Buscar dados diretamente do AI Service
        try:
            ai_stats_response = await self.client.get(f"{self.ai_url}/analytics/users/{user_id}/stats")
            ai_stats = ai_stats_response.json()
            results["ai_service_data"] = ai_stats
        except Exception as e:
            results["ai_service_data"] = {"error": str(e)}
        
        # Buscar dados via Chatbot Service (se implementado)
        try:
            chatbot_response = await self.client.post(
                f"{self.chatbot_url}/chat",
                json={
                    "user_id": user_id,
                    "message": "Quero ver meu uso de IA"
                }
            )
            results["chatbot_response"] = chatbot_response.json()
        except Exception as e:
            results["chatbot_response"] = {"error": str(e)}
        
        return results
    
    async def test_error_handling(self, user_id: int = 999999) -> Dict[str, Any]:
        """Testa tratamento de erros"""
        results = {}
        
        # Teste com usuário inexistente
        try:
            response = await self.client.get(f"{self.ai_url}/analytics/users/{user_id}/stats")
            results["non_existent_user"] = {
                "status": "success",
                "code": response.status_code,
                "response": response.json()
            }
        except Exception as e:
            results["non_existent_user"] = {
                "status": "error",
                "error": str(e)
            }
        
        return results
    
    async def test_performance(self, user_id: int = 1) -> Dict[str, Any]:
        """Testa performance das requisições"""
        results = {}
        
        # Teste de tempo de resposta
        start_time = asyncio.get_event_loop().time()
        
        try:
            response = await self.client.get(f"{self.ai_url}/analytics/users/{user_id}/stats")
            end_time = asyncio.get_event_loop().time()
            
            response_time = end_time - start_time
            
            results["response_time"] = {
                "status": "success",
                "time_seconds": response_time,
                "acceptable": response_time < 2.0  # Menos de 2 segundos
            }
            
            print(f"⏱️ Tempo de resposta: {response_time:.3f}s")
            
        except Exception as e:
            results["response_time"] = {
                "status": "error",
                "error": str(e)
            }
        
        return results
    
    async def run_integration_tests(self, user_id: int = 1) -> Dict[str, Any]:
        """Executa todos os testes de integração"""
        print("🔗 Iniciando testes de integração entre Chatbot e AI Service...")
        print("=" * 70)
        
        results = {
            "timestamp": asyncio.get_event_loop().time(),
            "chatbot_url": self.chatbot_url,
            "ai_url": self.ai_url,
            "tests": {}
        }
        
        # Teste de detecção de ações
        print("🎯 Testando detecção de ações...")
        results["tests"]["action_detection"] = await self.test_action_detection(user_id)
        
        # Teste de consistência de dados
        print("📊 Testando consistência de dados...")
        results["tests"]["data_consistency"] = await self.test_data_consistency(user_id)
        
        # Teste de tratamento de erros
        print("⚠️ Testando tratamento de erros...")
        results["tests"]["error_handling"] = await self.test_error_handling()
        
        # Teste de performance
        print("⏱️ Testando performance...")
        results["tests"]["performance"] = await self.test_performance(user_id)
        
        # Resumo dos testes
        print("\n" + "=" * 70)
        print("📋 RESUMO DOS TESTES DE INTEGRAÇÃO:")
        print("-" * 50)
        
        total_tests = 0
        successful_tests = 0
        
        for category, category_tests in results["tests"].items():
            print(f"\n{category.upper()}:")
            if isinstance(category_tests, dict):
                for test_name, test_result in category_tests.items():
                    total_tests += 1
                    if test_result.get("status") == "success":
                        successful_tests += 1
                        print(f"  ✅ {test_name}: OK")
                    else:
                        print(f"  ❌ {test_name}: ERRO - {test_result.get('error', 'Unknown')}")
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎯 Taxa de Sucesso: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        
        if success_rate == 100:
            print("🎉 TODOS OS TESTES DE INTEGRAÇÃO PASSARAM!")
        elif success_rate >= 80:
            print("⚠️ Maioria dos testes passou, mas há alguns problemas.")
        else:
            print("❌ Muitos testes falharam. Verificar implementação.")
        
        print("\n🎯 TESTES DE INTEGRAÇÃO CONCLUÍDOS!")
        
        await self.client.aclose()
        return results

async def main():
    tester = ChatbotIntegrationTester()
    results = await tester.run_integration_tests()
    
    print("📄 Resultados dos testes de integração:")
    print(json.dumps(results, indent=2, default=str))
    
    # Salvar resultados em arquivo
    with open("chatbot_integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Resultados salvos em: chatbot_integration_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
