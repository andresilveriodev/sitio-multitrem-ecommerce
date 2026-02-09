#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste direto do serviço simples
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

async def test_service_simple():
    """Testa o serviço simples diretamente"""
    print("=" * 60)
    print("TESTE DIRETO DO SERVICO SIMPLES")
    print("=" * 60)
    
    try:
        from services.ai_service_simple import ai_service_simple
        
        print("[*] Enviando mensagem para gpt-4.1-nano...")
        result = await ai_service_simple.send(
            user_message="Olá! Você está funcionando?",
            model="gpt-4.1-nano",
            max_tokens=50,
            temperature=0.7
        )
        
        print(f"[OK] SUCESSO!")
        print(f"Resposta: {result}")
        return True
        
    except Exception as e:
        print(f"[ERRO] FALHOU")
        print(f"Tipo: {type(e).__name__}")
        print(f"Erro: {str(e)}")
        import traceback
        print(f"\nTraceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_service_simple())
    sys.exit(0 if result else 1)





