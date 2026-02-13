#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de comunicação inicial para sistema homebroker
Simula ordens de compra e venda através da API de IA
"""

import urllib.request
import urllib.parse
import json
import time

# Configurações
API_URL = "http://localhost:8012/ai/generate"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def test_homebroker_communication():
    """
    Testa a comunicação inicial para o sistema homebroker
    """
    print("=== TESTE DE COMUNICAÇÃO HOMEBROKER ===")
    print(f"URL da API: {API_URL}")
    print()
    
    # Cenários de teste para homebroker com GPT-5 nano
    test_scenarios = [
        {
            "name": "Ordem de Compra - PETR4",
            "message": "Preciso executar uma ordem de compra de 100 ações da PETR4 ao preço de mercado. Como devo proceder?",
            "provider": "openai"
        },
        {
            "name": "Ordem de Venda - VALE3",
            "message": "Quero vender 200 ações da VALE3 com limite de R$ 65,50. Qual é o procedimento?",
            "provider": "openai"
        },
        {
            "name": "Análise de Risco",
            "message": "Analise o risco de uma carteira com 60% em ações, 30% em FIIs e 10% em renda fixa. O que você recomenda?",
            "provider": "openai"
        },
        {
            "name": "Stop Loss",
            "message": "Como configurar um stop loss de 5% para uma posição em ITUB4? Explique o processo.",
            "provider": "openai"
        },
        {
            "name": "Horário de Negociação B3",
            "message": "Quais são os horários de funcionamento da B3 e quando posso executar ordens?",
            "provider": "openai"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n[{i}/{len(test_scenarios)}] Testando: {scenario['name']}")
        print(f"Provedor: {scenario['provider']}")
        print(f"Pergunta: {scenario['message'][:80]}...")
        
        # Preparar dados da requisição
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": scenario['message']
                }
            ],
            "provider": scenario['provider'],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        try:
            # Fazer requisição
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(API_URL, data=json_data, headers=HEADERS, method='POST')
            
            start_time = time.time()
            with urllib.request.urlopen(req, timeout=30) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    print(f"✅ Sucesso! (Tempo: {response_time:.2f}s)")
                    print(f"Resposta completa: {result.get('response', 'N/A')}")
                    
                    results.append({
                        "scenario": scenario['name'],
                        "provider": scenario['provider'],
                        "status": "success",
                        "response_time": response_time,
                        "response": result.get('response', '')
                    })
                else:
                    print(f"❌ Erro HTTP: {response.status}")
                    results.append({
                        "scenario": scenario['name'],
                        "provider": scenario['provider'],
                        "status": "http_error",
                        "error": f"HTTP {response.status}"
                    })
                    
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode('utf-8') if e.fp else str(e)
            print(f"❌ Erro HTTP: {e.code} - {error_msg[:100]}")
            results.append({
                "scenario": scenario['name'],
                "provider": scenario['provider'],
                "status": "http_error",
                "error": f"HTTP {e.code}: {error_msg[:100]}"
            })
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            results.append({
                "scenario": scenario['name'],
                "provider": scenario['provider'],
                "status": "error",
                "error": str(e)
            })
        
        # Pausa entre requisições
        if i < len(test_scenarios):
            time.sleep(1)
    
    # Resumo dos resultados
    print("\n" + "="*50)
    print("RESUMO DOS TESTES")
    print("="*50)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    total_count = len(results)
    
    print(f"Total de testes: {total_count}")
    print(f"Sucessos: {success_count}")
    print(f"Falhas: {total_count - success_count}")
    print(f"Taxa de sucesso: {(success_count/total_count)*100:.1f}%")
    
    if success_count > 0:
        avg_time = sum(r.get('response_time', 0) for r in results if r['status'] == 'success') / success_count
        print(f"Tempo médio de resposta: {avg_time:.2f}s")
    
    print("\nDetalhes por provedor:")
    providers = set(r['provider'] for r in results)
    for provider in providers:
        provider_results = [r for r in results if r['provider'] == provider]
        provider_success = sum(1 for r in provider_results if r['status'] == 'success')
        print(f"  {provider}: {provider_success}/{len(provider_results)} sucessos")
    
    print("\nTestes com falha:")
    for result in results:
        if result['status'] != 'success':
            print(f"  ❌ {result['scenario']} ({result['provider']}): {result.get('error', 'Erro desconhecido')}")
    
    return results

if __name__ == "__main__":
    try:
        results = test_homebroker_communication()
        print("\n🎯 Teste de comunicação homebroker concluído!")
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n💥 Erro fatal: {e}")