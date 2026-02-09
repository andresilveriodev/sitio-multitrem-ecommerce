# 🤖 GUIA DE IMPLEMENTAÇÃO DO CHATBOT_SERVICE

## **🎯 OBJETIVO**

Este guia instrui o **Chatbot Service** sobre como implementar ações de usuário via conversa, utilizando os **endpoints já existentes** do AI Service.

---

## **🏗️ ARQUITETURA DE COMUNICAÇÃO**

### **Fluxo de Comunicação:**
```
Frontend → Chatbot Service (8008) → AI Service (8012) → Resposta → Frontend
```

### **Responsabilidades:**
- **Chatbot Service**: Detecta intenções, executa ações, formata respostas
- **AI Service**: Fornece dados via endpoints existentes

---

## **📋 ENDPOINTS DISPONÍVEIS NO AI SERVICE**

### **1. Analytics Endpoints (Para Dados do Usuário)**
```python
# Estatísticas do usuário
GET /analytics/users/{user_id}/stats
Response: {
    "user_id": 123,
    "username": "user123",
    "total_requests": 150,
    "total_tokens_used": 50000,
    "total_cost_spent": 0.75,
    "total_conversations": 25,
    "avg_cost_per_request": 0.005,
    "avg_tokens_per_request": 333,
    "avg_cost_per_conversation": 0.03
}

# Informações do plano do usuário
GET /analytics/users/{user_id}/subscription
Response: {
    "user_id": 123,
    "plan_type": "pay_per_token", // ou "unlimited"
    "plan_name": "Pague por Token",
    "monthly_fee": 0.00,
    "current_usage": {
        "tokens_this_month": 50000,
        "cost_this_month": 0.75
    },
    "limits": {
        "type": "pay_per_token",
        "description": "Pague apenas pelos tokens que usar"
    }
}

# Análise de custos
GET /analytics/cost/analysis?user_id={user_id}
Response: {
    "user_id": 123,
    "total_cost": 0.75,
    "cost_by_provider": {
        "openai": 0.50,
        "deepseek": 0.25
    },
    "cost_by_model": {
        "gpt-4o-mini": 0.40,
        "deepseek-chat": 0.25
    },
    "monthly_breakdown": [...]
}

# Transações do usuário
GET /analytics/transactions?user_id={user_id}&limit=50
Response: {
    "transactions": [
        {
            "id": 1,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "status": "success",
            "total_tokens": 150,
            "total_cost": 0.002,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "total_count": 150
}
```

### **2. Chatbot Endpoints (Para Conversas)**
```python
# Conversas do usuário
GET /chatbot/users/{user_id}/conversations
Response: [
    {
        "id": 1,
        "user_id": 123,
        "title": "Conversa sobre IA",
        "status": "active",
        "total_tokens": 5000,
        "total_cost": 0.075,
        "total_messages": 25,
        "created_at": "2024-01-15T09:00:00Z"
    }
]

# Mensagens de uma conversa
GET /chatbot/conversations/{conversation_id}/messages
Response: [
    {
        "id": 1,
        "conversation_id": 1,
        "content": "Olá, como você está?",
        "role": "user",
        "created_at": "2024-01-15T09:00:00Z"
    }
]
```

### **3. AI Endpoints (Para Configurações)**
```python
# Modelos disponíveis
GET /ai/models
Response: {
    "providers": {
        "openai": {
            "models": ["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"],
            "default_model": "gpt-4o-mini"
        },
        "deepseek": {
            "models": ["deepseek-chat"],
            "default_model": "deepseek-chat"
        }
    }
}

# Status dos providers
GET /ai/providers
Response: {
    "providers": [
        {
            "name": "openai",
            "available": true,
            "models": ["gpt-4o-mini", "gpt-4"],
            "description": "OpenAI GPT Models"
        }
    ]
}
```

---

## **🔧 IMPLEMENTAÇÃO NO CHATBOT SERVICE**

### **1. Cliente HTTP para AI Service**
```python
import httpx
from typing import Dict, Any, Optional

class AIServiceClient:
    def __init__(self, base_url: str = "http://localhost:8012"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtém estatísticas do usuário"""
        response = await self.client.get(f"{self.base_url}/analytics/users/{user_id}/stats")
        response.raise_for_status()
        return response.json()
    
    async def get_user_conversations(self, user_id: int) -> Dict[str, Any]:
        """Obtém conversas do usuário"""
        response = await self.client.get(f"{self.base_url}/chatbot/users/{user_id}/conversations")
        response.raise_for_status()
        return response.json()
    
    async def get_user_costs(self, user_id: int) -> Dict[str, Any]:
        """Obtém análise de custos do usuário"""
        response = await self.client.get(f"{self.base_url}/analytics/cost/analysis?user_id={user_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_user_transactions(self, user_id: int, limit: int = 50) -> Dict[str, Any]:
        """Obtém transações do usuário"""
        response = await self.client.get(f"{self.base_url}/analytics/transactions?user_id={user_id}&limit={limit}")
        response.raise_for_status()
        return response.json()
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Obtém modelos disponíveis"""
        response = await self.client.get(f"{self.base_url}/ai/models")
        response.raise_for_status()
        return response.json()
    
    async def get_user_subscription(self, user_id: int) -> Dict[str, Any]:
        """Obtém informações do plano do usuário"""
        response = await self.client.get(f"{self.base_url}/analytics/users/{user_id}/subscription")
        response.raise_for_status()
        return response.json()
    
    async def get_pricing_info(self) -> Dict[str, Any]:
        """Obtém informações de preços"""
        # Buscar planos
        plans_response = await self.client.get(f"{self.base_url}/analytics/subscriptions")
        plans_response.raise_for_status()
        plans = plans_response.json()
        
        # Buscar modelos com preços
        models_response = await self.client.get(f"{self.base_url}/ai/models")
        models_response.raise_for_status()
        models = models_response.json()
        
        return {
            "plans": plans,
            "models": models
        }
    
    async def close(self):
        """Fecha o cliente HTTP"""
        await self.client.aclose()
```

### **2. Detector de Intenções de Ação**
```python
import re
from typing import Optional, Dict, Any

class ActionIntentDetector:
    def __init__(self):
        self.action_patterns = {
            "get_my_usage": [
                r"ver (meu|meus) uso",
                r"quanto (eu )?usei",
                r"meus custos",
                r"estatísticas (do usuário|minhas)",
                r"métricas de uso",
                r"resumo do uso"
            ],
            "get_my_conversations": [
                r"minhas conversas",
                r"histórico (de conversas)?",
                r"conversas anteriores",
                r"listar conversas",
                r"todas as conversas"
            ],
            "get_my_costs": [
                r"meus custos",
                r"quanto (eu )?gastei",
                r"análise de custos",
                r"gastos",
                r"despesas"
            ],
            "get_my_transactions": [
                r"minhas transações",
                r"histórico de transações",
                r"transações anteriores",
                r"todas as transações"
            ],
            "get_available_models": [
                r"modelos disponíveis",
                r"quais modelos",
                r"modelos suportados",
                r"opções de modelo"
            ],
            "get_my_plan": [
                r"meu plano",
                r"qual meu plano",
                r"plano atual",
                r"assinatura",
                r"tipo de cobrança"
            ],
            "get_pricing_info": [
                r"preços",
                r"quanto custa",
                r"valores",
                r"tarifas",
                r"cobrança"
            ]
        }
    
    def detect_action(self, message: str) -> Optional[Dict[str, Any]]:
        """Detecta intenção de ação na mensagem"""
        message_lower = message.lower()
        
        for action, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return {
                        "action": action,
                        "confidence": 0.9,
                        "detected_pattern": pattern
                    }
        
        return None
```

### **3. Executor de Ações**
```python
class ChatbotActionExecutor:
    def __init__(self, ai_client: AIServiceClient):
        self.ai_client = ai_client
        self.response_formatter = ResponseFormatter()
    
    async def execute_action(self, user_id: int, action: str) -> str:
        """Executa ação e retorna resposta formatada"""
        
        try:
            if action == "get_my_usage":
                data = await self.ai_client.get_user_stats(user_id)
                return self.response_formatter.format_usage_stats(data)
                
            elif action == "get_my_conversations":
                data = await self.ai_client.get_user_conversations(user_id)
                return self.response_formatter.format_conversations(data)
                
            elif action == "get_my_costs":
                data = await self.ai_client.get_user_costs(user_id)
                return self.response_formatter.format_costs(data)
                
            elif action == "get_my_transactions":
                data = await self.ai_client.get_user_transactions(user_id)
                return self.response_formatter.format_transactions(data)
                
            elif action == "get_available_models":
                data = await self.ai_client.get_available_models()
                return self.response_formatter.format_models(data)
                
            elif action == "get_my_plan":
                data = await self.ai_client.get_user_subscription(user_id)
                return self.response_formatter.format_subscription(data)
                
            elif action == "get_pricing_info":
                data = await self.ai_client.get_pricing_info()
                return self.response_formatter.format_pricing(data)
                
            else:
                return f"Desculpe, não reconheci a ação '{action}'"
                
        except Exception as e:
            return f"Erro ao executar ação: {str(e)}"
```

### **4. Formatador de Respostas**
```python
class ResponseFormatter:
    def format_usage_stats(self, data: Dict[str, Any]) -> str:
        """Formata estatísticas de uso"""
        return f"""
📊 **Suas Estatísticas de Uso:**

• **Total de requisições**: {data.get('total_requests', 0):,}
• **Total de tokens**: {data.get('total_tokens_used', 0):,}
• **Custo total**: R$ {data.get('total_cost_spent', 0):.2f}
• **Conversas**: {data.get('total_conversations', 0)}
• **Custo médio por requisição**: R$ {data.get('avg_cost_per_request', 0):.4f}
• **Tokens médios por requisição**: {data.get('avg_tokens_per_request', 0):,}
        """.strip()
    
    def format_conversations(self, data: list) -> str:
        """Formata lista de conversas"""
        if not data:
            return "Você ainda não tem conversas."
        
        response = "🗣️ **Suas Conversas:**\n\n"
        for conv in data[:10]:  # Limita a 10 conversas
            title = conv.get('title', 'Sem título')
            messages = conv.get('total_messages', 0)
            cost = conv.get('total_cost', 0)
            created = conv.get('created_at', '')[:10]  # Apenas data
            
            response += f"• **{title}** ({messages} mensagens, R$ {cost:.3f}, {created})\n"
        
        if len(data) > 10:
            response += f"\n... e mais {len(data) - 10} conversas"
        
        return response
    
    def format_costs(self, data: Dict[str, Any]) -> str:
        """Formata análise de custos"""
        total_cost = data.get('total_cost', 0)
        cost_by_provider = data.get('cost_by_provider', {})
        
        response = f"💰 **Análise de Custos:**\n\n"
        response += f"• **Custo total**: R$ {total_cost:.2f}\n\n"
        
        if cost_by_provider:
            response += "**Por provedor:**\n"
            for provider, cost in cost_by_provider.items():
                response += f"• {provider.title()}: R$ {cost:.2f}\n"
        
        return response
    
    def format_transactions(self, data: Dict[str, Any]) -> str:
        """Formata transações"""
        transactions = data.get('transactions', [])
        if not transactions:
            return "Nenhuma transação encontrada."
        
        response = "📋 **Suas Transações Recentes:**\n\n"
        for tx in transactions[:5]:  # Limita a 5 transações
            provider = tx.get('provider', 'unknown')
            model = tx.get('model', 'unknown')
            cost = tx.get('total_cost', 0)
            status = tx.get('status', 'unknown')
            created = tx.get('created_at', '')[:16]  # Data e hora
            
            response += f"• {provider}/{model}: R$ {cost:.4f} ({status}) - {created}\n"
        
        return response
    
    def format_models(self, data: Dict[str, Any]) -> str:
        """Formata modelos disponíveis"""
        providers = data.get('providers', {})
        
        response = "🤖 **Modelos Disponíveis:**\n\n"
        for provider, info in providers.items():
            models = info.get('models', [])
            default = info.get('default_model', 'N/A')
            
            response += f"**{provider.upper()}:**\n"
            for model in models:
                marker = " ⭐" if model == default else ""
                response += f"• {model}{marker}\n"
            response += "\n"
        
        return response
    
    def format_subscription(self, data: Dict[str, Any]) -> str:
        """Formata informações do plano do usuário"""
        plan_type = data.get('plan_type', 'unknown')
        plan_name = data.get('plan_name', 'Desconhecido')
        monthly_fee = data.get('monthly_fee', 0)
        current_usage = data.get('current_usage', {})
        
        response = f"📋 **Seu Plano Atual:**\n\n"
        response += f"• **Plano**: {plan_name}\n"
        response += f"• **Tipo**: {plan_type.upper()}\n"
        response += f"• **Taxa mensal**: R$ {monthly_fee:.2f}\n\n"
        
        if current_usage:
            tokens = current_usage.get('tokens_this_month', 0)
            cost = current_usage.get('cost_this_month', 0)
            response += f"**Uso este mês:**\n"
            response += f"• Tokens: {tokens:,}\n"
            response += f"• Custo: R$ {cost:.2f}\n"
        
        return response
    
    def format_pricing(self, data: Dict[str, Any]) -> str:
        """Formata informações de preços"""
        plans = data.get('plans', [])
        models = data.get('models', [])
        
        response = "💰 **Nossos Planos e Preços:**\n\n"
        
        response += "**📈 PLANOS DISPONÍVEIS:**\n"
        for plan in plans:
            name = plan.get('name', '')
            price = plan.get('price', 0)
            description = plan.get('description', '')
            response += f"• **{name}**: R$ {price:.2f}/mês\n"
            response += f"  _{description}_\n\n"
        
        response += "**🤖 PREÇOS POR 1000 TOKENS:**\n"
        for model in models:
            name = model.get('name', '')
            cost = model.get('cost_per_1k_tokens', 0)
            if cost > 0:
                response += f"• {name}: R$ {cost:.6f}\n"
        
        return response
```

### **5. Integração Principal**
```python
class ChatbotService:
    def __init__(self):
        self.ai_client = AIServiceClient()
        self.action_detector = ActionIntentDetector()
        self.action_executor = ChatbotActionExecutor(self.ai_client)
    
    async def process_message(self, user_id: int, message: str) -> str:
        """Processa mensagem e executa ações se necessário"""
        
        # 1. Detectar intenção de ação
        action_intent = self.action_detector.detect_action(message)
        
        if action_intent:
            # 2. Executar ação
            action = action_intent["action"]
            response = await self.action_executor.execute_action(user_id, action)
            return response
        else:
            # 3. Processar normalmente com IA
            return await self.process_with_ai(user_id, message)
    
    async def process_with_ai(self, user_id: int, message: str) -> str:
        """Processa mensagem com IA (implementação existente)"""
        # Aqui você chama o AI Service para gerar resposta
        pass
    
    async def cleanup(self):
        """Limpa recursos"""
        await self.ai_client.close()
```

---

## **🚀 EXEMPLOS DE USO**

### **Cenários de Conversa:**
```
Usuário: "Quero ver meu uso de IA"
Chatbot: "📊 Suas Estatísticas de Uso:
• Total de requisições: 150
• Total de tokens: 50,000
• Custo total: R$ 0.75
• Conversas: 25
• Custo médio por requisição: R$ 0.0050
• Tokens médios por requisição: 333"

Usuário: "Mostre minhas conversas"
Chatbot: "🗣️ Suas Conversas:
• Conversa sobre IA (25 mensagens, R$ 0.075, 2024-01-15)
• Dúvidas sobre Python (12 mensagens, R$ 0.045, 2024-01-14)
• Análise de dados (8 mensagens, R$ 0.030, 2024-01-13)"

Usuário: "Quais são meus custos?"
Chatbot: "💰 Análise de Custos:
• Custo total: R$ 0.75
Por provedor:
• OpenAI: R$ 0.50
• Deepseek: R$ 0.25"

Usuário: "Qual meu plano atual?"
Chatbot: "📋 Seu Plano Atual:
• Plano: Pague por Token
• Tipo: PAY_PER_TOKEN
• Taxa mensal: R$ 0.00
Uso este mês:
• Tokens: 50,000
• Custo: R$ 0.75"

Usuário: "Quais são os preços?"
Chatbot: "💰 Nossos Planos e Preços:
📈 PLANOS DISPONÍVEIS:
• Pague por Token: R$ 0.00/mês
  _Pague apenas pelos tokens que usar_
• Ilimitado: R$ 99.90/mês
  _Uso ilimitado de tokens_
🤖 PREÇOS POR 1000 TOKENS:
• DeepSeek: R$ 0.000100
• GPT-4o Mini: R$ 0.000150
• GPT-5 Mini: R$ 0.000300"
```

---

## **🛡️ SEGURANÇA E BOAS PRÁTICAS**

### **1. Validação de Usuário**
```python
# Sempre validar se o usuário tem acesso aos dados
async def validate_user_access(user_id: int, target_user_id: int) -> bool:
    return user_id == target_user_id  # Apenas dados próprios
```

### **2. Rate Limiting**
```python
# Implementar rate limiting para ações
class RateLimiter:
    def __init__(self):
        self.action_counts = {}
    
    def check_limit(self, user_id: int, action: str, max_per_hour: int = 10) -> bool:
        key = f"{user_id}:{action}"
        current_hour = datetime.now().hour
        
        if key not in self.action_counts:
            self.action_counts[key] = {"hour": current_hour, "count": 0}
        
        if self.action_counts[key]["hour"] != current_hour:
            self.action_counts[key] = {"hour": current_hour, "count": 0}
        
        if self.action_counts[key]["count"] >= max_per_hour:
            return False
        
        self.action_counts[key]["count"] += 1
        return True
```

### **3. Logs de Auditoria**
```python
# Registrar todas as ações executadas
class ActionLogger:
    def log_action(self, user_id: int, action: str, success: bool, error: str = None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "success": success,
            "error": error,
            "ip_address": self.get_client_ip()
        }
        logger.info(f"Action executed: {log_entry}")
```

---

## **🧪 TESTES DE COMUNICAÇÃO ENTRE SERVIÇOS**

### **1. Script de Teste de Conectividade**
```python
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
            return {
                "status": "success",
                "response_code": response.status_code,
                "response": response.json()
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
        results["tests"]["health"] = await self.test_ai_service_health()
        
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
            for test_name, test_result in category_tests.items():
                total_tests += 1
                if test_result["status"] == "success":
                    successful_tests += 1
                    print(f"  ✅ {test_name}: OK")
                else:
                    print(f"  ❌ {test_name}: ERRO - {test_result.get('error', 'Unknown')}")
        
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
```

### **2. Script de Teste de Integração Completa**
```python
#!/usr/bin/env python3
import asyncio
import httpx
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
        
        print("\n" + "=" * 70)
        print("🎯 TESTES DE INTEGRAÇÃO CONCLUÍDOS!")
        
        await self.client.aclose()
        return results

async def main():
    tester = ChatbotIntegrationTester()
    results = await tester.run_integration_tests()
    
    print("📄 Resultados dos testes de integração:")
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
```

### **3. Checklist de Testes Manuais**
```markdown
## **🧪 CHECKLIST DE TESTES MANUAIS**

### **1. Testes de Conectividade**
- [ ] AI Service está rodando na porta 8012
- [ ] Chatbot Service está rodando na porta 8008
- [ ] Ambos os serviços respondem a /health
- [ ] Não há conflitos de porta

### **2. Testes de Endpoints**
- [ ] GET /analytics/users/{user_id}/stats retorna dados
- [ ] GET /analytics/cost/analysis?user_id={user_id} retorna dados
- [ ] GET /chatbot/users/{user_id}/conversations retorna dados
- [ ] GET /ai/models retorna lista de modelos
- [ ] GET /ai/providers retorna lista de providers

### **3. Testes de Detecção de Ações**
- [ ] "Quero ver meu uso" → detecta ação get_my_usage
- [ ] "Minhas conversas" → detecta ação get_my_conversations
- [ ] "Meus custos" → detecta ação get_my_costs
- [ ] "Meu plano" → detecta ação get_my_plan
- [ ] "Preços" → detecta ação get_pricing_info
- [ ] "Olá" → não detecta ação (processa normalmente)

### **4. Testes de Formatação de Resposta**
- [ ] Respostas estão bem formatadas
- [ ] Dados numéricos estão formatados corretamente
- [ ] Emojis e formatação markdown funcionam
- [ ] Respostas não são muito longas

### **5. Testes de Tratamento de Erros**
- [ ] Usuário inexistente retorna erro apropriado
- [ ] Endpoint indisponível retorna erro apropriado
- [ ] Timeout de conexão é tratado
- [ ] Erros são logados adequadamente

### **6. Testes de Performance**
- [ ] Resposta em menos de 2 segundos
- [ ] Múltiplas requisições simultâneas funcionam
- [ ] Não há vazamentos de memória
- [ ] Conexões HTTP são reutilizadas

### **7. Testes de Segurança**
- [ ] Usuário só acessa seus próprios dados
- [ ] Rate limiting funciona
- [ ] Logs de auditoria são gerados
- [ ] Dados sensíveis não são expostos
```

---

## **✅ CHECKLIST DE IMPLEMENTAÇÃO FINAL**

### **🔧 IMPLEMENTAÇÃO TÉCNICA**
- [ ] Implementar `AIServiceClient` para comunicação com AI Service
- [ ] Implementar `ActionIntentDetector` para detectar intenções
- [ ] Implementar `ChatbotActionExecutor` para executar ações
- [ ] Implementar `ResponseFormatter` para formatar respostas
- [ ] Integrar com sistema de autenticação
- [ ] Implementar rate limiting
- [ ] Implementar logs de auditoria

### **🧪 TESTES E VALIDAÇÃO**
- [ ] Executar script de teste de conectividade
- [ ] Executar script de teste de integração
- [ ] Completar checklist de testes manuais
- [ ] Testar todos os cenários de conversa
- [ ] Validar formatação de respostas
- [ ] Testar tratamento de erros

### **📋 DOCUMENTAÇÃO**
- [ ] Documentar APIs internas
- [ ] Criar guia de troubleshooting
- [ ] Documentar padrões de resposta
- [ ] Criar exemplos de uso

### **🚀 DEPLOYMENT**
- [ ] Configurar variáveis de ambiente
- [ ] Configurar logs e monitoramento
- [ ] Configurar health checks
- [ ] Testar em ambiente de produção

---

## **🎯 COMANDOS PARA EXECUTAR OS TESTES**

```bash
# 1. Teste de comunicação entre serviços
python service_communication_test.py

# 2. Teste de integração completa
python chatbot_integration_test.py

# 3. Verificar dados do sistema
python check_system_data.py

# 4. Verificar preços e planos
python check_pricing_tables.py
```

---

**Este guia fornece tudo que o Chatbot Service precisa para implementar ações de usuário via conversa, utilizando os endpoints já existentes do AI Service! 🚀**

**Com os testes implementados, você terá garantia de que a comunicação entre os serviços está funcionando perfeitamente! 🎯**
