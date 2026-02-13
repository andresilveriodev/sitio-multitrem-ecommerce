#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do modelo GPT-4.1-nano para operações de homebroker
Este arquivo testa a funcionalidade do modelo gpt-4.1-nano
com cenários específicos de homebroker da B3.
"""

import requests
import json
import time

# Configuração da API
API_BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def test_gpt41nano_model(message, max_tokens=200, temperature=0.7):
    """
    Testa o modelo gpt-4.1-nano com uma mensagem específica
    """
    data = {
        "message": message,
        "provider": "openai",
        "model": "gpt-4.1-nano",
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/ai/generate", json=data, headers=HEADERS)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "provider": result.get('provider'),
                "model": result.get('model'),
                "total_tokens": result.get('total_tokens'),
                "response": result.get('response', 'Resposta vazia'),
                "response_length": len(str(result.get('response', '')))
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro na requisição: {e}"
        }

def print_test_result(test_name, result):
    """
    Imprime o resultado de um teste de forma formatada
    """
    print(f"\n{'='*60}")
    print(f"TESTE: {test_name}")
    print(f"{'='*60}")
    
    if result["success"]:
        print(f"✅ Status: SUCESSO")
        print(f"📊 Provider: {result['provider']}")
        print(f"🤖 Model: {result['model']}")
        print(f"🔢 Total Tokens: {result['total_tokens']}")
        print(f"📏 Response Length: {result['response_length']} caracteres")
        print(f"\n💬 Resposta:")
        print(f"{'-'*40}")
        print(result['response'])
        print(f"{'-'*40}")
    else:
        print(f"❌ Status: ERRO")
        print(f"🚨 Erro: {result['error']}")

def main():
    """
    Executa todos os testes do modelo gpt-4.1-nano
    """
    print("🚀 INICIANDO TESTES DO MODELO GPT-4.1-NANO")
    print("📈 Cenários de Homebroker B3")
    print(f"🕐 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Cenários de teste
    test_scenarios = [
        {
            "name": "Ordem de Compra PETR4",
            "message": "Analise a seguinte operação de homebroker: Compra de 100 ações PETR4 a R$ 35,50. Forneça análise de risco e recomendações."
        },
        {
            "name": "Ordem de Venda VALE3",
            "message": "Operação: Venda de 200 ações VALE3 a R$ 68,20. Avalie se é um bom momento para esta operação."
        },
        {
            "name": "Stop Loss ITUB4",
            "message": "Configure um stop loss para ITUB4: preço atual R$ 32,15, stop loss em R$ 29,50. Calcule o risco da operação."
        },
        {
            "name": "Análise de Carteira",
            "message": "Analise esta carteira: 50% PETR4, 30% VALE3, 20% ITUB4. Sugira rebalanceamento considerando diversificação de risco."
        },
        {
            "name": "Horário de Negociação",
            "message": "É 15:45 de uma sexta-feira. Devo executar uma ordem de compra de BBAS3 agora ou aguardar? Considere liquidez e volatilidade."
        }
    ]
    
    # Executar testes
    results = []
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔄 Executando teste {i}/{len(test_scenarios)}: {scenario['name']}")
        
        result = test_gpt41nano_model(
            message=scenario['message'],
            max_tokens=250,
            temperature=0.7
        )
        
        results.append({
            "scenario": scenario['name'],
            "result": result
        })
        
        print_test_result(scenario['name'], result)
        
        # Pequena pausa entre testes
        time.sleep(1)
    
    # Resumo final
    print(f"\n\n{'='*60}")
    print("📊 RESUMO DOS TESTES")
    print(f"{'='*60}")
    
    successful_tests = sum(1 for r in results if r['result']['success'])
    total_tests = len(results)
    
    print(f"✅ Testes bem-sucedidos: {successful_tests}/{total_tests}")
    print(f"❌ Testes com erro: {total_tests - successful_tests}/{total_tests}")
    print(f"📈 Taxa de sucesso: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests > 0:
        total_tokens = sum(r['result'].get('total_tokens', 0) for r in results if r['result']['success'])
        avg_response_length = sum(r['result'].get('response_length', 0) for r in results if r['result']['success']) / successful_tests
        
        print(f"🔢 Total de tokens utilizados: {total_tokens}")
        print(f"📏 Tamanho médio das respostas: {avg_response_length:.1f} caracteres")
    
    print(f"\n🏁 Testes concluídos em {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()