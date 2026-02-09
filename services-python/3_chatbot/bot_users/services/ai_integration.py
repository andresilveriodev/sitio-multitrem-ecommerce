"""
Serviço de integração com o AI Service
"""

import httpx
from typing import Dict, Optional, Any, List
import structlog
from datetime import datetime
import json
import time

from config import settings

logger = structlog.get_logger(__name__)


class AIServiceIntegration:
    """Integração com o AI Service"""
    
    def __init__(self):
        self.base_url = settings.AI_SERVICE_URL
        self.timeout = settings.AI_SERVICE_TIMEOUT
        self.client: Optional[httpx.AsyncClient] = None
    
    async def connect(self):
        """Inicializa cliente HTTP"""
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            base_url=self.base_url
        )
        logger.info(f"Cliente HTTP inicializado para AI Service: {self.base_url}")
    
    async def disconnect(self):
        """Fecha cliente HTTP"""
        if self.client:
            await self.client.aclose()
            logger.info("Cliente HTTP fechado")
    
    async def get_user_settings(self, user_id: str) -> Optional[Dict]:
        """Busca configurações de IA do usuário"""
        try:
            response = await self.client.get(f"/ai/user-settings/{user_id}")
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Configurações não encontradas para usuário {user_id}")
                return None
            else:
                logger.error(f"Erro ao buscar configurações: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Erro na comunicação com AI Service: {e}")
            return None
    
    async def get_user_subscription(self, user_id: str) -> Optional[Dict]:
        """Busca assinatura e limites do usuário"""
        start_time = time.time()
        url = f"{self.base_url}/ai/user-subscription/{user_id}"
        
        try:
            logger.info(
                "Buscando assinatura do usuário",
                url=url,
                method="GET",
                user_id=user_id
            )
            
            response = await self.client.get(f"/ai/user-subscription/{user_id}")
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                logger.info(
                    "Assinatura encontrada",
                    user_id=user_id,
                    status_code=response.status_code,
                    elapsed_time=f"{elapsed_time:.3f}s",
                    subscription_id=result.get("subscription_id"),
                    plan=result.get("plan"),
                    limits=result.get("usage_limits")
                )
                return result
            elif response.status_code == 404:
                logger.warning(
                    "Assinatura não encontrada para usuário",
                    user_id=user_id,
                    status_code=response.status_code,
                    elapsed_time=f"{elapsed_time:.3f}s",
                    url=url,
                    response_text=response.text[:200] if response.text else None
                )
                return None
            else:
                logger.error(
                    "Erro ao buscar assinatura",
                    user_id=user_id,
                    status_code=response.status_code,
                    elapsed_time=f"{elapsed_time:.3f}s",
                    url=url,
                    response_text=response.text[:500] if response.text else None
                )
                return None
        except httpx.TimeoutException as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Timeout ao buscar assinatura",
                user_id=user_id,
                elapsed_time=f"{elapsed_time:.3f}s",
                timeout=self.timeout,
                url=url,
                error=str(e)
            )
            return None
        except httpx.RequestError as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Erro de requisição ao buscar assinatura",
                user_id=user_id,
                elapsed_time=f"{elapsed_time:.3f}s",
                url=url,
                error_type=type(e).__name__,
                error=str(e)
            )
            return None
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Erro inesperado ao buscar assinatura",
                user_id=user_id,
                elapsed_time=f"{elapsed_time:.3f}s",
                url=url,
                error_type=type(e).__name__,
                error=str(e)
            )
            return None
    
    async def get_available_models(self) -> List[Dict]:
        """Busca modelos disponíveis"""
        try:
            response = await self.client.get("/ai/models")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao buscar modelos: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Erro na comunicação com AI Service: {e}")
            return []
    
    async def get_providers(self) -> Optional[Dict]:
        """Busca provedores disponíveis"""
        try:
            response = await self.client.get("/ai/providers")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao buscar provedores: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Erro na comunicação com AI Service: {e}")
            return None
    
    async def create_conversation(self, user_id: str, title: str = None) -> Optional[Dict]:
        """Cria nova conversa no AI Service"""
        try:
            data = {
                "user_id": user_id,
                "title": title or f"Conversa {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            }
            response = await self.client.post("/ai/conversations", json=data)
            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"Erro ao criar conversa: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Erro na comunicação com AI Service: {e}")
            return None
    
    async def generate_response(self, 
                              user_id: str,
                              message: str,
                              conversation_id: Optional[int] = None,
                              context_summary: str = "",
                              user_preferences: Dict = None,
                              provider: Optional[str] = None,
                              model: Optional[str] = None) -> Optional[Dict]:
        """
        Gera resposta da IA com suporte a contexto completo.
        """
        start_time = time.time()
        
        try:
            # Usa método completo com contexto
            return await self._generate_response_with_context(
                user_id=user_id,
                message=message,
                conversation_id=conversation_id,
                context_summary=context_summary,
                user_preferences=user_preferences,
                provider=provider,
                model=model
            )
            
            # Método simplificado (sem contexto)
            logger.info(
                "Gerando resposta da IA (método simplificado)",
                user_id=user_id,
                conversation_id=conversation_id,
                provider=provider,
                model=model,
                message_length=len(message),
                context_summary_length=len(context_summary),
                has_user_preferences=user_preferences is not None
            )
            
            # Usa o método simplificado que envia apenas a mensagem
            reply = await self.chat_simple(message)
            
            elapsed_time = time.time() - start_time
            
            if reply:
                # Retorna no formato esperado pelos endpoints que usam este método
                result = {
                    "response": reply,
                    "provider": provider or "default",
                    "model": model or "default"
                }
                
                logger.info(
                    "Resposta gerada com sucesso",
                    user_id=user_id,
                    elapsed_time=f"{elapsed_time:.3f}s",
                    reply_length=len(reply)
                )
                
                return result
            else:
                logger.error(
                    "Erro ao gerar resposta da IA",
                    user_id=user_id,
                    elapsed_time=f"{elapsed_time:.3f}s"
                )
                return None
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Erro inesperado na geração de resposta",
                user_id=user_id,
                elapsed_time=f"{elapsed_time:.3f}s",
                error_type=type(e).__name__,
                error=str(e)
            )
            return None
    
    async def _generate_response_with_context(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[int] = None,
        context_summary: str = "",
        user_preferences: Dict = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Optional[Dict]:
        """Gera resposta da IA enviando contexto completo para /ai/chat ou /ai/generate"""
        start_time = time.time()
        
        try:
            # Prepara dados para envio com contexto
            request_data = {
                "user_id": user_id,
                "message": message
            }
            
            # Adiciona conversation_id se disponível
            if conversation_id:
                request_data["conversation_id"] = conversation_id
            
            # Adiciona context_summary se disponível
            if context_summary:
                request_data["context_summary"] = context_summary
            
            # Adiciona preferências do usuário se disponível
            if user_preferences:
                filtered_preferences = {}
                for k, v in user_preferences.items():
                    if k not in ("user_id", "created_at", "updated_at"):
                        if isinstance(v, datetime):
                            filtered_preferences[k] = v.isoformat()
                        else:
                            filtered_preferences[k] = v
                if filtered_preferences:
                    request_data["user_preferences"] = filtered_preferences
            
            # Adiciona provider e model se disponíveis
            if provider:
                request_data["provider"] = provider
            if model:
                request_data["model"] = model
            
            # Tenta usar /ai/chat primeiro (pode aceitar contexto agora)
            # Se não funcionar, tenta /ai/generate como fallback
            endpoints_to_try = ["/ai/chat", "/ai/generate"]
            
            for endpoint in endpoints_to_try:
                try:
                    logger.debug(f"Tentando endpoint {endpoint} com contexto")
                    response = await self.client.post(endpoint, json=request_data, timeout=self.timeout)
                    
                    if response.status_code == 200:
                        result = response.json()
                        elapsed_time = time.time() - start_time
                        
                        # Extrai resposta (pode ser "reply" ou "response")
                        reply = result.get("reply") or result.get("response", "")
                        
                        logger.info(
                            "Resposta gerada com contexto",
                            user_id=user_id,
                            endpoint=endpoint,
                            elapsed_time=f"{elapsed_time:.3f}s",
                            reply_length=len(reply) if reply else 0
                        )
                        
                        return {
                            "response": reply,
                            "provider": result.get("provider") or provider or "default",
                            "model": result.get("model") or model or "default",
                            "conversation_id": result.get("conversation_id") or conversation_id,
                            "tokens_used": result.get("tokens_used", 0)
                        }
                    elif response.status_code == 404:
                        # Endpoint não existe, tenta próximo
                        logger.debug(f"Endpoint {endpoint} não encontrado, tentando próximo")
                        continue
                    else:
                        logger.warning(f"Erro {response.status_code} no endpoint {endpoint}")
                        continue
                        
                except httpx.TimeoutException:
                    logger.warning(f"Timeout no endpoint {endpoint}, tentando próximo")
                    continue
                except httpx.RequestError:
                    logger.warning(f"Erro de requisição no endpoint {endpoint}, tentando próximo")
                    continue
            
            # Se nenhum endpoint funcionou, fallback para método simples
            logger.warning("Nenhum endpoint com contexto funcionou, usando fallback simples")
            reply = await self.chat_simple(message)
            
            if reply:
                return {
                    "response": reply,
                    "provider": provider or "default",
                    "model": model or "default"
                }
            
            return None
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Erro ao gerar resposta com contexto",
                user_id=user_id,
                elapsed_time=f"{elapsed_time:.3f}s",
                error_type=type(e).__name__,
                error=str(e)
            )
            # Fallback para método simples
            reply = await self.chat_simple(message)
            if reply:
                return {
                    "response": reply,
                    "provider": provider or "default",
                    "model": model or "default"
                }
            return None
    
    # ============================================================================
    # MÉTODO ANTERIOR - COMENTADO PARA SIMPLIFICAÇÃO
    # Método generate_response com requisição completa para /ai/generate
    # Guardado para uso futuro quando necessário
    # ============================================================================
    # async def generate_response_OLD(self, 
    #                               user_id: str,
    #                               message: str,
    #                               conversation_id: Optional[int] = None,
    #                               context_summary: str = "",
    #                               user_preferences: Dict = None,
    #                               provider: Optional[str] = None,
    #                               model: Optional[str] = None) -> Optional[Dict]:
    #     """Gera resposta da IA"""
    #     start_time = time.time()
    #     
    #     try:
    #         # Prepara dados para envio
    #         request_data = {
    #             "user_id": user_id,
    #             "message": message,
    #             "context_summary": context_summary,
    #             "metadata": {
    #                 "source": "chatbot_service",
    #                 "timestamp": datetime.utcnow().isoformat()
    #             }
    #         }
    #         
    #         if conversation_id:
    #             request_data["conversation_id"] = conversation_id
    #         
    #         if user_preferences:
    #             # Remove user_id e campos datetime do user_preferences para evitar duplicação
    #             # já que user_id já está no nível raiz do request_data
    #             filtered_preferences = {}
    #             for k, v in user_preferences.items():
    #                 if k not in ("user_id", "created_at", "updated_at"):
    #                     # Converte datetime para string ISO se houver algum campo datetime restante
    #                     if isinstance(v, datetime):
    #                         filtered_preferences[k] = v.isoformat()
    #                     else:
    #                         filtered_preferences[k] = v
    #             # Só adiciona se houver preferências válidas
    #             if filtered_preferences:
    #                 request_data["user_preferences"] = filtered_preferences
    #         
    #         if provider:
    #             request_data["provider"] = provider
    #         
    #         if model:
    #             request_data["model"] = model
    #         
    #         # URL completa da requisição
    #         url = f"{self.base_url}/ai/generate"
    #         
    #         # Função auxiliar para serializar datetime em JSON
    #         def json_serializer(obj):
    #             """Serializa objetos datetime para string ISO"""
    #             if isinstance(obj, datetime):
    #                 return obj.isoformat()
    #             raise TypeError(f"Tipo {type(obj)} não é serializável")
    #         
    #         # Log detalhado da requisição
    #         try:
    #             request_data_log = json.dumps(request_data, ensure_ascii=False, indent=2, default=json_serializer)
    #         except Exception as e:
    #             request_data_log = f"Erro ao serializar request_data: {str(e)}"
    #         
    #         logger.info(
    #             "Enviando requisição para AI Service",
    #             url=url,
    #             method="POST",
    #             user_id=user_id,
    #             conversation_id=conversation_id,
    #             provider=provider,
    #             model=model,
    #             message_length=len(message),
    #             context_summary_length=len(context_summary),
    #             request_data=request_data_log
    #         )
    #         
    #         # Envia para AI Service
    #         response = await self.client.post("/ai/generate", json=request_data)
    #         
    #         # Tempo de resposta
    #         elapsed_time = time.time() - start_time
    #         
    #         # Log da resposta
    #         if response.status_code == 200:
    #             result = response.json()
    #             logger.info(
    #                 "Resposta gerada com sucesso",
    #                 user_id=user_id,
    #                 status_code=response.status_code,
    #                 elapsed_time=f"{elapsed_time:.3f}s",
    #                 response_size=len(response.text),
    #                 provider=result.get("provider"),
    #                 model=result.get("model"),
    #                 tokens_used=result.get("tokens_used")
    #             )
    #             return result
    #         else:
    #             # Função auxiliar para serializar datetime em JSON
    #             def json_serializer(obj):
    #                 """Serializa objetos datetime para string ISO"""
    #                 if isinstance(obj, datetime):
    #                     return obj.isoformat()
    #                 raise TypeError(f"Tipo {type(obj)} não é serializável")
    #             
    #             try:
    #                 request_data_log = json.dumps(request_data, ensure_ascii=False, indent=2, default=json_serializer)
    #             except Exception as e:
    #                 request_data_log = f"Erro ao serializar request_data: {str(e)}"
    #             
    #             logger.error(
    #                 "Erro ao gerar resposta da IA",
    #                 user_id=user_id,
    #                 status_code=response.status_code,
    #                 elapsed_time=f"{elapsed_time:.3f}s",
    #                 response_text=response.text[:500],  # Limita a 500 caracteres
    #                 url=url,
    #                 request_data=request_data_log
    #             )
    #             return None
    #             
    #     except httpx.TimeoutException as e:
    #         elapsed_time = time.time() - start_time
    #         logger.error(
    #             "Timeout na comunicação com AI Service",
    #             user_id=user_id,
    #             elapsed_time=f"{elapsed_time:.3f}s",
    #             timeout=self.timeout,
    #             url=url if 'url' in locals() else f"{self.base_url}/ai/generate",
    #             error=str(e)
    #         )
    #         return None
    #     except httpx.RequestError as e:
    #         elapsed_time = time.time() - start_time
    #         
    #         # Função auxiliar para serializar datetime em JSON
    #         def json_serializer(obj):
    #             """Serializa objetos datetime para string ISO"""
    #             if isinstance(obj, datetime):
    #                 return obj.isoformat()
    #             raise TypeError(f"Tipo {type(obj)} não é serializável")
    #         
    #         request_data_log = None
    #         if 'request_data' in locals():
    #             try:
    #                 request_data_log = json.dumps(request_data, ensure_ascii=False, indent=2, default=json_serializer)
    #             except Exception as ser_error:
    #                 request_data_log = f"Erro ao serializar request_data: {str(ser_error)}"
    #         
    #         logger.error(
    #             "Erro de requisição para AI Service",
    #             user_id=user_id,
    #             elapsed_time=f"{elapsed_time:.3f}s",
    #             url=url if 'url' in locals() else f"{self.base_url}/ai/generate",
    #             error_type=type(e).__name__,
    #             error=str(e),
    #             request_data=request_data_log
    #         )
    #         return None
    #     except Exception as e:
    #         elapsed_time = time.time() - start_time
    #         
    #         # Função auxiliar para serializar datetime em JSON
    #         def json_serializer(obj):
    #             """Serializa objetos datetime para string ISO"""
    #             if isinstance(obj, datetime):
    #                 return obj.isoformat()
    #             raise TypeError(f"Tipo {type(obj)} não é serializável")
    #         
    #         request_data_log = None
    #         if 'request_data' in locals():
    #             try:
    #                 request_data_log = json.dumps(request_data, ensure_ascii=False, indent=2, default=json_serializer)
    #             except Exception as ser_error:
    #                 request_data_log = f"Erro ao serializar request_data: {str(ser_error)}"
    #         
    #         logger.error(
    #             "Erro inesperado na comunicação com AI Service",
    #             user_id=user_id,
    #             elapsed_time=f"{elapsed_time:.3f}s",
    #             error_type=type(e).__name__,
    #             error=str(e),
    #             url=url if 'url' in locals() else f"{self.base_url}/ai/generate",
    #             request_data=request_data_log
    #         )
    #         return None
    
    async def generate_streaming_response(self,
                                        user_id: str,
                                        message: str,
                                        conversation_id: Optional[int] = None,
                                        context_summary: str = "",
                                        user_preferences: Dict = None,
                                        provider: Optional[str] = None,
                                        model: Optional[str] = None):
        """Gera resposta em streaming da IA"""
        try:
            # Prepara dados para envio
            request_data = {
                "user_id": user_id,
                "message": message,
                "context_summary": context_summary,
                "metadata": {
                    "source": "chatbot_service",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            if conversation_id:
                request_data["conversation_id"] = conversation_id
            
            if user_preferences:
                # Remove user_id e campos datetime do user_preferences para evitar duplicação
                # já que user_id já está no nível raiz do request_data
                filtered_preferences = {}
                for k, v in user_preferences.items():
                    if k not in ("user_id", "created_at", "updated_at"):
                        # Converte datetime para string ISO se houver algum campo datetime restante
                        if isinstance(v, datetime):
                            filtered_preferences[k] = v.isoformat()
                        else:
                            filtered_preferences[k] = v
                # Só adiciona se houver preferências válidas
                if filtered_preferences:
                    request_data["user_preferences"] = filtered_preferences
            
            if provider:
                request_data["provider"] = provider
            
            if model:
                request_data["model"] = model
            
            # Envia para AI Service com streaming
            async with self.client.stream("POST", "/ai/generate/stream", json=request_data) as response:
                if response.status_code == 200:
                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            yield chunk
                else:
                    logger.error(f"Erro no streaming: {response.status_code}")
                    yield json.dumps({"error": "Erro na geração de resposta"})
                    
        except Exception as e:
            logger.error(f"Erro no streaming com AI Service: {e}")
            yield json.dumps({"error": "Erro na comunicação"})
    
    async def get_usage_metrics(self, user_id: str, period: str = "daily") -> Optional[Dict]:
        """Busca métricas de uso do usuário"""
        try:
            response = await self.client.get(f"/ai/usage/{user_id}?period={period}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao buscar métricas: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Erro na comunicação com AI Service: {e}")
            return None
    
    async def chat_simple(self, message: str) -> Optional[str]:
        """
        Método simplificado para chat - envia apenas a mensagem para o AI Service.
        Retorna apenas a resposta (reply) da IA.
        
        Este método faz uma requisição simplificada para /ai/chat do AI Service
        com apenas {"message": "..."} e retorna o campo "reply" da resposta.
        """
        start_time = time.time()
        url = f"{self.base_url}/ai/chat"
        
        try:
            # Requisição simplificada - apenas a mensagem
            request_data = {
                "message": message
            }
            
            logger.info(
                "Enviando requisição simplificada para AI Service",
                url=url,
                method="POST",
                message_length=len(message)
            )
            
            response = await self.client.post("/ai/chat", json=request_data)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                reply = result.get("reply", "")
                
                logger.info(
                    "Resposta recebida com sucesso",
                    status_code=response.status_code,
                    elapsed_time=f"{elapsed_time:.3f}s",
                    reply_length=len(reply) if reply else 0
                )
                
                return reply
            else:
                logger.error(
                    "Erro ao obter resposta do AI Service",
                    status_code=response.status_code,
                    elapsed_time=f"{elapsed_time:.3f}s",
                    response_text=response.text[:500] if response.text else None,
                    url=url
                )
                return None
                
        except httpx.TimeoutException as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Timeout na comunicação com AI Service",
                elapsed_time=f"{elapsed_time:.3f}s",
                timeout=self.timeout,
                url=url,
                error=str(e)
            )
            return None
        except httpx.RequestError as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Erro de requisição para AI Service",
                elapsed_time=f"{elapsed_time:.3f}s",
                url=url,
                error_type=type(e).__name__,
                error=str(e)
            )
            return None
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Erro inesperado na comunicação com AI Service",
                elapsed_time=f"{elapsed_time:.3f}s",
                error_type=type(e).__name__,
                error=str(e),
                url=url
            )
            return None
    
    async def validate_ai_connection(self) -> bool:
        """Valida conexão com AI Service"""
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                logger.info("Conexão com AI Service validada")
                return True
            else:
                logger.error(f"AI Service não está saudável: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erro ao validar conexão com AI Service: {e}")
            return False
    
    async def check_user_limits(self, user_id: str) -> Dict[str, Any]:
        """Verifica limites do usuário antes de chamar IA"""
        start_time = time.time()
        
        try:
            logger.info(
                "Verificando limites do usuário",
                user_id=user_id
            )
            
            # Busca assinatura do usuário
            subscription = await self.get_user_subscription(user_id)
            if not subscription:
                elapsed_time = time.time() - start_time
                logger.warning(
                    "Usuário sem assinatura ativa - bloqueando requisição",
                    user_id=user_id,
                    elapsed_time=f"{elapsed_time:.3f}s",
                    can_proceed=False,
                    reason="Usuário sem assinatura ativa"
                )
                return {
                    "can_proceed": False,
                    "reason": "Usuário sem assinatura ativa",
                    "limits": None
                }
            
            # Busca métricas de uso
            usage = await self.get_usage_metrics(user_id, "daily")
            
            # Verifica limites
            limits = subscription.get("usage_limits", {})
            current_usage = usage.get("current_usage", {}) if usage else {}
            
            # Verifica se pode fazer mais chamadas
            daily_requests = limits.get("daily_requests", 0)
            current_requests = current_usage.get("total_requests", 0)
            
            elapsed_time = time.time() - start_time
            
            if daily_requests > 0 and current_requests >= daily_requests:
                logger.warning(
                    "Limite diário de requisições atingido",
                    user_id=user_id,
                    elapsed_time=f"{elapsed_time:.3f}s",
                    daily_requests=daily_requests,
                    current_requests=current_requests,
                    can_proceed=False,
                    reason="Limite diário de requisições atingido"
                )
                return {
                    "can_proceed": False,
                    "reason": "Limite diário de requisições atingido",
                    "limits": {
                        "daily_requests": daily_requests,
                        "current_requests": current_requests
                    }
                }
            
            remaining = daily_requests - current_requests if daily_requests > 0 else -1
            logger.info(
                "Limites verificados - usuário pode prosseguir",
                user_id=user_id,
                elapsed_time=f"{elapsed_time:.3f}s",
                daily_requests=daily_requests,
                current_requests=current_requests,
                remaining=remaining,
                can_proceed=True
            )
            
            return {
                "can_proceed": True,
                "reason": "Limites OK",
                "limits": {
                    "daily_requests": daily_requests,
                    "current_requests": current_requests,
                    "remaining": remaining
                }
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Erro ao verificar limites do usuário",
                user_id=user_id,
                elapsed_time=f"{elapsed_time:.3f}s",
                error_type=type(e).__name__,
                error=str(e),
                can_proceed=False,
                reason="Erro ao verificar limites"
            )
            return {
                "can_proceed": False,
                "reason": "Erro ao verificar limites",
                "limits": None
            }


# Instância global do serviço de integração
ai_integration = AIServiceIntegration()
