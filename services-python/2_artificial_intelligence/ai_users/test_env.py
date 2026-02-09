#!/usr/bin/env python3
"""
Script para testar a leitura das credenciais do arquivo .env
"""
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente do .env
load_dotenv()

print("=" * 60)
print("VERIFICAÇÃO DAS CREDENCIAIS DO ARQUIVO .env")
print("=" * 60)

# Server Configuration
ai_port = os.getenv("AI_SERVICE_PORT", "NÃO ENCONTRADO")
cors_origins = os.getenv("CORS_ORIGINS", "NÃO ENCONTRADO")
print(f"\n[Server Configuration]")
print(f"   AI_SERVICE_PORT: {ai_port}")
print(f"   CORS_ORIGINS: {cors_origins}")

# Database Configuration
db_uri = os.getenv("DATABASE_URI", "NÃO ENCONTRADO")
if db_uri != "NÃO ENCONTRADO":
    # Mascarar senha na exibição
    db_uri_masked = db_uri.split("@")[0].split(":")[0] + ":***@" + "@".join(db_uri.split("@")[1:]) if "@" in db_uri else db_uri
    print(f"\n[Database Configuration]")
    print(f"   DATABASE_URI: {db_uri_masked}")
else:
    print(f"\n[Database Configuration]")
    print(f"   DATABASE_URI: {db_uri}")

# OpenAI Configuration
openai_key = os.getenv("OPENAI_API_KEY", "NÃO ENCONTRADO")
openai_model = os.getenv("OPENAI_MODEL", "NÃO ENCONTRADO")
print(f"\n[OpenAI Configuration]")
if openai_key != "NÃO ENCONTRADO":
    print(f"   OPENAI_API_KEY: {openai_key[:20]}...{openai_key[-10:] if len(openai_key) > 30 else ''} [OK]")
else:
    print(f"   OPENAI_API_KEY: {openai_key} [FALTANDO]")
print(f"   OPENAI_MODEL: {openai_model}")

# DeepSeek Configuration
deepseek_key = os.getenv("DEEPSEEK_API_KEY", "NÃO ENCONTRADO")
deepseek_base = os.getenv("DEEPSEEK_BASE_URL", "NÃO ENCONTRADO")
deepseek_model = os.getenv("DEEPSEEK_MODEL", "NÃO ENCONTRADO")
print(f"\n[DeepSeek Configuration]")
if deepseek_key != "NÃO ENCONTRADO":
    print(f"   DEEPSEEK_API_KEY: {deepseek_key[:20]}...{deepseek_key[-10:] if len(deepseek_key) > 30 else ''} [OK]")
else:
    print(f"   DEEPSEEK_API_KEY: {deepseek_key} [FALTANDO]")
print(f"   DEEPSEEK_BASE_URL: {deepseek_base}")
print(f"   DEEPSEEK_MODEL: {deepseek_model}")

# Gemini Configuration
gemini_key = os.getenv("GEMINI_API_KEY", "NÃO ENCONTRADO")
gemini_model = os.getenv("GEMINI_MODEL", "NÃO ENCONTRADO")
print(f"\n[Gemini Configuration]")
if gemini_key != "NÃO ENCONTRADO":
    print(f"   GEMINI_API_KEY: {gemini_key[:20]}...{gemini_key[-10:] if len(gemini_key) > 30 else ''} [OK]")
else:
    print(f"   GEMINI_API_KEY: {gemini_key} [FALTANDO]")
print(f"   GEMINI_MODEL: {gemini_model}")

# Ollama Configuration
ollama_base = os.getenv("OLLAMA_BASE_URL", "NÃO ENCONTRADO")
ollama_model = os.getenv("OLLAMA_MODEL", "NÃO ENCONTRADO")
print(f"\n[Ollama Configuration]")
print(f"   OLLAMA_BASE_URL: {ollama_base}")
print(f"   OLLAMA_MODEL: {ollama_model}")

# AI Provider Configuration
default_provider = os.getenv("DEFAULT_AI_PROVIDER", "NÃO ENCONTRADO")
print(f"\n[AI Provider Configuration]")
print(f"   DEFAULT_AI_PROVIDER: {default_provider}")

print("\n" + "=" * 60)
print("RESUMO:")
print("=" * 60)

# Verificar se as credenciais essenciais estão configuradas
essential_vars = {
    "AI_SERVICE_PORT": ai_port,
    "DATABASE_URI": db_uri,
    "OPENAI_API_KEY": openai_key,
    "DEFAULT_AI_PROVIDER": default_provider
}

all_ok = True
for var_name, var_value in essential_vars.items():
    if var_value == "NÃO ENCONTRADO":
        print(f"[X] {var_name}: FALTANDO")
        all_ok = False
    else:
        print(f"[OK] {var_name}: Configurado")

if all_ok:
    print("\n[SUCESSO] Todas as credenciais essenciais estao configuradas!")
else:
    print("\n[AVISO] Algumas credenciais essenciais estao faltando!")

print("=" * 60)
