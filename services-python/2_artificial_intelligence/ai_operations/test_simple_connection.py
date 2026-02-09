#!/usr/bin/env python3
"""
Teste simples de conexão e inserção de dados
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import time
from sqlalchemy import text
from app.db import engine

def test_server_connection():
    """Testa se o servidor está respondendo"""
    try:
        response = requests.get("http://localhost:8012/health", timeout=5)
        print(f"✅ Servidor respondendo: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Servidor não está respondendo: {e}")
        return False

def test_database_direct():
    """Testa inserção direta no banco"""
    try:
        with engine.connect() as conn:
            # Inserir um usuário de teste
            conn.execute(text("""
                INSERT INTO chatbot.users (username, email, full_name) 
                VALUES ('test_user', 'test@example.com', 'Test User')
                ON CONFLICT (username) DO NOTHING
            """))
            
            # Inserir uma transação de teste
            conn.execute(text("""
                INSERT INTO chatbot.transactions 
                (user_id, model_name, provider, request_tokens, response_tokens, total_tokens, cost, status)
                SELECT u.id, 'gpt-4', 'openai', 100, 50, 150, 0.01, 'completed'
                FROM chatbot.users u 
                WHERE u.username = 'test_user'
            """))
            
            conn.commit()
            
            # Verificar dados inseridos
            result = conn.execute(text("SELECT COUNT(*) FROM chatbot.users WHERE username = 'test_user'"))
            user_count = result.fetchone()[0]
            
            result = conn.execute(text("SELECT COUNT(*) FROM chatbot.transactions"))
            transaction_count = result.fetchone()[0]
            
            print(f"✅ Dados inseridos - Usuários: {user_count}, Transações: {transaction_count}")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao inserir dados: {e}")
        return False

def test_api_endpoint():
    """Testa endpoint da API"""
    try:
        # Testar endpoint de modelos
        response = requests.get("http://localhost:8012/ai/models", timeout=5)
        print(f"✅ Endpoint /ai/models: {response.status_code}")
        
        # Testar endpoint de health
        response = requests.get("http://localhost:8012/health", timeout=5)
        print(f"✅ Endpoint /health: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar endpoints: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 TESTE SIMPLES DE CONEXÃO")
    print("=" * 40)
    
    # Teste 1: Servidor
    server_ok = test_server_connection()
    
    # Teste 2: Banco direto
    db_ok = test_database_direct()
    
    # Teste 3: API
    api_ok = test_api_endpoint()
    
    print("\n" + "=" * 40)
    print("📊 RESUMO:")
    print(f"Servidor: {'✅' if server_ok else '❌'}")
    print(f"Banco: {'✅' if db_ok else '❌'}")
    print(f"API: {'✅' if api_ok else '❌'}")
    
    if all([server_ok, db_ok, api_ok]):
        print("\n🎉 Todos os testes passaram!")
        return 0
    else:
        print("\n⚠️ Alguns testes falharam.")
        return 1

if __name__ == "__main__":
    exit(main())