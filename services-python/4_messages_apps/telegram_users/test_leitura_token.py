"""Teste completo de leitura do token"""
import sys
import os

print("=" * 60)
print("TESTE DE LEITURA DO TOKEN")
print("=" * 60)
print()

# 1. Verificar arquivo .env
print("1. Verificando arquivo .env:")
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    print(f"   [OK] Arquivo existe: {env_path}")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("TELEGRAM_BOT_TOKEN="):
                token_value = line.split("=", 1)[1].strip()
                if token_value and token_value != "your_telegram_bot_token_here":
                    print(f"   [OK] Token no arquivo: {token_value[:15]}...")
                else:
                    print("   [ERRO] Token ainda como placeholder")
                break
else:
    print(f"   [ERRO] Arquivo nao existe: {env_path}")
    sys.exit(1)

print()

# 2. Testar pydantic-settings
print("2. Testando pydantic-settings:")
try:
    from config import settings
    token = settings.TELEGRAM_BOT_TOKEN
    if token and token != "your_telegram_bot_token_here":
        print(f"   [OK] Token lido pelo settings: {token[:15]}...")
    else:
        print("   [ERRO] Token nao foi lido ou esta como placeholder")
        sys.exit(1)
except Exception as e:
    print(f"   [ERRO] Erro ao importar settings: {e}")
    sys.exit(1)

print()

# 3. Testar TelegramService
print("3. Testando TelegramService:")
try:
    from services.telegram_service import TelegramService
    ts = TelegramService()
    print(f"   [OK] TelegramService criado com sucesso")
    print(f"   [OK] Token no servico: {ts.bot_token[:15]}...")
    print(f"   [OK] Base URL: {ts.base_url[:40]}...")
except ValueError as e:
    print(f"   [ERRO] Valor invalido: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   [ERRO] Erro ao criar TelegramService: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("TUDO OK! O token esta sendo lido corretamente.")
print("=" * 60)
