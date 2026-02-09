"""
Script para verificar o status do serviço Telegram
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def verificar_servico():
    """Verifica o status do serviço"""
    print("=" * 60)
    print("VERIFICACAO DO SERVICO TELEGRAM")
    print("=" * 60)
    print()
    
    # 1. Verificar token
    # Tentar ler do .env diretamente
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    token = ""
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    
    # Se não encontrou no arquivo, tentar variável de ambiente
    if not token:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    print("1. Token do Telegram:")
    if not token or token == "your_telegram_bot_token_here":
        print("   [ERRO] Token nao configurado ou esta como placeholder")
        print("   Configure o token no arquivo .env")
        return
    else:
        print(f"   [OK] Token configurado: {token[:10]}...{token[-5:]}")
    
    print()
    
    # 2. Verificar se o serviço está rodando
    print("2. Status do servico:")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:8021/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   [OK] Servico rodando")
                print(f"   Status: {data.get('status')}")
                polling = data.get('polling', {})
                print(f"   Polling rodando: {polling.get('running', False)}")
                print(f"   Last update ID: {polling.get('last_update_id', 0)}")
            else:
                print(f"   [AVISO] Servico retornou status {response.status_code}")
    except httpx.ConnectError:
        print("   [ERRO] Servico nao esta rodando")
        print("   Execute: python main.py")
        return
    except Exception as e:
        print(f"   [ERRO] {e}")
        return
    
    print()
    
    # 3. Verificar token com Telegram API
    print("3. Validando token com Telegram API:")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data.get("result", {})
                    print(f"   [OK] Token valido")
                    print(f"   Bot: @{bot_info.get('username', 'N/A')}")
                    print(f"   Nome: {bot_info.get('first_name', 'N/A')}")
                else:
                    print(f"   [ERRO] Token invalido: {data.get('description', 'Erro desconhecido')}")
            else:
                print(f"   [ERRO] Erro HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   [ERRO] {e}")
    
    print()
    
    # 4. Testar getUpdates
    print("4. Testando getUpdates:")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            params = {"timeout": 5, "offset": 0}
            print("   Buscando atualizacoes (aguarde 5s)...")
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    updates = data.get("result", [])
                    print(f"   [OK] Recebidas {len(updates)} atualizacao(oes)")
                    if updates:
                        print("   [AVISO] Ha atualizacoes pendentes - o polling deve processa-las")
                    else:
                        print("   [INFO] Nenhuma atualizacao pendente")
                else:
                    print(f"   [ERRO] Erro: {data.get('description', 'Erro desconhecido')}")
            else:
                print(f"   [ERRO] Erro HTTP {response.status_code}")
    except httpx.TimeoutException:
        print("   [AVISO] Timeout (normal se nao houver atualizacoes)")
    except Exception as e:
        print(f"   [ERRO] {e}")
    
    print()
    print("=" * 60)
    print("RECOMENDACOES:")
    print("=" * 60)
    print("1. Se o token nao esta configurado, edite o arquivo .env")
    print("2. Se o servico nao esta rodando, execute: python main.py")
    print("3. Envie uma mensagem para o bot e verifique os logs")
    print("4. Verifique se o polling esta rodando: curl http://localhost:8021/health")

if __name__ == "__main__":
    asyncio.run(verificar_servico())
