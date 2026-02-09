#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do GPT-4.1-nano através do Chatbot Service
"""

import httpx
import json
import sys

# Configuração
CHATBOT_BASE_URL = "http://localhost:8012"  # Mesma aplicação, prefixo /chatbot
USER_ID = 1
USERNAME = "test_user"

def test_chatbot_gpt41nano():
    """
    Testa o GPT-4.1-nano através do Chatbot Service
    """
    print("=" * 60)
    print("TESTE GPT-4.1-nano VIA CHATBOT SERVICE")
    print("=" * 60)
    print(f"URL: {CHATBOT_BASE_URL}")
    print()
    
    with httpx.Client(timeout=60.0) as client:
        # Passo 1: Criar uma conversa
        print("[*] Passo 1: Criando conversa...")
        try:
            create_response = client.post(
                f"{CHATBOT_BASE_URL}/chatbot/conversations",
                json={
                    "user_id": USER_ID,
                    "username": USERNAME,
                    "title": "Teste GPT-4.1-nano"
                }
            )
            
            if create_response.status_code != 200:
                print(f"[ERRO] Falha ao criar conversa: {create_response.status_code}")
                print(f"Resposta: {create_response.text}")
                return False
            
            conversation_data = create_response.json()
            conversation_id = conversation_data.get("id")
            print(f"[OK] Conversa criada: ID {conversation_id}")
            print()
            
        except Exception as e:
            print(f"[ERRO] Erro ao criar conversa: {e}")
            return False
        
        # Passo 2: Enviar mensagem com GPT-4.1-nano
        print("[*] Passo 2: Enviando mensagem com GPT-4.1-nano...")
        print(f"Mensagem: 'Olá! Você está funcionando com GPT-4.1-nano?'")
        print(f"Provider: openai")
        print(f"Model: gpt-4.1-nano")
        print()
        
        try:
            chat_response = client.post(
                f"{CHATBOT_BASE_URL}/chatbot/chat",
                json={
                    "conversation_id": conversation_id,
                    "message": "Olá! Você está funcionando com GPT-4.1-nano?",
                    "provider": "openai",
                    "model": "gpt-4.1-nano"
                }
            )
            
            print(f"[*] Status Code: {chat_response.status_code}")
            print()
            
            if chat_response.status_code == 200:
                result = chat_response.json()
                print("[OK] SUCESSO!")
                print("-" * 60)
                print(f"Conversa ID: {result.get('conversation_id')}")
                print(f"Mensagem do usuário: {result.get('user_message')}")
                print()
                print("Resposta da IA:")
                print("-" * 60)
                print(result.get('ai_response', 'Resposta vazia'))
                print("-" * 60)
                print()
                print("[OK] GPT-4.1-nano está FUNCIONANDO via Chatbot Service!")
                return True
            else:
                print(f"[ERRO] Falha na requisição: {chat_response.status_code}")
                print(f"Resposta: {chat_response.text}")
                
                try:
                    error_detail = chat_response.json()
                    print(f"Detalhes: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
                except:
                    pass
                
                return False
                
        except httpx.ConnectError:
            print(f"[ERRO] Não foi possível conectar ao Chatbot Service em {CHATBOT_BASE_URL}")
            print("Verifique se a aplicação está rodando!")
            return False
        except httpx.TimeoutException:
            print(f"[ERRO] Timeout na requisição (mais de 60 segundos)")
            return False
        except Exception as e:
            print(f"[ERRO] Erro inesperado: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_chatbot_gpt41nano()
    sys.exit(0 if success else 1)





