"""
Utilitário de Health Check
Responsável por verificar saúde dos microserviços
"""

import asyncio
import logging
import time
from typing import Dict, Any, List
import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class HealthChecker:
    """Verificador de saúde dos microserviços"""
    
    def __init__(self):
        self.services = [
            ("user", settings.USER_SERVICE_URL),
            ("import", settings.IMPORT_SERVICE_URL),
            ("chatbot", settings.CHATBOT_SERVICE_URL),
            ("ai", settings.AI_SERVICE_URL),
        ]
        
        self.http_client = None
        self.last_check = None
        self.check_interval = 30  # segundos
    
    async def initialize(self):
        """Inicializa o health checker"""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=10.0)
        )
    
    async def cleanup(self):
        """Limpa recursos"""
        if self.http_client:
            await self.http_client.aclose()
    
    async def check_service(self, service_name: str, service_url: str) -> Dict[str, Any]:
        """Verifica saúde de um serviço específico"""
        try:
            start_time = time.time()
            
            # Tentar health check
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
                    "url": service_url,
                    "timestamp": time.time()
                }
            else:
                return {
                    "service": service_name,
                    "status": "unhealthy",
                    "response_time": round(response_time, 3),
                    "url": service_url,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": time.time()
                }
                
        except httpx.TimeoutException:
            return {
                "service": service_name,
                "status": "timeout",
                "url": service_url,
                "error": "Timeout",
                "timestamp": time.time()
            }
            
        except httpx.ConnectError:
            return {
                "service": service_name,
                "status": "unavailable",
                "url": service_url,
                "error": "Connection error",
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "service": service_name,
                "status": "error",
                "url": service_url,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Verifica saúde de todos os serviços"""
        if not self.http_client:
            await self.initialize()
        
        # Criar tasks para verificação paralela
        tasks = [
            self.check_service(service_name, service_url)
            for service_name, service_url in self.services
        ]
        
        # Executar verificações em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        services_status = {}
        healthy_count = 0
        total_count = len(self.services)
        
        for i, result in enumerate(results):
            service_name = self.services[i][0]
            
            if isinstance(result, Exception):
                services_status[service_name] = {
                    "service": service_name,
                    "status": "error",
                    "error": str(result),
                    "timestamp": time.time()
                }
            else:
                services_status[service_name] = result
                if result["status"] == "healthy":
                    healthy_count += 1
        
        # Status geral
        overall_status = "healthy" if healthy_count == total_count else "degraded"
        if healthy_count == 0:
            overall_status = "unhealthy"
        
        self.last_check = time.time()
        
        return {
            "gateway": "healthy",
            "overall_status": overall_status,
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": services_status,
            "last_check": self.last_check,
            "timestamp": time.time()
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtém status atual (com cache)"""
        current_time = time.time()
        
        # Se não fez check recentemente, fazer agora
        if not self.last_check or (current_time - self.last_check) > self.check_interval:
            return await self.check_all_services()
        
        # Retornar status em cache (implementação básica)
        return {
            "gateway": "healthy",
            "message": "Status em cache, use /health/check para verificação completa",
            "last_check": self.last_check,
            "timestamp": current_time
        }
    
    async def check_specific_service(self, service_name: str) -> Dict[str, Any]:
        """Verifica saúde de um serviço específico"""
        service_url = None
        for name, url in self.services:
            if name == service_name:
                service_url = url
                break
        
        if not service_url:
            return {
                "error": f"Serviço '{service_name}' não encontrado",
                "timestamp": time.time()
            }
        
        return await self.check_service(service_name, service_url)
    
    def get_services_list(self) -> List[str]:
        """Retorna lista de serviços monitorados"""
        return [service_name for service_name, _ in self.services]
