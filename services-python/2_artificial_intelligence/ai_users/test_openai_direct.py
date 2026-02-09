#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste direto com a biblioteca OpenAI
Verifica se os modelos estão disponíveis
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("[ERRO] OPENAI_API_KEY nao encontrada")
    exit(1)

print("=" * 60)
print("TESTE DIRETO COM OPENAI")
print("=" * 60)
print(f"API Key: {api_key[:10]}...")
print()

client = OpenAI(api_key=api_key)

# Testa modelos
models_to_test = [
    ("gpt-4o-mini", 0.7),
    ("gpt-4.1-nano", 1.0),
]

for model_name, temp in models_to_test:
    print(f"\n{'='*60}")
    print(f"Testando: {model_name}")
    print(f"{'='*60}")
    
    try:
        # Para gpt-4.1-nano, usa max_completion_tokens
        if "gpt-4.1-nano" in model_name.lower() or "gpt-5" in model_name.lower():
            print(f"Usando max_completion_tokens e temperature=1.0")
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Responda apenas: OK"}],
                max_completion_tokens=50,
                temperature=1.0
            )
        else:
            print(f"Usando max_tokens e temperature={temp}")
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Responda apenas: OK"}],
                max_tokens=50,
                temperature=temp
            )
        
        content = response.choices[0].message.content
        print(f"[OK] SUCESSO!")
        print(f"Modelo: {response.model}")
        print(f"Resposta: {content}")
        print(f"Tokens usados: {response.usage.total_tokens if response.usage else 'N/A'}")
        
    except Exception as e:
        print(f"[ERRO] FALHOU")
        print(f"Tipo do erro: {type(e).__name__}")
        print(f"Mensagem: {str(e)}")
        
        # Se for erro da API, mostra mais detalhes
        if hasattr(e, 'response'):
            print(f"Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
            print(f"Body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")

print("\n" + "=" * 60)
print("TESTE CONCLUIDO")
print("=" * 60)





