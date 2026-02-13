#!/usr/bin/env python3
import psycopg2
import json

def check_system_data():
    try:
        # Conectar ao banco
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5434/b3_trader')
        cur = conn.cursor()
        
        print("🔍 Verificando dados básicos do sistema...")
        print("=" * 60)
        
        # 1. Verificar tabelas essenciais
        essential_tables = [
            ('security.ai_models', 'Modelos de IA'),
            ('security.ai_subscriptions', 'Planos de assinatura'),
            ('public.conversations', 'Conversas'),
            ('public.messages', 'Mensagens'),
            ('security.transactions', 'Transações'),
            ('security.usage', 'Uso')
        ]
        
        print("📋 VERIFICAÇÃO DE TABELAS ESSENCIAIS:")
        print("-" * 50)
        
        all_tables_exist = True
        for table, description in essential_tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                status = "✅" if count >= 0 else "❌"
                print(f"{status} {table} ({description}): {count} registros")
            except Exception as e:
                print(f"❌ {table} ({description}): ERRO - {e}")
                all_tables_exist = False
        
        print("\n" + "=" * 60)
        print("📊 DADOS BÁSICOS CONFIGURADOS:")
        print("-" * 50)
        
        # 2. Verificar modelos de IA
        print("\n🤖 MODELOS DE IA:")
        cur.execute("SELECT model_id, name, provider, cost_per_1k_tokens, is_paid FROM security.ai_models ORDER BY cost_per_1k_tokens")
        models = cur.fetchall()
        for model in models:
            model_id, name, provider, cost, is_paid = model
            status = "💰" if is_paid else "🆓"
            print(f"  {status} {name} ({model_id}) - {provider}: R$ {cost:.6f}")
        
        # 3. Verificar planos de assinatura
        print("\n💳 PLANOS DE ASSINATURA:")
        cur.execute("SELECT plan_id, name, price, currency FROM security.ai_subscriptions WHERE is_active = true")
        plans = cur.fetchall()
        for plan in plans:
            plan_id, name, price, currency = plan
            print(f"  📋 {name} ({plan_id}): {currency} {price:.2f}/mês")
        
        # 4. Verificar se há conversas de exemplo
        print("\n🗣️ CONVERSAS:")
        cur.execute("SELECT COUNT(*) FROM public.conversations")
        conv_count = cur.fetchone()[0]
        print(f"  📝 Total de conversas: {conv_count}")
        
        if conv_count > 0:
            cur.execute("SELECT id, user_id, title, status, created_at FROM public.conversations ORDER BY created_at DESC LIMIT 3")
            conversations = cur.fetchall()
            for conv in conversations:
                conv_id, user_id, title, status, created = conv
                print(f"    • {title} (ID: {conv_id}, User: {user_id}, Status: {status})")
        
        # 5. Verificar transações
        print("\n💰 TRANSAÇÕES:")
        cur.execute("SELECT COUNT(*) FROM security.transactions")
        tx_count = cur.fetchone()[0]
        print(f"  💳 Total de transações: {tx_count}")
        
        if tx_count > 0:
            cur.execute("SELECT id, user_id, provider, model, total_cost, status FROM security.transactions ORDER BY created_at DESC LIMIT 3")
            transactions = cur.fetchall()
            for tx in transactions:
                tx_id, user_id, provider, model, cost, status = tx
                print(f"    • {provider}/{model}: R$ {cost:.4f} (User: {user_id}, Status: {status})")
        
        # 6. Verificar uso
        print("\n📈 USO:")
        cur.execute("SELECT COUNT(*) FROM security.usage")
        usage_count = cur.fetchone()[0]
        print(f"  📊 Total de registros de uso: {usage_count}")
        
        # 7. Resumo do status
        print("\n" + "=" * 60)
        print("🎯 STATUS DO SISTEMA:")
        print("-" * 50)
        
        if all_tables_exist and len(models) > 0 and len(plans) > 0:
            print("✅ SISTEMA PRONTO PARA USO!")
            print("   • Todas as tabelas essenciais existem")
            print(f"   • {len(models)} modelos de IA configurados")
            print(f"   • {len(plans)} planos de assinatura ativos")
            print(f"   • {conv_count} conversas no sistema")
            print(f"   • {tx_count} transações registradas")
        else:
            print("⚠️ SISTEMA INCOMPLETO!")
            if not all_tables_exist:
                print("   • Algumas tabelas essenciais estão faltando")
            if len(models) == 0:
                print("   • Nenhum modelo de IA configurado")
            if len(plans) == 0:
                print("   • Nenhum plano de assinatura configurado")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar dados: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_system_data()
