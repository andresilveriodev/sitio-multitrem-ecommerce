"""
Testes para o serviço de pedidos
"""

import pytest
from datetime import datetime
from services.order_service import order_service
from models.order_models import (
    OrderItem, DeliveryAddress, PaymentMethod, OrderStatus
)


@pytest.mark.asyncio
async def test_create_order():
    """Testa criação de pedido"""
    items = [
        OrderItem(
            product_id="prod_001",
            product_name="Tomate",
            quantity=2,
            unit_price=15.50,
            total_price=31.00
        )
    ]
    
    order = await order_service.create_order(
        user_id="test_user_123",
        items=items,
        payment_method=PaymentMethod.PIX
    )
    
    assert order is not None
    assert order.user_id == "test_user_123"
    assert order.total_amount == 31.00
    assert order.status == OrderStatus.PENDING
    assert order.order_number.startswith("PED-")


@pytest.mark.asyncio
async def test_get_order():
    """Testa busca de pedido"""
    # Cria pedido
    items = [OrderItem(
        product_id="prod_001",
        product_name="Teste",
        quantity=1,
        unit_price=10.0,
        total_price=10.0
    )]
    
    order = await order_service.create_order(
        user_id="test_user_123",
        items=items
    )
    
    # Busca pedido
    found_order = await order_service.get_order(order.id)
    
    assert found_order is not None
    assert found_order.id == order.id
    assert found_order.order_number == order.order_number


@pytest.mark.asyncio
async def test_get_user_orders():
    """Testa listagem de pedidos do usuário"""
    # Cria alguns pedidos
    items = [OrderItem(
        product_id="prod_001",
        product_name="Teste",
        quantity=1,
        unit_price=10.0,
        total_price=10.0
    )]
    
    order1 = await order_service.create_order(
        user_id="test_user_123",
        items=items
    )
    
    order2 = await order_service.create_order(
        user_id="test_user_123",
        items=items
    )
    
    # Busca pedidos do usuário
    user_orders = await order_service.get_user_orders(
        user_id="test_user_123"
    )
    
    assert len(user_orders) >= 2
    assert any(o.id == order1.id for o in user_orders)
    assert any(o.id == order2.id for o in user_orders)


@pytest.mark.asyncio
async def test_update_order():
    """Testa atualização de pedido"""
    from models.order_models import OrderUpdate
    
    # Cria pedido
    items = [OrderItem(
        product_id="prod_001",
        product_name="Teste",
        quantity=1,
        unit_price=10.0,
        total_price=10.0
    )]
    
    order = await order_service.create_order(
        user_id="test_user_123",
        items=items
    )
    
    # Atualiza pedido
    update = OrderUpdate(
        order_id=order.id,
        status=OrderStatus.CONFIRMED
    )
    
    updated_order = await order_service.update_order(order.id, update)
    
    assert updated_order is not None
    assert updated_order.status == OrderStatus.CONFIRMED


@pytest.mark.asyncio
async def test_advance_order_stage():
    """Testa avanço de etapa do pedido"""
    # Cria pedido
    items = [OrderItem(
        product_id="prod_001",
        product_name="Teste",
        quantity=1,
        unit_price=10.0,
        total_price=10.0
    )]
    
    order = await order_service.create_order(
        user_id="test_user_123",
        items=items
    )
    
    # Avança para separação
    updated_order = await order_service.advance_order_stage(
        order.id,
        "separacao"
    )
    
    assert updated_order is not None
    assert updated_order.status == OrderStatus.IN_SEPARATION
    
    # Verifica etapas
    stages = await order_service.get_order_stages(order.id)
    assert len(stages) >= 2
    assert any(s.stage == "separacao" for s in stages)


@pytest.mark.asyncio
async def test_cancel_order():
    """Testa cancelamento de pedido"""
    # Cria pedido
    items = [OrderItem(
        product_id="prod_001",
        product_name="Teste",
        quantity=1,
        unit_price=10.0,
        total_price=10.0
    )]
    
    order = await order_service.create_order(
        user_id="test_user_123",
        items=items
    )
    
    # Cancela pedido
    cancelled_order = await order_service.cancel_order(order.id)
    
    assert cancelled_order is not None
    assert cancelled_order.status == OrderStatus.CANCELLED


@pytest.mark.asyncio
async def test_get_order_stages():
    """Testa busca de etapas do pedido"""
    # Cria pedido
    items = [OrderItem(
        product_id="prod_001",
        product_name="Teste",
        quantity=1,
        unit_price=10.0,
        total_price=10.0
    )]
    
    order = await order_service.create_order(
        user_id="test_user_123",
        items=items
    )
    
    # Busca etapas
    stages = await order_service.get_order_stages(order.id)
    
    assert len(stages) >= 1
    assert stages[0].stage == "pedido"
    assert stages[0].status == "completed"
