"""Verificar se o .env está sendo lido corretamente"""
import os
from pathlib import Path

# Caminho do .env
env_path = Path(__file__).parent / ".env"

print(f"Verificando arquivo: {env_path}")
print(f"Arquivo existe: {env_path.exists()}")
print()

if env_path.exists():
    print("Conteudo do .env (apenas linhas com TELEGRAM):")
    with open(env_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if "TELEGRAM" in line.upper():
                # Mascarar o token para segurança
                if "=" in line:
                    key, value = line.split("=", 1)
                    value = value.strip()
                    if len(value) > 20:
                        masked = f"{value[:10]}...{value[-5:]}"
                    else:
                        masked = value
                    print(f"  Linha {i}: {key}={masked}")
                else:
                    print(f"  Linha {i}: {line.strip()}")

print()
print("Testando leitura com pydantic-settings:")
try:
    from config import settings
    token = settings.TELEGRAM_BOT_TOKEN
    if token and token != "your_telegram_bot_token_here":
        print(f"  Token lido: {token[:10]}...{token[-5:]}")
    else:
        print("  Token NAO foi lido ou esta como placeholder")
except Exception as e:
    print(f"  ERRO ao ler config: {e}")
