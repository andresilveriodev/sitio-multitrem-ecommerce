#!/usr/bin/env python3
"""
Script para testar se o config.py consegue ler as credenciais do .env
"""
import sys
sys.path.insert(0, '.')

from app.config import (
    HTTP_PORT, 
    OPENAI_API_KEY, 
    OPENAI_MODEL, 
    DATABASE_URI, 
    DEFAULT_AI_PROVIDER,
    DEEPSEEK_API_KEY,
    CORS_ORIGINS
)

print("=" * 60)
print("TESTE DE LEITURA VIA app.config")
print("=" * 60)

print(f"\n[Server Configuration]")
print(f"   HTTP_PORT: {HTTP_PORT}")

print(f"\n[CORS Configuration]")
print(f"   CORS_ORIGINS: {CORS_ORIGINS}")

print(f"\n[Database Configuration]")
if DATABASE_URI:
    db_masked = DATABASE_URI.split("@")[0].split(":")[0] + ":***@" + "@".join(DATABASE_URI.split("@")[1:]) if "@" in DATABASE_URI else DATABASE_URI
    print(f"   DATABASE_URI: {db_masked} [OK]")
else:
    print(f"   DATABASE_URI: None [ERRO]")

print(f"\n[OpenAI Configuration]")
if OPENAI_API_KEY:
    print(f"   OPENAI_API_KEY: {OPENAI_API_KEY[:20]}...{OPENAI_API_KEY[-10:]} [OK]")
    print(f"   OPENAI_MODEL: {OPENAI_MODEL} [OK]")
else:
    print(f"   OPENAI_API_KEY: None [ERRO]")
    print(f"   OPENAI_MODEL: {OPENAI_MODEL}")

print(f"\n[DeepSeek Configuration]")
if DEEPSEEK_API_KEY:
    print(f"   DEEPSEEK_API_KEY: {DEEPSEEK_API_KEY[:20]}...{DEEPSEEK_API_KEY[-10:]} [OK]")
else:
    print(f"   DEEPSEEK_API_KEY: None [Nao configurado]")

print(f"\n[AI Provider Configuration]")
print(f"   DEFAULT_AI_PROVIDER: {DEFAULT_AI_PROVIDER}")

print("\n" + "=" * 60)
print("RESUMO:")
print("=" * 60)

all_ok = True
if not OPENAI_API_KEY:
    print("[X] OPENAI_API_KEY nao foi carregada")
    all_ok = False
else:
    print("[OK] OPENAI_API_KEY carregada corretamente")

if not DATABASE_URI:
    print("[X] DATABASE_URI nao foi carregada")
    all_ok = False
else:
    print("[OK] DATABASE_URI carregada corretamente")

if HTTP_PORT != 8003:
    print(f"[AVISO] HTTP_PORT esta como {HTTP_PORT}, esperado 8003")
else:
    print(f"[OK] HTTP_PORT configurado corretamente: {HTTP_PORT}")

if all_ok:
    print("\n[SUCESSO] Todas as configuracoes essenciais foram carregadas!")
    print("O arquivo .env esta sendo lido corretamente pelo config.py")
else:
    print("\n[ERRO] Algumas configuracoes nao foram carregadas corretamente")

print("=" * 60)
