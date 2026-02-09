import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.routers.ai_resource import AIResponse

print("=" * 80)
print("TESTE DE VALIDACAO DO AIResponse")
print("=" * 80)

# Teste 1: Criar AIResponse com dados válidos
try:
    result = AIResponse(
        response="Teste de resposta",
        provider="openai",
        model="gpt-4o-mini",
        usage={"total_tokens": 10}
    )
    print("[OK] AIResponse criado com sucesso")
    print(f"    Response: {result.response}")
    print(f"    Provider: {result.provider}")
    print(f"    Model: {result.model}")
    print(f"    Usage: {result.usage}")
except Exception as e:
    print(f"[ERRO] Erro ao criar AIResponse: {e}")
    import traceback
    print(traceback.format_exc())

# Teste 2: Com model vazio
print("\n" + "-" * 80)
try:
    result = AIResponse(
        response="Teste",
        provider="openai",
        model="",  # String vazia
        usage={}
    )
    print("[OK] AIResponse criado com model vazio")
except Exception as e:
    print(f"[ERRO] Erro com model vazio: {e}")

# Teste 3: Com model None (deve falhar)
print("\n" + "-" * 80)
try:
    result = AIResponse(
        response="Teste",
        provider="openai",
        model=None,  # None
        usage={}
    )
    print("[OK] AIResponse criado com model None")
except Exception as e:
    print(f"[ERRO] Erro com model None (esperado): {e}")

print("=" * 80)





