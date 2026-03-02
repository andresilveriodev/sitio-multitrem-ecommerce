"""
Teste de persistência de pedidos no e-commerce service
Testa criação real de pedidos via endpoint bulk
"""

import asyncio
import sys
import json
from services.telegram_order_parser import telegram_order_parser
from services.commerce_client import commerce_client
from config import settings
import structlog

logger = structlog.get_logger(__name__)


async def test_order_persistence():
    """Testa persistência real de pedido no e-commerce service"""
    print("=" * 70)
    print("TESTE DE PERSISTÊNCIA DE PEDIDOS")
    print("=" * 70)
    print()
    
    # Verificar configuração
    print(f"[*] E-commerce Service URL: {settings.COMMERCE_SERVICE_URL}")
    print(f"[*] Timeout: {settings.COMMERCE_SERVICE_TIMEOUT}s")
    print()
    
    # Token opcional - pode ser fornecido via variável de ambiente ou argumento
    token = None
    if len(sys.argv) > 1 and sys.argv[1] != "--simple":
        token = sys.argv[1]
        print(f"[*] Token fornecido: {token[:20]}...")
    else:
        print("[AVISO] Nenhum token fornecido. Testando sem autenticacao.")
        print("       Para fornecer token: python test_order_persistence.py <token>")
    print()
    
    # Texto de teste
    test_text = "Dona Dilma: 08 Couve 04 Coentros 04 Cebolinhas"
    
    print("=" * 70)
    print("ETAPA 1: Parsing do Pedido")
    print("=" * 70)
    print(f"Texto: {test_text}")
    print()
    
    # Parsear pedidos
    orders = telegram_order_parser.parse_order_text(test_text)
    
    if not orders:
        print("[ERRO] Nenhum pedido foi parseado do texto!")
        return False
    
    print(f"[OK] Pedidos parseados: {len(orders)}")
    for i, order in enumerate(orders, 1):
        print(f"\n  Pedido {i}:")
        print(f"    Contato: {order.get('contact_name', 'N/A')}")
        print(f"    Estabelecimento: {order.get('establishment_name', 'N/A')}")
        print(f"    Itens: {len(order.get('items', []))}")
        for item in order.get('items', []):
            print(f"      - {item.get('qty')}x {item.get('product_name')} (product_id: {item.get('product_id', 'N/A')})")
    print()
    
    # Buscar produtos
    print("=" * 70)
    print("ETAPA 2: Busca de Produtos no E-commerce Service")
    print("=" * 70)
    print()
    
    products_found = 0
    products_not_found = []
    
    for order in orders:
        for item in order.get('items', []):
            product_name = item.get('product_name')
            if not product_name:
                continue
            
            print(f"[*] Buscando produto: {product_name}")
            try:
                product = await telegram_order_parser.search_product(product_name, token=token)
                if product:
                    item['product_id'] = product.get('id')
                    print(f"    [OK] Encontrado: ID={product.get('id')}, Nome={product.get('name')}, SKU={product.get('sku', 'N/A')}")
                    products_found += 1
                else:
                    item['product_id'] = None
                    print(f"    [AVISO] Nao encontrado (sera enviado com product_id=null)")
                    products_not_found.append(product_name)
            except Exception as e:
                item['product_id'] = None
                print(f"    [ERRO] Erro ao buscar: {e}")
                products_not_found.append(product_name)
            print()
    
    print(f"[*] Resumo da busca:")
    print(f"    [OK] Produtos encontrados: {products_found}")
    print(f"    [AVISO] Produtos nao encontrados: {len(products_not_found)}")
    if products_not_found:
        print(f"     {', '.join(products_not_found)}")
    print()
    
    # Preparar dados para envio
    print("=" * 70)
    print("ETAPA 3: Preparação dos Dados para Envio")
    print("=" * 70)
    print()
    
    import uuid
    conversation_id = f"test_{uuid.uuid4()}"
    
    bulk_data = {
        "conversation_id": conversation_id,
        "orders": orders
    }
    
    print(f"[*] Dados preparados:")
    print(f"  Conversation ID: {conversation_id}")
    print(f"  Total de pedidos: {len(orders)}")
    print()
    print("[*] JSON que sera enviado:")
    print(json.dumps(bulk_data, indent=2, ensure_ascii=False))
    print()
    
    # Enviar pedidos
    print("=" * 70)
    print("ETAPA 4: Envio para E-commerce Service")
    print("=" * 70)
    print()
    
    try:
        print(f"[*] Enviando pedidos para: {settings.COMMERCE_SERVICE_URL}/v1/chatbot/orders/bulk")
        print()
        
        created_orders = await commerce_client.create_orders_bulk(bulk_data, token=token)
        
        if not created_orders:
            print("[ERRO] Nenhum pedido foi criado!")
            print("       Verifique se os produtos foram identificados corretamente.")
            return False
        
        print(f"[OK] SUCESSO! Pedidos criados: {len(created_orders)}")
        print()
        
        # Mostrar detalhes dos pedidos criados
        print("=" * 70)
        print("ETAPA 5: Detalhes dos Pedidos Criados")
        print("=" * 70)
        print()
        
        for i, order in enumerate(created_orders, 1):
            print(f"[PEDIDO {i}]")
            print(f"  ID: {order.get('id')}")
            print(f"  Número: {order.get('order_number', 'N/A')}")
            print(f"  Status: {order.get('status', 'N/A')}")
            print(f"  Cliente ID: {order.get('customer_id', 'N/A')}")
            print(f"  Subtotal: R$ {order.get('subtotal', 0):.2f}")
            print(f"  Taxa de entrega: R$ {order.get('delivery_fee', 0):.2f}")
            print(f"  Total: R$ {order.get('total', 0):.2f}")
            
            items = order.get('items', [])
            if items:
                print(f"  Itens ({len(items)}):")
                for item in items:
                    product_name = item.get('product_name', 'N/A')
                    product_id = item.get('product_id', 'N/A')
                    qty = item.get('qty', 0)
                    price = item.get('price', 0)
                    print(f"    - {qty}x {product_name} (ID: {product_id}) - R$ {price:.2f}")
            print()
        
        print("=" * 70)
        print("[OK] TESTE DE PERSISTENCIA CONCLUIDO COM SUCESSO!")
        print("=" * 70)
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERRO] Erro ao criar pedidos: {e}")
        print()
        import traceback
        print("Detalhes do erro:")
        traceback.print_exc()
        print()
        return False


async def test_simple_order():
    """Testa criação de pedido simples (mínimo necessário)"""
    print("=" * 70)
    print("TESTE SIMPLES: Pedido Mínimo")
    print("=" * 70)
    print()
    
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
    
    # Pedido mínimo conforme guia
    bulk_data = {
        "orders": [
            {
                "items": [
                    {
                        "product_id": None,  # Será null se não encontrar
                        "product_name": "Couve",
                        "qty": 8
                    }
                ]
            }
        ]
    }
    
    print("📦 Dados do pedido mínimo:")
    print(json.dumps(bulk_data, indent=2, ensure_ascii=False))
    print()
    
    try:
        print(f"[*] Enviando pedido minimo...")
        created_orders = await commerce_client.create_orders_bulk(bulk_data, token=token)
        
        if created_orders:
            print(f"[OK] Pedido criado com sucesso!")
            print(f"     ID: {created_orders[0].get('id')}")
            print(f"     Status: {created_orders[0].get('status')}")
            return True
        else:
            print("[ERRO] Nenhum pedido foi criado")
            return False
            
    except Exception as e:
        print(f"[ERRO] Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Executa testes de persistência"""
    print("\n" + "=" * 70)
    print("TESTES DE PERSISTÊNCIA DE PEDIDOS")
    print("=" * 70)
    print()
    
    # Verificar se e-commerce service está acessível
    print("[*] Verificando conectividade com e-commerce service...")
    try:
        # Tentar buscar produtos (endpoint simples)
        products = await commerce_client.search_products("test", token=None)
        print(f"[OK] E-commerce service esta acessivel")
        print(f"     URL: {settings.COMMERCE_SERVICE_URL}")
        print()
    except Exception as e:
        print(f"[AVISO] Nao foi possivel conectar ao e-commerce service: {e}")
        print(f"        URL: {settings.COMMERCE_SERVICE_URL}")
        print()
        print("[DICA] Certifique-se de que o e-commerce service esta rodando")
        print()
        return
    
    # Executar testes
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        # Teste simples
        success = await test_simple_order()
    else:
        # Teste completo
        success = await test_order_persistence()
    
    if success:
        print("\n[OK] Todos os testes passaram!")
    else:
        print("\n[AVISO] Alguns testes falharam. Verifique os logs acima.")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
