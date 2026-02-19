"""
Cliente HTTP para comunicação com o Commerce Service
"""

import httpx
from typing import Optional, Dict, Any, List
import structlog
from config import settings

logger = structlog.get_logger(__name__)


class CommerceServiceClient:
    """Cliente para comunicação com o Commerce Service"""
    
    def __init__(self):
        self.base_url = settings.COMMERCE_SERVICE_URL
        self.timeout = settings.COMMERCE_SERVICE_TIMEOUT
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Faz uma requisição HTTP para o Commerce Service"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                return response.json() if response.content else {}
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Erro HTTP ao chamar Commerce Service: {e.response.status_code} - {e.response.text}",
                endpoint=endpoint,
                method=method
            )
            raise
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão com Commerce Service: {e}", endpoint=endpoint)
            raise
    
    # ========== PRODUTOS ==========
    
    async def list_products(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lista produtos"""
        params = {"limit": limit, "offset": offset}
        if category:
            params["category"] = category
        if is_active is not None:
            params["is_active"] = is_active
        
        response = await self._request("GET", "/api/v1/products", params=params)
        return response.get("items", []) if isinstance(response, dict) else response
    
    async def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Busca um produto por ID"""
        try:
            return await self._request("GET", f"/api/v1/products/{product_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um produto"""
        return await self._request("POST", "/api/v1/products", data=product_data)
    
    async def update_product(
        self,
        product_id: int,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atualiza um produto"""
        return await self._request("PUT", f"/api/v1/products/{product_id}", data=product_data)
    
    async def list_categories(self) -> List[Dict[str, Any]]:
        """Lista categorias de produtos"""
        response = await self._request("GET", "/api/v1/products/categories")
        return response.get("items", []) if isinstance(response, dict) else response
    
    async def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma categoria"""
        return await self._request("POST", "/api/v1/products/categories", data=category_data)
    
    # ========== CLIENTES ==========
    
    async def list_customers(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lista clientes"""
        params = {"limit": limit, "offset": offset}
        response = await self._request("GET", "/api/v1/customers", params=params)
        return response.get("items", []) if isinstance(response, dict) else response
    
    async def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Busca um cliente por ID"""
        try:
            return await self._request("GET", f"/api/v1/customers/{customer_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um cliente"""
        return await self._request("POST", "/api/v1/customers", data=customer_data)
    
    async def update_customer(
        self,
        customer_id: int,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atualiza um cliente"""
        return await self._request("PUT", f"/api/v1/customers/{customer_id}", data=customer_data)
    
    async def list_customer_addresses(self, customer_id: int) -> List[Dict[str, Any]]:
        """Lista endereços de um cliente"""
        response = await self._request("GET", f"/api/v1/customers/{customer_id}/addresses")
        return response.get("items", []) if isinstance(response, dict) else response
    
    async def create_customer_address(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um endereço para um cliente"""
        return await self._request("POST", "/api/v1/customers/addresses", data=address_data)
    
    # ========== PEDIDOS ==========
    
    async def list_orders(
        self,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lista pedidos"""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if customer_id:
            params["customer_id"] = customer_id
        
        response = await self._request("GET", "/api/v1/orders", params=params)
        return response.get("items", []) if isinstance(response, dict) else response
    
    async def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Busca um pedido por ID"""
        try:
            return await self._request("GET", f"/api/v1/orders/{order_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um pedido"""
        return await self._request("POST", "/api/v1/orders", data=order_data)
    
    async def update_order(
        self,
        order_id: int,
        order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atualiza um pedido"""
        return await self._request("PUT", f"/api/v1/orders/{order_id}", data=order_data)
    
    async def confirm_order(self, order_id: int) -> Dict[str, Any]:
        """Confirma um pedido"""
        return await self._request("POST", f"/api/v1/orders/{order_id}/confirm")
    
    async def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """Cancela um pedido"""
        return await self._request("POST", f"/api/v1/orders/{order_id}/cancel")
    
    # ========== PAGAMENTOS ==========
    
    async def list_payments(
        self,
        order_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lista pagamentos"""
        params = {"limit": limit, "offset": offset}
        if order_id:
            params["order_id"] = order_id
        if status:
            params["status"] = status
        
        response = await self._request("GET", "/api/v1/payments", params=params)
        return response.get("items", []) if isinstance(response, dict) else response
    
    async def get_payment(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """Busca um pagamento por ID"""
        try:
            return await self._request("GET", f"/api/v1/payments/{payment_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um pagamento"""
        return await self._request("POST", "/api/v1/payments", data=payment_data)
    
    async def mark_payment_paid(self, payment_id: int) -> Dict[str, Any]:
        """Marca um pagamento como pago"""
        return await self._request("POST", f"/api/v1/payments/{payment_id}/mark-paid")
    
    # ========== ENTREGAS ==========
    
    async def list_delivery_routes(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Lista rotas de entrega"""
        params = {"limit": limit, "offset": offset}
        response = await self._request("GET", "/api/v1/deliveries/routes", params=params)
        return response.get("items", []) if isinstance(response, dict) else response
    
    async def get_delivery_route(self, route_id: int) -> Optional[Dict[str, Any]]:
        """Busca uma rota de entrega por ID"""
        try:
            return await self._request("GET", f"/api/v1/deliveries/routes/{route_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def create_delivery_route(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma rota de entrega"""
        return await self._request("POST", "/api/v1/deliveries/routes", data=route_data)
    
    async def update_delivery_stop(
        self,
        stop_id: int,
        stop_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atualiza uma parada de entrega"""
        return await self._request("PUT", f"/api/v1/deliveries/stops/{stop_id}", data=stop_data)


# Instância global do cliente
commerce_client = CommerceServiceClient()
