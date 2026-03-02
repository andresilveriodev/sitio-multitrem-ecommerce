"""
Script de teste para processamento de pedidos do Telegram
Testa parsing e comunicação com e-commerce service
"""

import asyncio
import sys
from services.telegram_order_parser import telegram_order_parser


async def test_parsing():
    """Testa o parsing de pedidos"""
    print("=" * 60)
    print("TESTE 1: Parsing de Pedidos")
    print("=" * 60)
    
    test_cases = [
        "Dona Dilma: 08 Couve 04 Coentros 04 Cebolinhas",
        "Dona Dilma: 08 Couve 04 Coentros 04 Cebolinhas 01 palito alface roxa 01 palito alface crespa verde 02 rúcula",
        "Senhor João: 10 Couve 05 Coentros",
        "Dilma: 08 Couve 04 Coentros",
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n--- Teste {i} ---")
        print(f"Texto: {test_text}")
        
        orders = telegram_order_parser.parse_order_text(test_text)
        
        print(f"Pedidos encontrados: {len(orders)}")
        for j, order in enumerate(orders, 1):
            print(f"\n  Pedido {j}:")
            print(f"    Contato: {order.get('contact_name', 'N/A')}")
            print(f"    Itens: {len(order.get('items', []))}")
            for item in order.get('items', []):
                print(f"      - {item.get('qty')}x {item.get('product_name')}")
        
        print()


async def test_remove_pronouns():
    """Testa remoção de pronomes"""
    print("=" * 60)
    print("TESTE 2: Remoção de Pronomes")
    print("=" * 60)
    
    test_cases = [
        "Dona Dilma",
        "Don João",
        "Senhor Pedro",
        "Senhora Maria",
        "Sr. José",
        "Sra. Ana",
        "Sr João",
        "Sra Maria",
    ]
    
    for name in test_cases:
        cleaned = telegram_order_parser.remove_pronouns(name)
        print(f"  '{name}' -> '{cleaned}'")
    
    print()


async def test_product_search():
    """Testa busca de produtos (requer e-commerce service rodando)"""
    print("=" * 60)
    print("TESTE 3: Busca de Produtos")
    print("=" * 60)
    print("\n⚠️  Este teste requer:")
    print("  - E-commerce service rodando em http://localhost:8002")
    print("  - Token Keycloak válido (opcional)")
    print()
    
    # Token opcional - pode ser None para testar sem autenticação
    token = None  # Substitua por um token válido se necessário
    
    test_products = ["Couve", "Coentro", "Cebolinha", "Alface"]
    
    for product_name in test_products:
        print(f"\nBuscando: {product_name}")
        try:
            product = await telegram_order_parser.search_product(product_name, token=token)
            if product:
                print(f"  ✅ Encontrado: ID={product.get('id')}, Nome={product.get('name')}")
            else:
                print(f"  ❌ Não encontrado")
        except Exception as e:
            print(f"  ⚠️  Erro: {e}")
    
    print()


async def test_full_order_processing():
    """Testa processamento completo de pedido (requer e-commerce service)"""
    print("=" * 60)
    print("TESTE 4: Processamento Completo de Pedido")
    print("=" * 60)
    print("\n⚠️  Este teste requer:")
    print("  - E-commerce service rodando em http://localhost:8002")
    print("  - Token Keycloak válido (opcional)")
    print("  - Produtos cadastrados no e-commerce")
    print()
    
    # Token opcional
    token = None  # Substitua por um token válido se necessário
    
    test_text = "Dona Dilma: 08 Couve 04 Coentros 04 Cebolinhas"
    
    print(f"Texto do pedido: {test_text}\n")
    
    # Parsear pedidos
    orders = telegram_order_parser.parse_order_text(test_text)
    print(f"Pedidos parseados: {len(orders)}")
    
    if orders:
        # Processar pedidos
        try:
            conversation_id = "test_conversation_123"
            success, message, created_orders = await telegram_order_parser.process_orders(
                orders,
                conversation_id=conversation_id,
                token=token
            )
            
            print(f"\nResultado: {'✅ Sucesso' if success else '❌ Erro'}")
            print(f"Mensagem: {message}")
            
            if created_orders:
                print(f"\nPedidos criados: {len(created_orders)}")
                for i, order in enumerate(created_orders, 1):
                    print(f"  Pedido {i}: ID={order.get('id')}, Status={order.get('status')}")
        except Exception as e:
            print(f"\n❌ Erro ao processar pedidos: {e}")
            import traceback
            traceback.print_exc()
    
    print()


async def main():
    """Executa todos os testes"""
    print("\n" + "=" * 60)
    print("TESTES DE PROCESSAMENTO DE PEDIDOS DO TELEGRAM")
    print("=" * 60 + "\n")
    
    # Testes que não requerem e-commerce service
    await test_parsing()
    await test_remove_pronouns()
    
    # Testes que requerem e-commerce service (comentados por padrão)
    # Descomente para testar com e-commerce service rodando
    if len(sys.argv) > 1 and sys.argv[1] == "--with-ecommerce":
        await test_product_search()
        await test_full_order_processing()
    else:
        print("\n" + "=" * 60)
        print("Para testar comunicação com e-commerce service:")
        print("  python test_order_processing.py --with-ecommerce")
        print("=" * 60 + "\n")
    
    print("\n[OK] Testes concluidos!\n")


if __name__ == "__main__":
    asyncio.run(main())
