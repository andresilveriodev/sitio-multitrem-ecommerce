#!/usr/bin/env python3
import psycopg2
from psycopg2 import sql

def check_pricing_tables():
    try:
        # Conectar ao banco
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5434/sitio_multitrem')
        cur = conn.cursor()
        
        print("💰 Verificando tabelas de preços e cobrança...")
        print("=" * 60)
        
        # Tabelas de preços no schema security
        pricing_tables = [
            'ai_models', 'ai_subscriptions', 'user_subscriptions', 
            'user_ai_settings', 'ai_usage_alerts'
        ]
        
        for table in pricing_tables:
            print(f"\n🔍 Estrutura da tabela 'security.{table}':")
            print("-" * 50)
            
            cur.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'security' AND table_name = '{table}'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            for col in columns:
                print(f"  • {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # Verificar dados
            cur.execute(f"SELECT COUNT(*) FROM security.{table}")
            count = cur.fetchone()[0]
            print(f"  📊 Total de registros: {count}")
            
            if count > 0:
                # Mostrar alguns registros
                cur.execute(f"SELECT * FROM security.{table} LIMIT 3")
                rows = cur.fetchall()
                print(f"  📋 Exemplos de dados:")
                for i, row in enumerate(rows, 1):
                    print(f"    {i}. {row}")
        
        print("\n" + "=" * 60)
        print("📊 RESUMO DAS TABELAS DE PREÇOS:")
        print()
        print("1. 🔧 ai_models - Preços por token dos modelos de IA")
        print("   • cost_per_1k_tokens: Custo por 1000 tokens")
        print("   • is_paid: Se o modelo é pago")
        print()
        print("2. 💳 ai_subscriptions - Planos de assinatura disponíveis")
        print("   • price: Preço do plano")
        print("   • billing_cycle: Ciclo de cobrança (mensal/anual)")
        print("   • limits: Limites do plano")
        print()
        print("3. 👤 user_subscriptions - Assinaturas ativas dos usuários")
        print("   • status: Status da assinatura")
        print("   • current_usage: Uso atual")
        print("   • usage_limits: Limites do usuário")
        print()
        print("4. ⚙️ user_ai_settings - Configurações de IA do usuário")
        print("   • default_model: Modelo padrão")
        print("   • auto_fallback: Fallback automático")
        print()
        print("5. 🚨 ai_usage_alerts - Alertas de uso e limites")
        print("   • alert_type: Tipo de alerta")
        print("   • threshold: Limite para alerta")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas de preços: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_pricing_tables()
