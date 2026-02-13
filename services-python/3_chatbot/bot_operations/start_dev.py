#!/usr/bin/env python3
"""
Script para inicializar o Chatbot Service em modo desenvolvimento
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Função principal"""
    print("🤖 Iniciando B3-Trader Chatbot Service...")
    
    # Verifica se o arquivo .env existe
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Arquivo .env não encontrado!")
        print("📝 Copiando env.example para .env...")
        try:
            with open("env.example", "r") as f:
                env_content = f.read()
            with open(".env", "w") as f:
                f.write(env_content)
            print("✅ Arquivo .env criado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar .env: {e}")
            return 1
    
    # Configurações para desenvolvimento
    config = {
        "host": "0.0.0.0",
        "port": 8011,
        "reload": True,
        "log_level": "info",
        "access_log": True
    }
    
    print(f"🚀 Servidor iniciando em http://{config['host']}:{config['port']}")
    print("📚 Documentação disponível em: http://localhost:8011/docs")
    print("🔍 Health check: http://localhost:8011/health")
    print("⏹️  Pressione Ctrl+C para parar")
    
    try:
        uvicorn.run("main:app", **config)
    except KeyboardInterrupt:
        print("\n👋 Chatbot Service finalizado!")
        return 0
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())


