"""
Script rápido para testar o sistema de pedidos
Execute: python test_orders_quick.py
"""

import asyncio
import httpx
from datetime import datetime


BASE_URL = "http://localhost:8002"


async def test_create_order():
    """Testa criação de pedido"""
    print("\n=== Teste 1: Criar Pedido ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/orders/create",
            json={
                "user_id": "test_user_123",
                "items": [
                    {
                        "product_id": "prod_001",
                        "product_name": "Tomate",
                        "quantity": 2,
                        "unit_price": 15.50,
                        "total_price": 31.00
                    },
                    {
                        "product_id": "prod_002",
                        "product_name": "Cebola",
                        "quantity": 1,
                        "unit_price": 8.00,
                        "total_price": 8.00
                    }
                ],
                "delivery_address": {
                    "street": "Rua Exemplo",
                    "number": "123",
                    "neighborhood": "Centro",
                    "city": "São Paulo",
                    "state": "SP",
                    "zip_code": "01234-567"
                },
                "payment_method": "pix",
                "notes": "Entregar de manhã"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            order = data.get("order", {})
            print(f"✅ Pedido criado: {order.get('order_number')}")
            print(f"   ID: {order.get('id')}")
            print(f"   Total: R$ {order.get('total_amount', 0):.2f}")
            print(f"   Status: {order.get('status')}")
            return order.get("id")
        else:
            print(f"❌ Erro: {response.status_code}")
            print(response.text)
            return None


async def test_get_order(order_id: str):
    """Testa busca de pedido"""
    print("\n=== Teste 2: Buscar Pedido ===")
    
    if not order_id:
        print("⚠️  Pulando teste (pedido não criado)")
        return
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/orders/{order_id}")
        
        if response.status_code == 200:
            data = response.json()
            order = data.get("order", {})
            print(f"✅ Pedido encontrado: {order.get('order_number')}")
            print(f"   Status: {order.get('status')}")
            print(f"   Itens: {len(order.get('items', []))}")
        else:
            print(f"❌ Erro: {response.status_code}")
            print(response.text)


async def test_list_orders():
    """Testa listagem de pedidos"""
    print("\n=== Teste 3: Listar Pedidos ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/orders/user/test_user_123")
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get("orders", [])
            print(f"✅ Encontrados {len(orders)} pedido(s)")
            for order in orders[:3]:  # Mostra apenas os 3 primeiros
                print(f"   - {order.get('order_number')}: {order.get('status')}")
        else:
            print(f"❌ Erro: {response.status_code}")
            print(response.text)


async def test_advance_stage(order_id: str):
    """Testa avanço de etapa"""
    print("\n=== Teste 4: Avançar Etapa ===")
    
    if not order_id:
        print("⚠️  Pulando teste (pedido não criado)")
        return
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/orders/{order_id}/advance-stage",
            json={"stage": "separacao"}
        )
        
        if response.status_code == 200:
            data = response.json()
            order = data.get("order", {})
            print(f"✅ Etapa avançada")
            print(f"   Novo status: {order.get('status')}")
        else:
            print(f"❌ Erro: {response.status_code}")
            print(response.text)


async def test_process_with_ai(order_id: str):
    """Testa processamento com IA"""
    print("\n=== Teste 5: Processar com IA ===")
    
    if not order_id:
        print("⚠️  Pulando teste (pedido não criado)")
        return
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/orders/{order_id}/process-with-ai",
            json={
                "message": "Onde está meu pedido?",
                "context": {}
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("response", "")
            print(f"✅ Processado com IA")
            print(f"   Resposta: {ai_response[:100]}...")
        else:
            print(f"❌ Erro: {response.status_code}")
            print(response.text)


async def test_chat_message():
    """Testa processamento de mensagem no chat"""
    print("\n=== Teste 6: Processar Mensagem no Chat ===")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/chatbot/process-message",
            json={
                "user_id": "test_user_123",
                "message": "Onde está meu pedido?",
                "session_id": "test_session_001"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                response_data = data.get("response", {})
                if isinstance(response_data, dict):
                    message = response_data.get("response", "")
                else:
                    message = str(response_data)
                print(f"✅ Mensagem processada")
                print(f"   Resposta: {message[:100]}...")
            else:
                print(f"❌ Erro: {data.get('error')}")
        else:
            print(f"❌ Erro HTTP: {response.status_code}")
            print(response.text)


async def test_health():
    """Testa health check"""
    print("\n=== Teste 0: Health Check ===")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Serviço está rodando")
                return True
            else:
                print(f"❌ Serviço retornou: {response.status_code}")
                return False
        except httpx.ConnectError:
            print("❌ Serviço não está rodando!")
            print(f"   Certifique-se de que o Chatbot Service está rodando em {BASE_URL}")
            return False


async def main():
    """Executa todos os testes"""
    print("=" * 50)
    print("TESTE RÁPIDO DO SISTEMA DE PEDIDOS")
    print("=" * 50)
    
    # Testa se o serviço está rodando
    is_running = await test_health()
    if not is_running:
        print("\n⚠️  Inicie o serviço antes de continuar:")
        print("   python main.py")
        return
    
    # Executa testes
    order_id = await test_create_order()
    await test_get_order(order_id)
    await test_list_orders()
    await test_advance_stage(order_id)
    await test_process_with_ai(order_id)
    await test_chat_message()
    
    print("\n" + "=" * 50)
    print("TESTES CONCLUÍDOS")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
