#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inicializar o Chatbot Service em modo desenvolvimento
"""

import os
import sys
import uvicorn
from pathlib import Path

# Configurar encoding UTF-8 para Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    """Função principal"""
    try:
        print("Iniciando E-commerce Chatbot Service...")
    except UnicodeEncodeError:
        print("[CHATBOT] Iniciando E-commerce Chatbot Service...")
    
    # Verifica se o arquivo .env existe
    env_file = Path(".env")
    if not env_file.exists():
        print("Arquivo .env nao encontrado!")
        print("Copiando env.example para .env...")
        try:
            with open("env.example", "r", encoding="utf-8") as f:
                env_content = f.read()
            with open(".env", "w", encoding="utf-8") as f:
                f.write(env_content)
            print("Arquivo .env criado com sucesso!")
        except Exception as e:
            print(f"Erro ao criar .env: {e}")
            return 1
    
    # Configurações para desenvolvimento
    config = {
        "host": "0.0.0.0",
        "port": 8002,
        "reload": True,
        "log_level": "info",
        "access_log": True
    }
    
    print(f"Servidor iniciando em http://{config['host']}:{config['port']}")
    print("Documentacao disponivel em: http://localhost:8002/docs")
    print("Health check: http://localhost:8002/health")
    print("Pressione Ctrl+C para parar")
    
    try:
        uvicorn.run("main:app", **config)
    except KeyboardInterrupt:
        print("\nChatbot Service finalizado!")
        return 0
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())


