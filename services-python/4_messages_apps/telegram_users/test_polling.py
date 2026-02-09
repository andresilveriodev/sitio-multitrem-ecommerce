"""
Script para testar o polling do Telegram manualmente
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

async def test_get_updates():
    """Testa getUpdates diretamente"""
    if not TELEGRAM_BOT_TOKEN:
        print("ERRO: TELEGRAM_BOT_TOKEN nao configurado no .env")
        return
    
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    print("=" * 60)
    print("TESTE DE GETUPDATES DO TELEGRAM")
    print("=" * 60)
    print()
    
    async with httpx.AsyncClient() as client:
        # Testar getMe primeiro
        print("1. Testando token do bot...")
        try:
            response = await client.get(f"{base_url}/getMe", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data.get("result", {})
                    print(f"   OK - Bot: @{bot_info.get('username', 'N/A')}")
                else:
                    print(f"   ERRO: {data.get('description', 'Token invalido')}")
                    return
            else:
                print(f"   ERRO - Status {response.status_code}")
                return
        except Exception as e:
            print(f"   ERRO: {e}")
            return
        
        print()
        
        # Testar getUpdates
        print("2. Buscando atualizacoes (getUpdates)...")
        try:
            url = f"{base_url}/getUpdates"
            params = {
                "timeout": 5,
                "offset": 0  # Buscar todas as atualizações pendentes
            }
            
            print(f"   URL: {url}")
            print(f"   Aguardando atualizacoes (timeout: 5s)...")
            
            response = await client.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    updates = data.get("result", [])
                    print(f"   OK - Recebidas {len(updates)} atualizacao(oes)")
                    
                    if updates:
                        print()
                        print("   Atualizacoes encontradas:")
                        for update in updates:
                            update_id = update.get("update_id")
                            message = update.get("message")
                            if message:
                                text = message.get("text", "")
                                from_user = message.get("from", {})
                                print(f"   - Update ID: {update_id}")
                                print(f"     Usuario: {from_user.get('first_name', 'N/A')} (@{from_user.get('username', 'N/A')})")
                                print(f"     Mensagem: {text}")
                                print()
                    else:
                        print("   Nenhuma atualizacao pendente")
                        print("   Envie uma mensagem para o bot e execute novamente")
                else:
                    print(f"   ERRO: {data.get('description', 'Erro desconhecido')}")
            else:
                print(f"   ERRO - Status {response.status_code}")
                print(f"   Resposta: {response.text}")
        except httpx.TimeoutException:
            print("   Timeout (normal se nao houver atualizacoes)")
        except Exception as e:
            print(f"   ERRO: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_get_updates())
