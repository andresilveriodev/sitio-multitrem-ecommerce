#!/usr/bin/env python3
"""
Script para inicializar o Chatbot Service em modo desenvolvimento
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [CHATBOT] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Função principal"""
    logger.info("Iniciando B3-Trader Chatbot Service...")
    
    # Verifica se o arquivo .env existe
    env_file = Path(".env")
    if not env_file.exists():
        logger.warning("Arquivo .env nao encontrado!")
        logger.info("Copiando env.example para .env...")
        try:
            with open("env.example", "r", encoding="utf-8") as f:
                env_content = f.read()
            with open(".env", "w", encoding="utf-8") as f:
                f.write(env_content)
            logger.info("Arquivo .env criado com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao criar .env: {e}", exc_info=True)
            return 1
    
    # Configurações para desenvolvimento
    config = {
        "host": "0.0.0.0",
        "port": 8011,
        "reload": True,
        "log_level": "info",
        "access_log": True
    }
    
    logger.info(f"Servidor iniciando em http://{config['host']}:{config['port']}")
    logger.info("Documentacao disponivel em: http://localhost:8011/docs")
    logger.info("Health check: http://localhost:8011/health")
    logger.info("Pressione Ctrl+C para parar")
    
    try:
        uvicorn.run("main:app", **config)
    except KeyboardInterrupt:
        logger.info("Chatbot Service finalizado!")
        return 0
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())


