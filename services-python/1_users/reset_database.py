#!/usr/bin/env python3
"""
Script para resetar o banco de dados - limpa todas as tabelas
"""

import structlog
from sqlalchemy import create_engine, text
from config import settings

logger = structlog.get_logger()

def reset_database():
    """Limpa todas as tabelas do banco de dados"""
    try:
        logger.info("🗑️ INICIANDO RESET DO BANCO DE DADOS")
        
        # Criar engine do banco
        engine = create_engine(
            settings.DATABASE_URI,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE
        )
        
        # Lista de tabelas para limpar (em ordem de dependência)
        tables = [
            "user_activities",
            "user_settings", 
            "user_preferences",
            "user_profiles_data",
            "profile_permissions",
            "user_profiles",
            "permissions",
            "profiles",
            "user_sessions",
            "audit_logs",
            "users"
        ]
        
        with engine.connect() as conn:
            # Desabilitar verificação de chaves estrangeiras temporariamente
            conn.execute(text("SET session_replication_role = replica;"))
            
            for table in tables:
                try:
                    logger.info(f"🧹 Limpando tabela: {table}")
                    conn.execute(text(f"DELETE FROM {table};"))
                    conn.commit()
                    logger.info(f"✅ Tabela {table} limpa com sucesso")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao limpar tabela {table}: {str(e)}")
                    # Continua com as próximas tabelas
            
            # Reabilitar verificação de chaves estrangeiras
            conn.execute(text("SET session_replication_role = DEFAULT;"))
            conn.commit()
        
        logger.info("🎉 RESET DO BANCO CONCLUÍDO COM SUCESSO!")
        logger.info("📊 Todas as tabelas foram limpas")
        
    except Exception as e:
        logger.error(f"❌ ERRO NO RESET DO BANCO: {str(e)}")
        raise

def verify_clean_database():
    """Verifica se o banco está limpo"""
    try:
        logger.info("🔍 VERIFICANDO SE O BANCO ESTÁ LIMPO")
        
        engine = create_engine(settings.DATABASE_URI)
        
        with engine.connect() as conn:
            # Verificar contagem de registros em cada tabela
            tables = [
                "users",
                "profiles", 
                "permissions",
                "user_profiles",
                "profile_permissions",
                "user_profiles_data",
                "user_preferences",
                "user_settings",
                "user_activities",
                "user_sessions",
                "audit_logs"
            ]
            
            total_records = 0
            
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    count = result.fetchone()[0]
                    logger.info(f"📊 {table}: {count} registros")
                    total_records += count
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao verificar tabela {table}: {str(e)}")
            
            if total_records == 0:
                logger.info("✅ BANCO VERIFICADO: Todas as tabelas estão vazias!")
                return True
            else:
                logger.warning(f"⚠️ BANCO VERIFICADO: Ainda existem {total_records} registros")
                return False
        
    except Exception as e:
        logger.error(f"❌ ERRO AO VERIFICAR BANCO: {str(e)}")
        return False

def main():
    """Função principal"""
    logger.info("🚀 INICIANDO PROCESSO DE RESET DO BANCO")
    logger.info("=" * 60)
    
    # Confirmar com o usuário
    print("\n⚠️  ATENÇÃO: Este script irá DELETAR TODOS os dados do banco!")
    print("   Todas as tabelas serão limpas completamente.")
    print("   Esta ação NÃO PODE ser desfeita!")
    
    response = input("\n🤔 Tem certeza que deseja continuar? (digite 'SIM' para confirmar): ")
    
    if response.upper() != "SIM":
        logger.info("❌ Operação cancelada pelo usuário")
        return
    
    try:
        # Reset do banco
        reset_database()
        
        # Verificar se foi limpo
        verify_clean_database()
        
        logger.info("=" * 60)
        logger.info("🎉 RESET DO BANCO CONCLUÍDO!")
        logger.info("📝 Próximos passos:")
        logger.info("   1. Execute: python init_db.py")
        logger.info("   2. Execute: python migrate_user_fields.py")
        logger.info("   3. Execute: python migrate_user_profile.py")
        logger.info("   4. Execute: python test_persistence.py")
        
    except Exception as e:
        logger.error(f"❌ ERRO NO PROCESSO: {str(e)}")
        raise

if __name__ == "__main__":
    main()

