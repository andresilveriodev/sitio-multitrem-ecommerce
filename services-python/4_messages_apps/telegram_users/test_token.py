"""Teste rápido do token"""
from config import settings

token = settings.TELEGRAM_BOT_TOKEN
if token and token != "your_telegram_bot_token_here":
    print(f"Token OK: {token[:15]}...")
else:
    print("Token NAO configurado")
