#!/usr/bin/env python3
"""
Exemplos de uso do Chatbot Service
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Configuração
BASE_URL = "http://localhost:8008"
USER_ID = "test_user_123"

async def test_health_check():
    """Testa o health check do serviço"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print("🔍 Health Check:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()

async def test_auto_response():
    """Testa resposta automática para perguntas simples"""
    async with httpx.AsyncClient() as client:
        # Teste de saudação
        data = {
            "user_id": USER_ID,
            "message": "Oi, como você está?"
        }
        response = await client.post(f"{BASE_URL}/chatbot/process-message", json=data)
        
        print("🤖 Resposta Automática (Saudação):")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Response: {result['response']['response']}")
            print(f"Processing Time: {result['metadata']['processing_time']:.3f}s")
            print(f"Auto Response: {result['metadata']['auto_response']}")
        print()

async def test_ai_request():
    """Testa requisição que requer IA"""
    async with httpx.AsyncClient() as client:
        # Teste de pergunta complexa
        data = {
            "user_id": USER_ID,
            "message": "Qual é a análise técnica da Petrobras para esta semana?"
        }
        response = await client.post(f"{BASE_URL}/chatbot/process-message", json=data)
        
        print("🧠 Requisição com IA:")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Requires AI: {result['metadata']['requires_ai']}")
            print(f"Processing Time: {result['metadata']['processing_time']:.3f}s")
            print(f"Urgency: {result['metadata']['urgency']}")
            print(f"Keywords: {result['metadata']['keywords']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        print()

async def test_cache_functionality():
    """Testa funcionalidade de cache"""
    async with httpx.AsyncClient() as client:
        # Primeira requisição
        data = {
            "user_id": USER_ID,
            "message": "Que horas são?"
        }
        
        print("⏰ Teste de Cache:")
        
        # Primeira chamada
        response1 = await client.post(f"{BASE_URL}/chatbot/process-message", json=data)
        result1 = response1.json()
        print(f"Primeira chamada - Cache Hit: {result1['metadata']['cache_hit']}")
        print(f"Tempo: {result1['metadata']['processing_time']:.3f}s")
        
        # Segunda chamada (deve usar cache)
        response2 = await client.post(f"{BASE_URL}/chatbot/process-message", json=data)
        result2 = response2.json()
        print(f"Segunda chamada - Cache Hit: {result2['metadata']['cache_hit']}")
        print(f"Tempo: {result2['metadata']['processing_time']:.3f}s")
        print()

async def test_analytics():
    """Testa endpoints de analytics"""
    async with httpx.AsyncClient() as client:
        print("📊 Analytics:")
        
        # Cache stats
        response = await client.get(f"{BASE_URL}/chatbot/cache-stats")
        cache_stats = response.json()
        print(f"Cache Stats: {cache_stats['cache_stats']}")
        
        # System health
        response = await client.get(f"{BASE_URL}/chatbot/system-health")
        health = response.json()
        print(f"System Health: {health['health']['overall_status']}")
        print()

async def test_invalid_message():
    """Testa mensagem inválida"""
    async with httpx.AsyncClient() as client:
        data = {
            "user_id": USER_ID,
            "message": ""  # Mensagem vazia
        }
        response = await client.post(f"{BASE_URL}/chatbot/process-message", json=data)
        
        print("❌ Mensagem Inválida:")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Success: {result['success']}")
        print(f"Error: {result['error']}")
        print()

async def main():
    """Função principal"""
    print("🚀 Testando Chatbot Service")
    print("=" * 50)
    
    try:
        await test_health_check()
        await test_auto_response()
        await test_ai_request()
        await test_cache_functionality()
        await test_analytics()
        await test_invalid_message()
        
        print("✅ Todos os testes concluídos!")
        
    except httpx.ConnectError:
        print("❌ Erro: Não foi possível conectar ao Chatbot Service")
        print("💡 Certifique-se de que o serviço está rodando em http://localhost:8008")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(main())


