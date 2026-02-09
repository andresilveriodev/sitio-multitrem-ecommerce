"""
Serviço principal do Gateway
Responsável por gerenciar conexões e operações do gateway
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import httpx
import time

from ..config import settings

logger = logging.getLogger(__name__)


class GatewayService:
    """Serviço principal do Gateway"""
    
    def __init__(self):
        self.http_client = None
        self.service_status = {}
        self.circuit_breakers = {}
        self.load_balancers = {}
        
        # Configurações de circuit breaker
        self.circuit_breaker_config = {
            "failure_threshold": settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            "recovery_timeout": settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
        }
    
    async def initialize(self):
        """Inicializa o serviço"""
        logger.info("Inicializando Gateway Service...")
        
        # Criar cliente HTTP
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=settings.CONNECT_TIMEOUT,
                read=settings.REQUEST_TIMEOUT
            )
        )
        
        # Inicializar circuit breakers
        await self._initialize_circuit_breakers()
        
        # Inicializar load balancers
        if settings.ENABLE_LOAD_BALANCING:
            await self._initialize_load_balancers()
        
        logger.info("Gateway Service inicializado com sucesso!")
    
    async def cleanup(self):
        """Limpa recursos do serviço"""
        logger.info("Limpando recursos do Gateway Service...")
        
        if self.http_client:
            await self.http_client.aclose()
        
        logger.info("Recursos do Gateway Service limpos!")
    
    async def _initialize_circuit_breakers(self):
        """Inicializa circuit breakers para cada serviço"""
        services = [
            ("user", settings.USER_SERVICE_URL),
            ("import", settings.IMPORT_SERVICE_URL),
            ("chatbot", settings.CHATBOT_SERVICE_URL),
            ("ai", settings.AI_SERVICE_URL),
        ]
        
        for service_name, service_url in services:
            self.circuit_breakers[service_name] = CircuitBreaker(
                service_name,
                self.circuit_breaker_config
            )
    
    async def _initialize_load_balancers(self):
        """Inicializa load balancers"""
        # Implementação básica de round-robin
        for service_name in self.circuit_breakers.keys():
            self.load_balancers[service_name] = RoundRobinLoadBalancer()
    
    async def make_request(self, service_name: str, method: str, url: str, **kwargs) -> httpx.Response:
        """Faz requisição para um serviço com circuit breaker"""
        circuit_breaker = self.circuit_breakers.get(service_name)
        
        if not circuit_breaker:
            raise ValueError(f"Serviço '{service_name}' não encontrado")
        
        # Verificar se circuit breaker está aberto
        if circuit_breaker.is_open():
            raise ServiceUnavailableError(f"Serviço '{service_name}' temporariamente indisponível")
        
        try:
            # Fazer requisição
            response = await self.http_client.request(method, url, **kwargs)
            
            # Registrar sucesso
            circuit_breaker.record_success()
            
            return response
            
        except Exception as e:
            # Registrar falha
            circuit_breaker.record_failure()
            raise
    
    async def health_check_service(self, service_name: str, service_url: str) -> Dict[str, Any]:
        """Verifica saúde de um serviço específico"""
        try:
            start_time = time.time()
            
            response = await self.http_client.get(
                f"{service_url}/health",
                timeout=5.0
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "service": service_name,
                    "status": "healthy",
                    "response_time": round(response_time, 3),
                    "timestamp": time.time()
                }
            else:
                return {
                    "service": service_name,
                    "status": "unhealthy",
                    "response_time": round(response_time, 3),
                    "timestamp": time.time()
                }
                
        except Exception as e:
            return {
                "service": service_name,
                "status": "unavailable",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def get_all_services_status(self) -> Dict[str, Any]:
        """Obtém status de todos os serviços"""
        services = [
            ("user", settings.USER_SERVICE_URL),
            ("import", settings.IMPORT_SERVICE_URL),
            ("chatbot", settings.CHATBOT_SERVICE_URL),
            ("ai", settings.AI_SERVICE_URL),
        ]
        
        tasks = [
            self.health_check_service(service_name, service_url)
            for service_name, service_url in services
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        status = {
            "gateway": "healthy",
            "services": {},
            "timestamp": time.time()
        }
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                service_name = services[i][0]
                status["services"][service_name] = {
                    "status": "error",
                    "error": str(result),
                    "timestamp": time.time()
                }
            else:
                status["services"][result["service"]] = result
        
        return status


class CircuitBreaker:
    """Implementação de circuit breaker"""
    
    def __init__(self, service_name: str, config: Dict[str, Any]):
        self.service_name = service_name
        self.failure_threshold = config["failure_threshold"]
        self.recovery_timeout = config["recovery_timeout"]
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self) -> bool:
        """Verifica se circuit breaker está aberto"""
        if self.state == "OPEN":
            # Verificar se já passou tempo suficiente para tentar novamente
            if self.last_failure_time and time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False
    
    def record_success(self):
        """Registra sucesso"""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            self.last_failure_time = None
    
    def record_failure(self):
        """Registra falha"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker aberto para {self.service_name}")


class RoundRobinLoadBalancer:
    """Load balancer round-robin simples"""
    
    def __init__(self):
        self.current_index = 0
        self.instances = []
    
    def add_instance(self, instance_url: str):
        """Adiciona instância ao load balancer"""
        self.instances.append(instance_url)
    
    def get_next_instance(self) -> Optional[str]:
        """Obtém próxima instância"""
        if not self.instances:
            return None
        
        instance = self.instances[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.instances)
        return instance


class ServiceUnavailableError(Exception):
    """Exceção para serviço indisponível"""
    pass
