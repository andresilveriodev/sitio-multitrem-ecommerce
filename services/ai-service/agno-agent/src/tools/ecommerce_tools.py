"""
Ferramentas do E-commerce para o Agente de Vendas.
Cada funcao e automaticamente disponibilizada ao agente atraves do decorator.
Configurado para o projeto Sitio Multitrem.
"""

import httpx
import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# ============================================
# URLs dos Microsservicos - Sitio Multitrem
# ============================================
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:3001')
CART_SERVICE_URL = os.getenv('CART_SERVICE_URL', 'http://localhost:3002')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://localhost:3003')
PAYMENT_SERVICE_URL = os.getenv('PAYMENT_SERVICE_URL', 'http://localhost:3004')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:3005')
WHATSAPP_SERVICE_URL = os.getenv('WHATSAPP_SERVICE_URL', 'http://localhost:3006')
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:8000')

# Variavel global para armazenar visitor_id (sera injetada pelo contexto)
_current_visitor_id = None

def set_visitor_id(visitor_id: str):
    """Define o visitor_id atual para as operacoes."""
    global _current_visitor_id
    _current_visitor_id = visitor_id

def get_visitor_id() -> str:
    """Retorna o visitor_id atual."""
    return _current_visitor_id or "anonymous"


def list_products(category: str = None) -> dict:
    """
    Lista produtos disponiveis no Sitio Multitrem.
    
    Args:
        category: Categoria opcional para filtrar (hortalicas, ovos, kits, combos)
    
    Returns:
        dict: Lista de produtos com nome, preco e disponibilidade
    """
    try:
        url = f"{PRODUCT_SERVICE_URL}/products"
        if category:
            url += f"?category={category}"
        
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        
        return {
            "success": True,
            "products": response.json()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def add_to_cart(product_id: int, quantity: int) -> dict:
    """
    Adiciona um produto ao carrinho do cliente.
    
    Args:
        product_id: ID do produto a adicionar
        quantity: Quantidade desejada
    
    Returns:
        dict: Carrinho atualizado com os itens
    """
    try:
        visitor_id = get_visitor_id()
        
        payload = {
            "productId": product_id,
            "quantity": quantity
        }
        
        response = httpx.post(
            f"{CART_SERVICE_URL}/cart/{visitor_id}/items",
            json=payload,
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "cart": response.json(),
            "message": "Produto adicionado ao carrinho com sucesso!"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def remove_from_cart(product_id: int) -> dict:
    """
    Remove um produto do carrinho do cliente.
    
    Args:
        product_id: ID do produto a remover
    
    Returns:
        dict: Carrinho atualizado apos remocao
    """
    try:
        visitor_id = get_visitor_id()
        
        response = httpx.delete(
            f"{CART_SERVICE_URL}/cart/{visitor_id}/items/{product_id}",
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "cart": response.json(),
            "message": "Produto removido do carrinho"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def view_cart() -> dict:
    """
    Mostra o carrinho atual do cliente com todos os itens e total.
    
    Returns:
        dict: Carrinho com itens, quantidades e valor total
    """
    try:
        visitor_id = get_visitor_id()
        
        response = httpx.get(
            f"{CART_SERVICE_URL}/cart/{visitor_id}",
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "cart": response.json()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def check_delivery_slots() -> dict:
    """
    Verifica os dias e horarios disponiveis para entrega.
    Entregas disponiveis de quarta a sabado, periodo da manha.
    
    Returns:
        dict: Lista de slots disponiveis com data e horario
    """
    try:
        response = httpx.get(
            f"{ORDER_SERVICE_URL}/delivery/slots",
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "slots": response.json()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_order(
    delivery_date: str,
    customer_name: str,
    customer_phone: str,
    customer_address: str
) -> dict:
    """
    Cria um novo pedido com os itens do carrinho.
    
    Args:
        delivery_date: Data de entrega no formato YYYY-MM-DD
        customer_name: Nome completo do cliente
        customer_phone: Telefone do cliente com DDD
        customer_address: Endereco completo para entrega
    
    Returns:
        dict: Pedido criado com numero, itens e valor total
    """
    try:
        visitor_id = get_visitor_id()
        
        # Primeiro buscar o carrinho
        cart_response = httpx.get(
            f"{CART_SERVICE_URL}/cart/{visitor_id}",
            timeout=10.0
        )
        cart_response.raise_for_status()
        cart = cart_response.json()
        
        if not cart.get('items') or len(cart['items']) == 0:
            return {
                "success": False,
                "error": "Carrinho esta vazio. Adicione produtos antes de criar o pedido."
            }
        
        # Criar o pedido
        order_payload = {
            "visitorId": visitor_id,
            "items": cart['items'],
            "deliveryDate": delivery_date,
            "customerName": customer_name,
            "customerPhone": customer_phone,
            "customerAddress": customer_address
        }
        
        response = httpx.post(
            f"{ORDER_SERVICE_URL}/orders",
            json=order_payload,
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "order": response.json(),
            "message": "Pedido criado com sucesso!"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def generate_payment_link(order_id: int, method: str) -> dict:
    """
    Gera link ou QR Code de pagamento para o pedido.
    
    Args:
        order_id: ID do pedido
        method: Metodo de pagamento ('pix' ou 'boleto')
    
    Returns:
        dict: Link de pagamento ou QR Code Pix
    """
    try:
        if method not in ['pix', 'boleto']:
            return {
                "success": False,
                "error": "Metodo invalido. Use 'pix' ou 'boleto'."
            }
        
        response = httpx.post(
            f"{PAYMENT_SERVICE_URL}/payments/{method}",
            json={"orderId": order_id},
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "payment": response.json(),
            "message": f"Link de pagamento {method.upper()} gerado com sucesso!"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

