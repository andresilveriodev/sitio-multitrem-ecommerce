#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para verificar se o servidor está rodando
"""

import requests
import time

def test_server():
    """Testa se o servidor está rodando"""
    
    print("🔍 TESTANDO SE O SERVIDOR ESTÁ RODANDO")
    print("=" * 50)
    
    # Testa diferentes portas
    ports = [8012, 5000, 8000, 8080]
    
    for port in ports:
        try:
            print(f"\n📡 Testando porta {port}...")
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Servidor rodando na porta {port}!")
                print(f"   Resposta: {response.json()}")
                return port
            else:
                print(f"❌ Porta {port} respondeu com status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Porta {port} não está respondendo")
        except requests.exceptions.Timeout:
            print(f"❌ Timeout na porta {port}")
        except Exception as e:
            print(f"❌ Erro ao testar porta {port}: {e}")
    
    print("\n❌ Nenhuma porta respondeu. Servidor pode não estar rodando.")
    return None

if __name__ == "__main__":
    test_server()
