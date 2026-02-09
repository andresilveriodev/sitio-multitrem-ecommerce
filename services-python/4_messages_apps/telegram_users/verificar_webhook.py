"""
Script para verificar e configurar o webhook do Telegram
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_SERVICE_URL = "http://localhost:8021"

def print_header(text):
    print("=" * 60)
    print(text)
    print("=" * 60)
    print()

def verificar_token():
    """Verifica se o token do bot está configurado e válido"""
    print("1. Verificando token do bot...")
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        print("   ERRO - Token nao configurado no .env")
        print("   Configure TELEGRAM_BOT_TOKEN no arquivo .env")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                print(f"   OK - Token valido")
                print(f"   Bot: @{bot_info.get('username', 'N/A')}")
                print(f"   Nome: {bot_info.get('first_name', 'N/A')}")
                return True
            else:
                print(f"   ERRO - Token invalido: {data.get('description', 'Erro desconhecido')}")
                return False
        else:
            print(f"   ERRO - Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"   ERRO - Nao foi possivel verificar token: {e}")
        return False

def verificar_servico():
    """Verifica se o serviço está rodando"""
    print("\n2. Verificando se o servico esta rodando...")
    
    try:
        response = requests.get(f"{TELEGRAM_SERVICE_URL}/", timeout=5)
        if response.status_code == 200:
            print("   OK - Servico rodando na porta 8021")
            return True
        else:
            print(f"   ERRO - Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERRO - Servico nao esta rodando: {e}")
        print("   Inicie o servico com: python main.py")
        return False

def obter_info_webhook():
    """Obtém informações sobre o webhook configurado"""
    print("\n3. Verificando webhook configurado...")
    
    if not TELEGRAM_BOT_TOKEN:
        print("   ERRO - Token nao configurado")
        return None
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                webhook_info = data.get("result", {})
                webhook_url = webhook_info.get("url", "")
                pending = webhook_info.get("pending_update_count", 0)
                last_error = webhook_info.get("last_error_message", "")
                
                print(f"   URL configurada: {webhook_url if webhook_url else 'NENHUMA'}")
                print(f"   Updates pendentes: {pending}")
                
                if last_error:
                    print(f"   ERRO: {last_error}")
                    print(f"   Data do erro: {webhook_info.get('last_error_date', 'N/A')}")
                
                if not webhook_url:
                    print("\n   ATENCAO - Webhook nao esta configurado!")
                    print("   O Telegram nao conseguira enviar mensagens.")
                    return None
                
                return webhook_info
            else:
                print(f"   ERRO: {data.get('description', 'Erro desconhecido')}")
                return None
        else:
            print(f"   ERRO - Status {response.status_code}")
            return None
    except Exception as e:
        print(f"   ERRO - Nao foi possivel obter informacoes: {e}")
        return None

def configurar_webhook(webhook_url):
    """Configura o webhook do Telegram"""
    print(f"\n4. Configurando webhook para: {webhook_url}")
    
    if not TELEGRAM_BOT_TOKEN:
        print("   ERRO - Token nao configurado")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
        payload = {"url": webhook_url}
        
        # Adicionar secret token se configurado
        secret_token = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
        if secret_token and secret_token != "your_secret_token_here":
            payload["secret_token"] = secret_token
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("   OK - Webhook configurado com sucesso!")
                print(f"   Descricao: {data.get('description', 'N/A')}")
                return True
            else:
                print(f"   ERRO: {data.get('description', 'Erro desconhecido')}")
                return False
        else:
            print(f"   ERRO - Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"   ERRO - Nao foi possivel configurar webhook: {e}")
        return False

def remover_webhook():
    """Remove o webhook configurado"""
    print("\n5. Removendo webhook...")
    
    if not TELEGRAM_BOT_TOKEN:
        print("   ERRO - Token nao configurado")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
        response = requests.post(url, json={"drop_pending_updates": True}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("   OK - Webhook removido")
                return True
            else:
                print(f"   ERRO: {data.get('description', 'Erro desconhecido')}")
                return False
        else:
            print(f"   ERRO - Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ERRO - Nao foi possivel remover webhook: {e}")
        return False

def main():
    print_header("VERIFICACAO E CONFIGURACAO DO WEBHOOK TELEGRAM")
    
    # Verificar token
    if not verificar_token():
        print("\nERRO: Token nao configurado ou invalido")
        print("Configure TELEGRAM_BOT_TOKEN no arquivo .env")
        sys.exit(1)
    
    # Verificar serviço
    if not verificar_servico():
        print("\nERRO: Servico nao esta rodando")
        print("Inicie o servico com: python main.py")
        sys.exit(1)
    
    # Obter informações do webhook
    webhook_info = obter_info_webhook()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTICO")
    print("=" * 60)
    
    if not webhook_info or not webhook_info.get("url"):
        print("\nPROBLEMA ENCONTRADO: Webhook nao esta configurado!")
        print("\nPara receber mensagens do Telegram, voce precisa:")
        print("1. Expor o servico publicamente (usar ngrok para desenvolvimento)")
        print("2. Configurar o webhook com a URL publica")
        print("\nExemplo com ngrok:")
        print("  ngrok http 8021")
        print("  # Depois use a URL do ngrok para configurar o webhook")
        print("\nOu configure manualmente:")
        webhook_url = input("\nDigite a URL do webhook (ou Enter para pular): ").strip()
        if webhook_url:
            if not webhook_url.startswith("https://"):
                print("ERRO: URL deve comecar com https://")
            else:
                if not webhook_url.endswith("/telegram/webhook"):
                    webhook_url = webhook_url.rstrip("/") + "/telegram/webhook"
                configurar_webhook(webhook_url)
    else:
        webhook_url = webhook_info.get("url", "")
        print(f"\nWebhook configurado: {webhook_url}")
        
        if webhook_info.get("pending_update_count", 0) > 0:
            print(f"\nATENCAO: Ha {webhook_info.get('pending_update_count')} updates pendentes")
            print("Isso pode indicar que o webhook nao esta funcionando corretamente")
        
        if webhook_info.get("last_error_message"):
            print(f"\nERRO no webhook: {webhook_info.get('last_error_message')}")
            print("Verifique se o servico esta acessivel publicamente")
        
        # Verificar se a URL aponta para localhost (não funcionará)
        if "localhost" in webhook_url or "127.0.0.1" in webhook_url:
            print("\nPROBLEMA: Webhook aponta para localhost!")
            print("O Telegram nao consegue acessar localhost.")
            print("Use ngrok ou uma URL publica.")
    
    print("\n" + "=" * 60)
    print("TESTE MANUAL")
    print("=" * 60)
    print("\nPara testar se o webhook esta funcionando:")
    print("1. Envie uma mensagem para o bot no Telegram")
    print("2. Verifique os logs do servico")
    print("3. Se nao aparecer 'Webhook recebido', o problema e na configuracao do webhook")
    print("\nPara verificar updates pendentes:")
    print(f"  https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates")

if __name__ == "__main__":
    main()
