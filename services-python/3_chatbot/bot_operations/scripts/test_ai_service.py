#!/usr/bin/env python3
"""
Script para testar a comunicação do AI Service Operations (bot_operations) com o AI Service (Chatbot Middleware).
Usa config.AI_SERVICE_URL e o mesmo contrato que ai_integration (POST /ai/chat).
Execute: python scripts/test_ai_service.py
"""

import os
import sys

# Garante que o projeto está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from config import settings


def test_health() -> bool:
    """Testa GET /health do AI Service."""
    url = f"{settings.AI_SERVICE_URL.rstrip('/')}/health"
    print(f"\n1. Health check: GET {url}")
    try:
        r = httpx.get(url, timeout=5)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   Body: {r.text[:200] if r.text else '(vazio)'}")
            return True
        print(f"   Body: {r.text[:300]}")
        return False
    except Exception as e:
        print(f"   Erro: {type(e).__name__}: {e}")
        return False


def test_chat() -> bool:
    """Testa POST /ai/chat com mensagem simples (igual ao operations)."""
    url = f"{settings.AI_SERVICE_URL.rstrip('/')}/ai/chat"
    payload = {"message": "Oi"}
    print(f"\n2. Chat: POST {url}")
    print(f"   Payload: {payload}")
    try:
        r = httpx.post(url, json=payload, timeout=settings.AI_SERVICE_TIMEOUT)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            reply = data.get("reply", data.get("response", ""))
            print(f"   Reply: {reply[:500] if reply else '(vazio)'}")
            return bool(reply and reply.strip())
        print(f"   Body: {r.text[:400]}")
        return False
    except Exception as e:
        print(f"   Erro: {type(e).__name__}: {e}")
        return False


def main():
    print("=" * 60)
    print("Teste: AI Service Operations -> AI Service (Chatbot Middleware)")
    print(f"AI_SERVICE_URL = {settings.AI_SERVICE_URL}")
    print("=" * 60)

    ok_health = test_health()
    ok_chat = test_chat()

    print("\n" + "=" * 60)
    if ok_health and ok_chat:
        print("Resultado: OK — Health e Chat responderam corretamente.")
    elif ok_health and not ok_chat:
        print("Resultado: Parcial — Health OK, Chat falhou ou retornou vazio.")
    else:
        print("Resultado: Falha — AI Service inacessível (verifique URL e se o serviço está rodando).")
    print("=" * 60)
    return 0 if (ok_health and ok_chat) else 1


if __name__ == "__main__":
    sys.exit(main())
