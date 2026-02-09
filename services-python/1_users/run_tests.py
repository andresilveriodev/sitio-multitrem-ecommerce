#!/usr/bin/env python3
"""
Script principal para executar todos os testes
"""

import asyncio
import sys
import structlog

logger = structlog.get_logger()

def run_persistence_tests():
    """Executa testes de persistência"""
    logger.info("🧪 EXECUTANDO TESTES DE PERSISTÊNCIA")
    
    try:
        from test_persistence import main as persistence_main
        persistence_main()
        logger.info("✅ Testes de persistência concluídos com sucesso!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro nos testes de persistência: {str(e)}")
        return False

async def run_api_tests():
    """Executa testes da API"""
    logger.info("🌐 EXECUTANDO TESTES DA API")
    
    try:
        from test_api_endpoints import main as api_main
        await api_main()
        logger.info("✅ Testes da API concluídos com sucesso!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro nos testes da API: {str(e)}")
        return False

def main():
    """Função principal"""
    logger.info("🚀 INICIANDO SUITE COMPLETA DE TESTES")
    logger.info("=" * 60)
    
    # Teste 1: Persistência
    persistence_success = run_persistence_tests()
    
    if not persistence_success:
        logger.error("❌ Testes de persistência falharam. Abortando.")
        sys.exit(1)
    
    # Teste 2: API
    api_success = asyncio.run(run_api_tests())
    
    if not api_success:
        logger.error("❌ Testes da API falharam.")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    logger.info("📁 Arquivos gerados:")
    logger.info("   - json_examples.json (exemplos de JSON)")
    logger.info("   - api_examples.json (exemplos de API)")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()

