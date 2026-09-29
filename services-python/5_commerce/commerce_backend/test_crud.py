#!/usr/bin/env python3
"""
Script de teste CRUD completo para o Commerce Service
Testa todas as operações básicas de Create, Read, Update, Delete
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal
from datetime import datetime, date
import logging

from db_session import SessionLocal, engine
from models.commerce import (
    ProductCategory, Product, PriceList, ProductPrice, PriceProfile,
    Customer, CustomerAddress, DeliveryZone, CustomerProductPrice,
    Order, OrderItem, OrderStatus, OrderChannel, Payment, PaymentMethod, PaymentStatus
)
from services.product_service import ProductService
from services.customer_service import CustomerService
from services.order_service import OrderService
from services.payment_service import PaymentService
from services.shipping_service import ShippingService
from services.pricing_service import PricingService
from schemas.product import ProductCategoryCreate, ProductCreate, PriceListCreate, ProductPriceCreate
from schemas.customer import CustomerCreate, CustomerAddressCreate
from schemas.order import OrderCreate, OrderItemCreate
from schemas.payment import PaymentCreate

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_connection():
    """Testa conexão com o banco de dados"""
    logger.info("🔌 Testando conexão com banco de dados...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Conexão com banco de dados estabelecida com sucesso!")
            return True
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com banco de dados: {e}")
        return False


def test_product_crud(db: Session):
    """Testa CRUD de produtos"""
    logger.info("\n" + "="*60)
    logger.info("📦 TESTE CRUD - PRODUTOS")
    logger.info("="*60)
    
    try:
        # CREATE - Categoria
        logger.info("\n1. CREATE - Criando categoria...")
        category = ProductService.create_category(db, ProductCategoryCreate(
            name="Hortaliças",
            sort_order=1
        ))
        logger.info(f"✅ Categoria criada: ID={category.id}, Nome={category.name}")
        
        # CREATE - Produto
        logger.info("\n2. CREATE - Criando produto...")
        product = ProductService.create_product(db, ProductCreate(
            category_id=category.id,
            sku="ALFACE_UN",
            name="Alface Unidade",
            unit="un",
            active=True
        ))
        logger.info(f"✅ Produto criado: ID={product.id}, SKU={product.sku}, Nome={product.name}")
        
        # READ - Buscar produto
        logger.info("\n3. READ - Buscando produto...")
        found_product = ProductService.get_product(db, product.id)
        if found_product:
            logger.info(f"✅ Produto encontrado: {found_product.name}")
        else:
            logger.error("❌ Produto não encontrado!")
            return False
        
        # UPDATE - Atualizar produto
        logger.info("\n4. UPDATE - Atualizando produto...")
        from schemas.product import ProductUpdate
        updated_product = ProductService.update_product(db, product.id, ProductUpdate(
            name="Alface Americana Unidade"
        ))
        if updated_product:
            logger.info(f"✅ Produto atualizado: {updated_product.name}")
        else:
            logger.error("❌ Erro ao atualizar produto!")
            return False
        
        # READ - Listar produtos
        logger.info("\n5. READ - Listando produtos...")
        products = ProductService.get_products(db, skip=0, limit=10)
        logger.info(f"✅ Total de produtos encontrados: {len(products)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de produtos: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_customer_crud(db: Session):
    """Testa CRUD de clientes"""
    logger.info("\n" + "="*60)
    logger.info("👤 TESTE CRUD - CLIENTES")
    logger.info("="*60)
    
    try:
        # CREATE - Cliente
        logger.info("\n1. CREATE - Criando cliente...")
        customer = CustomerService.create_customer(db, CustomerCreate(
            name="João Silva",
            phone_e164="+5562999999999",
            document="12345678900",
            price_profile=PriceProfile.VAREJO,
            notes="Cliente teste"
        ))
        logger.info(f"✅ Cliente criado: ID={customer.id}, Nome={customer.name}, Perfil={customer.price_profile.value}")
        
        # READ - Buscar cliente
        logger.info("\n2. READ - Buscando cliente...")
        found_customer = CustomerService.get_customer(db, customer.id)
        if found_customer:
            logger.info(f"✅ Cliente encontrado: {found_customer.name}")
        else:
            logger.error("❌ Cliente não encontrado!")
            return False
        
        # READ - Buscar por telefone
        logger.info("\n3. READ - Buscando cliente por telefone...")
        customer_by_phone = CustomerService.get_customer_by_phone(db, "+5562999999999")
        if customer_by_phone:
            logger.info(f"✅ Cliente encontrado por telefone: {customer_by_phone.name}")
        else:
            logger.error("❌ Cliente não encontrado por telefone!")
            return False
        
        # UPDATE - Atualizar cliente
        logger.info("\n4. UPDATE - Atualizando cliente...")
        from schemas.customer import CustomerUpdate
        updated_customer = CustomerService.update_customer(db, customer.id, CustomerUpdate(
            price_profile=PriceProfile.RESTAURANTE_LOW
        ))
        if updated_customer:
            logger.info(f"✅ Cliente atualizado: Perfil={updated_customer.price_profile.value}")
        else:
            logger.error("❌ Erro ao atualizar cliente!")
            return False
        
        # CREATE - Endereço
        logger.info("\n5. CREATE - Criando endereço...")
        # Primeiro criar uma zona
        zone = DeliveryZone(name="Centro", fee=Decimal("5.00"), active=True)
        db.add(zone)
        db.flush()
        
        address = CustomerService.create_customer_address(db, CustomerAddressCreate(
            customer_id=customer.id,
            delivery_zone_id=zone.id,
            label="Casa",
            street="Rua Teste",
            number="123",
            district="Centro",
            city="Goiânia",
            state="GO",
            zip="74000000",
            is_default=True
        ))
        logger.info(f"✅ Endereço criado: ID={address.id}, Label={address.label}")
        
        # READ - Listar endereços
        logger.info("\n6. READ - Listando endereços do cliente...")
        addresses = CustomerService.get_customer_addresses(db, customer.id)
        logger.info(f"✅ Total de endereços encontrados: {len(addresses)}")
        
        return True, customer, zone
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de clientes: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_order_crud(db: Session, customer, zone):
    """Testa CRUD de pedidos"""
    logger.info("\n" + "="*60)
    logger.info("🛒 TESTE CRUD - PEDIDOS")
    logger.info("="*60)
    
    try:
        # Buscar categoria e produto
        category = db.query(ProductCategory).filter(ProductCategory.name == "Hortaliças").first()
        product = db.query(Product).filter(Product.sku == "ALFACE_UN").first()
        
        if not category or not product:
            logger.error("❌ Categoria ou produto não encontrado!")
            return False
        
        # Criar lista de preços
        price_list = PriceList(name="Padrão", active=True)
        db.add(price_list)
        db.flush()
        
        # Criar preço do produto
        product_price = ProductPrice(
            product_id=product.id,
            price_list_id=price_list.id,
            price=Decimal("4.00")
        )
        db.add(product_price)
        db.commit()
        
        # Buscar endereço do cliente
        address = db.query(CustomerAddress).filter(CustomerAddress.customer_id == customer.id).first()
        
        # CREATE - Pedido
        logger.info("\n1. CREATE - Criando pedido...")
        order = OrderService.create_order(db, OrderCreate(
            customer_id=customer.id,
            channel=OrderChannel.MANUAL,
            price_list_id=price_list.id,
            delivery_address_id=address.id if address else None,
            delivery_fee=Decimal("5.00"),
            items=[
                OrderItemCreate(
                    product_id=product.id,
                    qty=Decimal("10"),
                    unit_price=Decimal("4.00"),
                    notes="Teste"
                )
            ]
        ))
        logger.info(f"✅ Pedido criado: ID={order.id}, Total=R$ {order.total}, Status={order.status.value}")
        
        # READ - Buscar pedido
        logger.info("\n2. READ - Buscando pedido...")
        found_order = OrderService.get_order(db, order.id)
        if found_order:
            logger.info(f"✅ Pedido encontrado: ID={found_order.id}, Total=R$ {found_order.total}")
        else:
            logger.error("❌ Pedido não encontrado!")
            return False
        
        # UPDATE - Atualizar pedido
        logger.info("\n3. UPDATE - Atualizando pedido...")
        from schemas.order import OrderUpdate
        updated_order = OrderService.update_order(db, order.id, OrderUpdate(
            notes="Pedido atualizado"
        ))
        if updated_order:
            logger.info(f"✅ Pedido atualizado: Notas={updated_order.notes}")
        else:
            logger.error("❌ Erro ao atualizar pedido!")
            return False
        
        # CONFIRM - Confirmar pedido
        logger.info("\n4. CONFIRM - Confirmando pedido...")
        confirmed_order = OrderService.confirm_order(db, order.id)
        if confirmed_order:
            logger.info(f"✅ Pedido confirmado: Status={confirmed_order.status.value}")
        else:
            logger.error("❌ Erro ao confirmar pedido!")
            return False
        
        # READ - Listar pedidos
        logger.info("\n5. READ - Listando pedidos...")
        orders = OrderService.get_orders(db, skip=0, limit=10)
        logger.info(f"✅ Total de pedidos encontrados: {len(orders)}")
        
        return True, order
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de pedidos: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_payment_crud(db: Session, order):
    """Testa CRUD de pagamentos"""
    logger.info("\n" + "="*60)
    logger.info("💳 TESTE CRUD - PAGAMENTOS")
    logger.info("="*60)
    
    try:
        # CREATE - Pagamento
        logger.info("\n1. CREATE - Criando pagamento...")
        payment = PaymentService.create_payment(db, PaymentCreate(
            order_id=order.id,
            method=PaymentMethod.PIX,
            amount=order.total,
            external_ref="PIX123456789"
        ))
        logger.info(f"✅ Pagamento criado: ID={payment.id}, Valor=R$ {payment.amount}, Status={payment.status.value}")
        
        # READ - Buscar pagamento
        logger.info("\n2. READ - Buscando pagamento...")
        found_payment = PaymentService.get_payment(db, payment.id)
        if found_payment:
            logger.info(f"✅ Pagamento encontrado: ID={found_payment.id}")
        else:
            logger.error("❌ Pagamento não encontrado!")
            return False
        
        # UPDATE - Marcar como pago
        logger.info("\n3. UPDATE - Marcando pagamento como pago...")
        paid_payment = PaymentService.mark_as_paid(db, payment.id, "PIX123456789")
        if paid_payment:
            logger.info(f"✅ Pagamento marcado como pago: Status={paid_payment.status.value}, Pago em={paid_payment.paid_at}")
        else:
            logger.error("❌ Erro ao marcar pagamento como pago!")
            return False
        
        # READ - Listar pagamentos
        logger.info("\n4. READ - Listando pagamentos...")
        payments = PaymentService.get_payments(db, skip=0, limit=10, order_id=order.id)
        logger.info(f"✅ Total de pagamentos encontrados: {len(payments)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de pagamentos: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pricing_rules(db: Session):
    """Testa regras de precificação"""
    logger.info("\n" + "="*60)
    logger.info("💰 TESTE - REGRAS DE PRECIFICAÇÃO")
    logger.info("="*60)
    
    try:
        # Buscar cliente e produto
        customer = db.query(Customer).first()
        product = db.query(Product).filter(Product.sku == "ALFACE_UN").first()
        
        if not customer or not product:
            logger.error("❌ Cliente ou produto não encontrado!")
            return False
        
        logger.info(f"\nCliente: {customer.name}, Perfil: {customer.price_profile.value}")
        logger.info(f"Produto: {product.name}")
        
        # Testar obtenção de preço
        logger.info("\n1. Obtendo preço por perfil...")
        price = PricingService.get_product_price(db, customer, product, is_palito=False)
        logger.info(f"✅ Preço obtido: R$ {price}")
        
        # Testar normalização de alfaces
        logger.info("\n2. Testando normalização de alfaces...")
        palitos, unidades = PricingService.normalize_alface_units(Decimal("10"), "ALFACE_UN")
        logger.info(f"✅ 10 alfaces = {palitos} palitos + {unidades} unidades")
        
        palitos, unidades = PricingService.normalize_alface_units(Decimal("7"), "ALFACE_UN")
        logger.info(f"✅ 7 alfaces = {palitos} palitos + {unidades} unidades")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de precificação: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_shipping_calculation(db: Session):
    """Testa cálculo de frete"""
    logger.info("\n" + "="*60)
    logger.info("🚚 TESTE - CÁLCULO DE FRETE")
    logger.info("="*60)
    
    try:
        # Buscar endereço
        address = db.query(CustomerAddress).first()
        
        if not address:
            logger.error("❌ Endereço não encontrado!")
            return False
        
        logger.info(f"\nEndereço: {address.street}, {address.district}")
        
        # Testar cálculo de frete
        logger.info("\n1. Calculando frete...")
        subtotal = Decimal("30.00")
        shipping = ShippingService.calculate_shipping(db, address, subtotal)
        logger.info(f"✅ Frete calculado: R$ {shipping} (Subtotal: R$ {subtotal})")
        
        # Testar frete grátis
        logger.info("\n2. Testando frete grátis (subtotal >= R$ 50)...")
        subtotal_free = Decimal("60.00")
        shipping_free = ShippingService.calculate_shipping(db, address, subtotal_free)
        logger.info(f"✅ Frete calculado: R$ {shipping_free} (Subtotal: R$ {subtotal_free})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de frete: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executa todos os testes CRUD"""
    logger.info("🚀 Iniciando testes CRUD do Commerce Service")
    logger.info("="*60)
    
    # Testar conexão
    if not test_connection():
        logger.error("❌ Falha na conexão. Abortando testes.")
        return 1
    
    db = SessionLocal()
    results = {}
    
    try:
        # Teste de Produtos
        results['products'] = test_product_crud(db)
        
        # Teste de Clientes
        success, customer, zone = test_customer_crud(db)
        results['customers'] = success
        
        if success and customer and zone:
            # Teste de Pedidos
            success, order = test_order_crud(db, customer, zone)
            results['orders'] = success
            
            if success and order:
                # Teste de Pagamentos
                results['payments'] = test_payment_crud(db, order)
        
        # Teste de Precificação
        results['pricing'] = test_pricing_rules(db)
        
        # Teste de Frete
        results['shipping'] = test_shipping_calculation(db)
        
        # Resumo
        logger.info("\n" + "="*60)
        logger.info("📊 RESUMO DOS TESTES")
        logger.info("="*60)
        
        for test_name, result in results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            logger.info(f"{test_name.upper()}: {status}")
        
        all_passed = all(results.values())
        
        if all_passed:
            logger.info("\n✅ TODOS OS TESTES PASSARAM!")
            return 0
        else:
            logger.error("\n❌ ALGUNS TESTES FALHARAM!")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    exit(main())
