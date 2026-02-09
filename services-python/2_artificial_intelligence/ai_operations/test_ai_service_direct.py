import asyncio
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import ai_service

async def test_direct():
    print("=" * 80)
    print("TESTE DIRETO DO AI SERVICE")
    print("=" * 80)
    
    try:
        messages = [{"role": "user", "content": "teste simples"}]
        
        print("[*] Chamando ai_service.generate_response...")
        print(f"    Provider: openai")
        print(f"    Model: gpt-4o-mini")
        print(f"    Messages: {messages}")
        
        response = await ai_service.generate_response(
            messages=messages,
            provider="openai",
            model="gpt-4o-mini",
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"\n[OK] Resposta recebida: {response[:100] if response else 'VAZIA'}")
        print(f"    Tipo: {type(response)}")
        print(f"    Tamanho: {len(response) if response else 0}")
        
    except Exception as e:
        print(f"\n[ERRO] Erro ao chamar ai_service:")
        print(f"    Tipo: {type(e).__name__}")
        print(f"    Mensagem: {str(e)}")
        import traceback
        print(f"\nTraceback completo:")
        print(traceback.format_exc())
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_direct())
