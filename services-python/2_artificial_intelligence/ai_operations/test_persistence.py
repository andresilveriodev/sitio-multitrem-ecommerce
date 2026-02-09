#!/usr/bin/env python3
"""
Teste de Persistência de Tráfego

Este arquivo testa se o sistema está persistindo corretamente:
- Transações de IA no banco de dados
- Métricas de uso
- Dados de conversas
- Tracking de usuários
"""

import requests
import json
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração
BASE_URL = "http://localhost:8012"
DATABASE_URI = os.getenv("DATABASE_URI", 'postgresql://postgres:123456@localhost:5434/sitio_multitrem')

def get_db_connection():
    """Conecta ao banco de dados"""
    try:
        conn = psycopg2.connect(DATABASE_URI)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None

def check_database_tables():
    """Verifica se as tabelas de tracking existem"""
    print("🔍 Verificando estrutura do banco de dados...")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verifica se o schema chatbot existe
            cur.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'chatbot'
            """)
            schema_exists = cur.fetchone()
            
            if not schema_exists:
                print("❌ Schema 'chatbot' não encontrado")
                return False
            
            print("✅ Schema 'chatbot' encontrado")
            
            # Verifica tabelas de tracking
            tables_to_check = ['transactions', 'usage_metrics', 'conversations', 'users']
            
            for table in tables_to_check:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'chatbot' AND table_name = %s
                """, (table,))
                
                table_exists = cur.fetchone()
                status = "✅" if table_exists else "❌"
                print(f"{status} Tabela 'chatbot.{table}': {'Existe' if table_exists else 'Não encontrada'}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        return False
    finally:
        conn.close()

def count_records_before():
    """Conta registros antes dos testes"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    counts = {}
    tables = ['transactions', 'usage_metrics', 'conversations', 'users']
    
    try:
        with conn.cursor() as cur:
            for table in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM chatbot.{table}")
                    count = cur.fetchone()[0]
                    counts[table] = count
                    print(f"📊 chatbot.{table}: {count} registros")
                except Exception as e:
                    print(f"⚠️ Erro ao contar {table}: {e}")
                    counts[table] = 0
    except Exception as e:
        print(f"❌ Erro ao contar registros: {e}")
    finally:
        conn.close()
    
    return counts

def send_test_requests():
    """Envia requisições de teste para gerar tráfego"""
    print("\n🚀 Enviando requisições de teste...")
    
    test_requests = [
        {
            "endpoint": "/ai/models",
            "method": "GET",
            "description": "Listar modelos de IA"
        },
        {
            "endpoint": "/chatbot/message",
            "method": "POST",
            "data": {
                "message": "Teste de persistência 1",
                "user_id": "test_user_persistence",
                "conversation_id": "test_conv_persistence"
            },
            "description": "Mensagem de chatbot 1"
        },
        {
            "endpoint": "/chatbot/message",
            "method": "POST",
            "data": {
                "message": "Teste de persistência 2",
                "user_id": "test_user_persistence",
                "conversation_id": "test_conv_persistence"
            },
            "description": "Mensagem de chatbot 2"
        },
        {
            "endpoint": "/analytics/usage-stats",
            "method": "GET",
            "description": "Consultar estatísticas"
        }
    ]
    
    successful_requests = 0
    
    for req in test_requests:
        try:
            if req["method"] == "GET":
                response = requests.get(f"{BASE_URL}{req['endpoint']}")
            else:
                response = requests.post(
                    f"{BASE_URL}{req['endpoint']}",
                    json=req.get("data", {}),
                    headers={"Content-Type": "application/json"}
                )
            
            status = "✅" if response.status_code in [200, 201, 404] else "❌"
            print(f"{status} {req['description']}: {response.status_code}")
            
            if response.status_code in [200, 201]:
                successful_requests += 1
            
            # Pequena pausa entre requisições
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ {req['description']}: Erro - {e}")
    
    print(f"\n📈 Requisições bem-sucedidas: {successful_requests}/{len(test_requests)}")
    return successful_requests

def count_records_after():
    """Conta registros após os testes"""
    print("\n📊 Verificando persistência após testes...")
    return count_records_before()

def check_specific_data():
    """Verifica dados específicos criados pelos testes"""
    print("\n🔍 Verificando dados específicos dos testes...")
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verifica usuário de teste
            cur.execute("""
                SELECT * FROM chatbot.users 
                WHERE user_id = 'test_user_persistence'
            """)
            user = cur.fetchone()
            
            if user:
                print(f"✅ Usuário de teste encontrado: {user['user_id']}")
                print(f"   📅 Criado em: {user.get('created_at', 'N/A')}")
            else:
                print("❌ Usuário de teste não encontrado")
            
            # Verifica conversas de teste
            cur.execute("""
                SELECT * FROM chatbot.conversations 
                WHERE conversation_id = 'test_conv_persistence'
            """)
            conversation = cur.fetchone()
            
            if conversation:
                print(f"✅ Conversa de teste encontrada: {conversation['conversation_id']}")
                print(f"   💬 Total de tokens: {conversation.get('total_tokens', 0)}")
                print(f"   💰 Custo total: ${conversation.get('total_cost', 0):.4f}")
            else:
                print("❌ Conversa de teste não encontrada")
            
            # Verifica transações recentes
            cur.execute("""
                SELECT COUNT(*) as count, 
                       AVG(response_time_ms) as avg_response_time,
                       SUM(total_tokens) as total_tokens,
                       SUM(cost) as total_cost
                FROM chatbot.transactions 
                WHERE created_at > NOW() - INTERVAL '5 minutes'
            """)
            stats = cur.fetchone()
            
            if stats and stats['count'] > 0:
                print(f"✅ Transações recentes: {stats['count']}")
                print(f"   ⏱️ Tempo médio de resposta: {stats['avg_response_time']:.2f}ms")
                print(f"   🎯 Total de tokens: {stats['total_tokens'] or 0}")
                print(f"   💰 Custo total: ${stats['total_cost'] or 0:.4f}")
            else:
                print("❌ Nenhuma transação recente encontrada")
                
    except Exception as e:
        print(f"❌ Erro ao verificar dados específicos: {e}")
    finally:
        conn.close()

def run_persistence_test():
    """Executa o teste completo de persistência"""
    print("🧪 TESTE DE PERSISTÊNCIA DE TRÁFEGO")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Verificar estrutura do banco
    if not check_database_tables():
        print("❌ Estrutura do banco não está correta. Execute as migrations primeiro.")
        return
    
    # 2. Contar registros antes
    print("\n📊 Contagem inicial de registros:")
    counts_before = count_records_before()
    
    # 3. Enviar requisições de teste
    successful_requests = send_test_requests()
    
    # 4. Aguardar um pouco para garantir persistência
    print("\n⏳ Aguardando persistência no banco...")
    time.sleep(2)
    
    # 5. Contar registros depois
    counts_after = count_records_after()
    
    # 6. Comparar contagens
    print("\n📈 Análise de persistência:")
    persistence_detected = False
    
    for table in counts_before.keys():
        before = counts_before.get(table, 0)
        after = counts_after.get(table, 0)
        diff = after - before
        
        if diff > 0:
            print(f"✅ {table}: +{diff} novos registros ({before} → {after})")
            persistence_detected = True
        elif diff == 0:
            print(f"⚠️ {table}: Nenhum novo registro ({before} → {after})")
        else:
            print(f"❌ {table}: Inconsistência detectada ({before} → {after})")
    
    # 7. Verificar dados específicos
    check_specific_data()
    
    # 8. Resultado final
    print("\n" + "=" * 60)
    if persistence_detected:
        print("✅ TESTE DE PERSISTÊNCIA: SUCESSO")
        print("   O sistema está persistindo dados corretamente no banco.")
    else:
        print("❌ TESTE DE PERSISTÊNCIA: FALHA")
        print("   O sistema não está persistindo dados no banco.")
        print("   Verifique:")
        print("   1. Se o middleware de tracking está ativo")
        print("   2. Se a conexão com o banco está funcionando")
        print("   3. Se as migrations foram executadas")
    
    print(f"\n📊 Resumo: {successful_requests} requisições enviadas")
    print("\n🔧 Para debug adicional, verifique os logs em /logs/")

if __name__ == "__main__":
    run_persistence_test()