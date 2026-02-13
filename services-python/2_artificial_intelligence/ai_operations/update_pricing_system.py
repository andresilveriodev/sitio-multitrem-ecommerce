#!/usr/bin/env python3
import psycopg2
import json
from psycopg2 import sql

def update_pricing_system():
    try:
        # Conectar ao banco
        conn = psycopg2.connect('postgresql://postgres:123456@localhost:5434/b3_trader')
        cur = conn.cursor()
        
        print("🔄 Atualizando sistema de preços para 2 tipos de venda...")
        print("=" * 60)
        
        # 1. Atualizar tabela ai_subscriptions para ter apenas 2 planos
        print("\n📝 Atualizando planos de assinatura...")
        
        # Limpar planos existentes
        cur.execute("DELETE FROM security.ai_subscriptions")
        print("✅ Planos antigos removidos")
        
        # Inserir apenas 2 planos: por tokens e ilimitado
        plans = [
            {
                'plan_id': 'pay_per_token',
                'name': 'Pague por Token',
                'price': 0.0,
                'currency': 'BRL',
                'billing_cycle': 'monthly',
                'is_active': True,
                'features': ['chat', 'analysis', 'coding'],
                'limits': {
                    'type': 'pay_per_token',
                    'description': 'Pague apenas pelos tokens que usar'
                }
            },
            {
                'plan_id': 'unlimited',
                'name': 'Ilimitado',
                'price': 99.90,
                'currency': 'BRL',
                'billing_cycle': 'monthly',
                'is_active': True,
                'features': ['chat', 'analysis', 'coding', 'advanced_features'],
                'limits': {
                    'type': 'unlimited',
                    'description': 'Uso ilimitado de tokens'
                }
            }
        ]
        
        for plan in plans:
            cur.execute("""
                INSERT INTO security.ai_subscriptions 
                (plan_id, name, price, currency, billing_cycle, is_active, features, limits)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                plan['plan_id'],
                plan['name'],
                plan['price'],
                plan['currency'],
                plan['billing_cycle'],
                plan['is_active'],
                json.dumps(plan['features']),
                json.dumps(plan['limits'])
            ))
        
        print("✅ Novos planos inseridos:")
        print("   • Pague por Token: R$ 0,00 (paga por token usado)")
        print("   • Ilimitado: R$ 99,90/mês (uso ilimitado)")
        
        # 2. Verificar preços dos modelos por token
        print("\n🔍 Verificando preços por token dos modelos...")
        cur.execute("""
            SELECT model_id, name, cost_per_1k_tokens, is_paid 
            FROM security.ai_models 
            ORDER BY cost_per_1k_tokens
        """)
        
        models = cur.fetchall()
        print("📋 Preços por 1000 tokens:")
        for model in models:
            model_id, name, cost, is_paid = model
            status = "💰 Pago" if is_paid else "🆓 Gratuito"
            print(f"   • {name} ({model_id}): R$ {cost:.6f} - {status}")
        
        # 3. Mostrar resumo do sistema
        print("\n" + "=" * 60)
        print("🎯 SISTEMA DE VENDA SIMPLIFICADO:")
        print()
        print("📈 VENDA POR TOKENS:")
        print("   • Plano: Pague por Token")
        print("   • Preço: R$ 0,00/mês + tokens consumidos")
        print("   • Exemplo: 10.000 tokens GPT-4o = R$ 1,50")
        print()
        print("♾️ VENDA ILIMITADA:")
        print("   • Plano: Ilimitado")
        print("   • Preço: R$ 99,90/mês")
        print("   • Uso: Ilimitado de tokens")
        print()
        print("💰 PREÇOS POR 1000 TOKENS:")
        for model in models:
            model_id, name, cost, is_paid = model
            if is_paid:
                print(f"   • {name}: R$ {cost:.6f}")
        
        # Commit das alterações
        conn.commit()
        print("\n✅ Sistema de preços atualizado com sucesso!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao atualizar sistema: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    update_pricing_system()
