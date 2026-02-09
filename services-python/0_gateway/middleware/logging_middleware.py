"""
Middleware de Logging
Responsável por registrar logs de requisições e respostas
"""

import time
import json
import logging
from fastapi import Request, Response
from typing import Dict, Any
import uuid

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """Middleware para logging de requisições e respostas"""
    
    def __init__(self, app):
        self.app = app
        self.request_logger = logging.getLogger("gateway.requests")
        self.error_logger = logging.getLogger("gateway.errors")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        # Gerar ID único para a requisição
        request_id = str(uuid.uuid4())
        scope["request_id"] = request_id
        
        # Log da requisição
        await self._log_request(request, request_id)
        
        # Capturar resposta
        response_data = {"status_code": None, "headers": {}, "body": None}
        
        async def custom_send(message):
            if message["type"] == "http.response.start":
                response_data["status_code"] = message["status"]
                response_data["headers"] = dict(message["headers"])
            elif message["type"] == "http.response.body":
                response_data["body"] = message["body"].decode() if message["body"] else None
            
            await send(message)
        
        try:
            await self.app(scope, receive, custom_send)
            
            # Calcular tempo de resposta
            response_time = time.time() - start_time
            
            # Log da resposta
            await self._log_response(request, response_data, response_time, request_id)
            
        except Exception as e:
            # Log de erro
            response_time = time.time() - start_time
            await self._log_error(request, e, response_time, request_id)
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """Log da requisição recebida"""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": time.time()
        }
        
        # Adicionar informações do usuário se autenticado
        user = request.scope.get("user")
        if user:
            log_data["user_id"] = user.get("id")
            log_data["user_email"] = user.get("email")
        
        self.request_logger.info(f"Request: {json.dumps(log_data, default=str)}")
    
    async def _log_response(self, request: Request, response_data: Dict[str, Any], response_time: float, request_id: str):
        """Log da resposta enviada"""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response_data["status_code"],
            "response_time": round(response_time, 3),
            "timestamp": time.time()
        }
        
        # Log de erro se status code >= 400
        if response_data["status_code"] and response_data["status_code"] >= 400:
            log_data["error"] = True
            self.error_logger.warning(f"Error Response: {json.dumps(log_data, default=str)}")
        else:
            self.request_logger.info(f"Response: {json.dumps(log_data, default=str)}")
    
    async def _log_error(self, request: Request, error: Exception, response_time: float, request_id: str):
        """Log de erro"""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "error": str(error),
            "error_type": type(error).__name__,
            "response_time": round(response_time, 3),
            "timestamp": time.time()
        }
        
        self.error_logger.error(f"Request Error: {json.dumps(log_data, default=str)}", exc_info=True)


class MetricsMiddleware:
    """Middleware para métricas de performance"""
    
    def __init__(self, app):
        self.app = app
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "error_requests": 0,
            "average_response_time": 0,
            "endpoint_stats": {}
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        # Incrementar contador total
        self.metrics["total_requests"] += 1
        
        # Atualizar estatísticas por endpoint
        path = request.url.path
        if path not in self.metrics["endpoint_stats"]:
            self.metrics["endpoint_stats"][path] = {
                "count": 0,
                "total_time": 0,
                "errors": 0
            }
        
        self.metrics["endpoint_stats"][path]["count"] += 1
        
        try:
            await self.app(scope, receive, send)
            
            # Calcular tempo de resposta
            response_time = time.time() - start_time
            
            # Atualizar métricas
            self.metrics["successful_requests"] += 1
            self.metrics["endpoint_stats"][path]["total_time"] += response_time
            
            # Calcular tempo médio
            total_time = sum(stats["total_time"] for stats in self.metrics["endpoint_stats"].values())
            total_requests = sum(stats["count"] for stats in self.metrics["endpoint_stats"].values())
            self.metrics["average_response_time"] = total_time / total_requests if total_requests > 0 else 0
            
        except Exception as e:
            # Atualizar métricas de erro
            self.metrics["error_requests"] += 1
            self.metrics["endpoint_stats"][path]["errors"] += 1
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas atuais"""
        return self.metrics.copy()
