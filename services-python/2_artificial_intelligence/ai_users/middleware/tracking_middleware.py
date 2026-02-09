"""Middleware para tracking automático de transações e métricas de uso"""

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Any, Optional
import time
import json
import logging
from services.transaction_service import TransactionService
from services.alert_service import alert_service
from models.transaction import AITransaction
from app.db import get_db
import asyncio
from io import StringIO
import re

logger = logging.getLogger(__name__)

class AITrackingMiddleware(BaseHTTPMiddleware):
    """Middleware para capturar automaticamente métricas de requisições de IA"""
    
    def __init__(self, app, track_endpoints: list = None):
        super().__init__(app)
        # Endpoints que devem ser rastreados
        self.track_endpoints = track_endpoints or [
            '/ai/generate',
            '/ai/generate/stream'
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Verificar se é um endpoint que deve ser rastreado
        if not self._should_track(request):
            return await call_next(request)
        
        # Capturar dados da requisição
        start_time = time.time()
        request_data = await self._extract_request_data(request)
        
        # Extrair informações da requisição
        user_id = self._extract_user_id(request)
        conversation_id = self._extract_conversation_id(request_data)
        provider = request_data.get('provider', 'unknown')
        model = request_data.get('model', 'unknown')
        endpoint = str(request.url.path)
        
        # Verificar limites do usuário antes de processar
        if user_id:
            try:
                logger.info(f"[MIDDLEWARE] Verificando limites para user_id={user_id}")
                try:
                    db = next(get_db())
                    should_block, reason = alert_service.should_block_request(user_id, db)
                    db.close()
                    
                    logger.info(f"[MIDDLEWARE] Resultado da verificação: should_block={should_block}, reason={reason}")
                    
                    if should_block:
                        logger.warning(f"[MIDDLEWARE] BLOQUEANDO requisição do user_id={user_id}: {reason}")
                        from fastapi import HTTPException
                        raise HTTPException(
                            status_code=429,
                            detail={
                                "error": "Limite de uso excedido",
                                "reason": reason,
                                "user_id": user_id
                            }
                        )
                except StopIteration:
                    # get_db() não retornou um gerador válido, pular verificação
                    logger.warning(f"[MIDDLEWARE] Não foi possível obter conexão com DB, pulando verificação de limites")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"[MIDDLEWARE] ERRO ao verificar limites do usuário {user_id}: {e}")
                logger.error(f"[MIDDLEWARE] Tipo do erro: {type(e).__name__}")
                import traceback
                logger.error(f"[MIDDLEWARE] Traceback: {traceback.format_exc()}")
                # Continuar processamento mesmo com erro na verificação de limites
        
        transaction = None
        
        try:
            # Criar transação (com tratamento de erro para não quebrar a requisição)
            if user_id:
                try:
                    transaction = TransactionService.create_transaction(
                        user_id=user_id,
                        conversation_id=conversation_id,
                        provider=provider,
                        model=model,
                        request_data=request_data,
                        endpoint=endpoint
                    )
                except Exception as e:
                    logger.warning(f"[MIDDLEWARE] Erro ao criar transação: {e}")
                    # Continua sem transação, não quebra a requisição
            
            # Processar requisição
            response = await call_next(request)
            
            # Calcular tempo de resposta
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Processar resposta baseado no tipo
            if isinstance(response, StreamingResponse):
                # Para streaming, precisamos interceptar o conteúdo
                response = await self._handle_streaming_response(
                    response, transaction, response_time_ms
                )
            else:
                # Para resposta normal
                await self._handle_normal_response(
                    response, transaction, response_time_ms
                )
            
            return response
            
        except HTTPException as http_ex:
            # Re-raise HTTPException para manter o status code e detalhes
            logger.error(f"[MIDDLEWARE] HTTPException capturada: status={http_ex.status_code}, detail={http_ex.detail}")
            raise
        except Exception as e:
            # Marcar transação como falha
            if transaction:
                try:
                    TransactionService.fail_transaction(
                        transaction.id,
                        str(e),
                        error_code=getattr(e, 'code', None)
                    )
                except Exception as track_error:
                    logger.error(f"[MIDDLEWARE] Erro ao marcar transação como falha: {track_error}")
            
            logger.error(f"[MIDDLEWARE] ERRO no middleware de tracking: {e}")
            logger.error(f"[MIDDLEWARE] Tipo do erro: {type(e).__name__}")
            logger.error(f"[MIDDLEWARE] Endpoint: {endpoint}")
            logger.error(f"[MIDDLEWARE] User ID: {user_id}")
            logger.error(f"[MIDDLEWARE] Provider: {provider}, Model: {model}")
            import traceback
            logger.error(f"[MIDDLEWARE] Traceback completo: {traceback.format_exc()}")
            # Re-raise a exceção para que o FastAPI possa tratá-la
            raise
    
    def _should_track(self, request: Request) -> bool:
        """Verifica se a requisição deve ser rastreada"""
        return any(request.url.path.startswith(endpoint) for endpoint in self.track_endpoints)
    
    async def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        """Extrai dados da requisição"""
        try:
            # Ler o corpo da requisição
            body = await request.body()
            
            if body:
                request_data = json.loads(body.decode('utf-8'))
            else:
                request_data = {}
            
            # Adicionar parâmetros da query
            request_data.update(dict(request.query_params))
            
            # Recriar o corpo da requisição para que possa ser lido novamente
            async def receive():
                return {"type": "http.request", "body": body}
            
            request._receive = receive
            
            return request_data
            
        except Exception as e:
            logger.warning(f"Erro ao extrair dados da requisição: {e}")
            return {}
    
    def _extract_user_id(self, request: Request) -> Optional[int]:
        """Extrai ID do usuário da requisição"""
        try:
            # Tentar extrair do header Authorization ou de outros lugares
            # Por enquanto, usar um usuário padrão para testes
            return 1  # TODO: Implementar extração real do usuário
        except Exception as e:
            logger.warning(f"Erro ao extrair user_id: {e}")
            return None
    
    def _extract_conversation_id(self, request_data: Dict[str, Any]) -> Optional[int]:
        """Extrai ID da conversa dos dados da requisição"""
        return request_data.get('conversation_id')
    
    async def _handle_normal_response(
        self,
        response: Response,
        transaction: Optional[AITransaction],
        response_time_ms: int
    ):
        """Processa resposta normal (não streaming)"""
        if not transaction:
            return
        
        try:
            # Ler conteúdo da resposta de forma segura
            response_data = {}
            try:
                if hasattr(response, 'body') and response.body:
                    body_str = response.body.decode('utf-8') if isinstance(response.body, bytes) else str(response.body)
                    if body_str:
                        response_data = json.loads(body_str)
            except (json.JSONDecodeError, AttributeError, UnicodeDecodeError) as e:
                logger.warning(f"Erro ao ler body da resposta no middleware: {e}")
                response_data = {}
            
            # Extrair métricas de tokens da resposta
            usage = response_data.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
            
            # Completar transação
            try:
                TransactionService.complete_transaction(
                    transaction.id,
                    response_data=response_data,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens
                )
            except Exception as e:
                logger.warning(f"Erro ao completar transação no middleware: {e}")
            
            # Atualizar tempo de resposta
            try:
                from app.db import Session as DBSession
                db = DBSession()
                try:
                    db_transaction = db.query(AITransaction).filter(AITransaction.id == transaction.id).first()
                    if db_transaction:
                        db_transaction.response_time_ms = response_time_ms
                        db.commit()
                finally:
                    db.close()
            except Exception as e:
                logger.warning(f"Erro ao atualizar tempo de resposta no middleware: {e}")
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta normal: {e}")
            # Não falha a transação aqui para não quebrar a resposta
            # Apenas loga o erro
    
    async def _handle_streaming_response(
        self,
        response: StreamingResponse,
        transaction: Optional[AITransaction],
        response_time_ms: int
    ) -> StreamingResponse:
        """Processa resposta de streaming"""
        if not transaction:
            return response
        
        # Variáveis para acumular dados do stream
        accumulated_content = []
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        
        async def track_streaming_generator():
            nonlocal total_tokens, prompt_tokens, completion_tokens
            
            try:
                async for chunk in response.body_iterator:
                    # Enviar chunk para o cliente
                    yield chunk
                    
                    # Processar chunk para extrair métricas
                    try:
                        chunk_str = chunk.decode('utf-8') if isinstance(chunk, bytes) else str(chunk)
                        
                        # Tentar extrair dados JSON do chunk
                        if chunk_str.startswith('data: '):
                            json_str = chunk_str[6:].strip()
                            if json_str and json_str != '[DONE]':
                                chunk_data = json.loads(json_str)
                                
                                # Extrair conteúdo
                                if 'choices' in chunk_data:
                                    for choice in chunk_data['choices']:
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            content = choice['delta']['content']
                                            if content:
                                                accumulated_content.append(content)
                                
                                # Extrair métricas de uso se disponível
                                if 'usage' in chunk_data:
                                    usage = chunk_data['usage']
                                    prompt_tokens = usage.get('prompt_tokens', prompt_tokens)
                                    completion_tokens = usage.get('completion_tokens', completion_tokens)
                                    total_tokens = usage.get('total_tokens', total_tokens)
                    
                    except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
                        # Ignorar erros de parsing, continuar processando
                        pass
                
                # Após o streaming terminar, completar a transação
                if not total_tokens and accumulated_content:
                    # Estimar tokens se não fornecido
                    content_text = ''.join(accumulated_content)
                    completion_tokens = max(1, len(content_text) // 4)  # Estimativa aproximada
                    total_tokens = completion_tokens
                
                response_data = {
                    'content': ''.join(accumulated_content),
                    'streaming': True,
                    'chunks_count': len(accumulated_content)
                }
                
                TransactionService.complete_transaction(
                    transaction.id,
                    response_data=response_data,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens
                )
                
                # Atualizar tempo de resposta
                from app.db import Session as DBSession
                db = DBSession()
                try:
                    db_transaction = db.query(AITransaction).filter(AITransaction.id == transaction.id).first()
                    if db_transaction:
                        db_transaction.response_time_ms = response_time_ms
                        db.commit()
                finally:
                    db.close()
                
            except Exception as e:
                logger.error(f"Erro no streaming tracking: {e}")
                if transaction:
                    TransactionService.fail_transaction(
                        transaction.id,
                        f"Erro no streaming: {str(e)}"
                    )
        
        # Retornar nova resposta de streaming com tracking
        return StreamingResponse(
            track_streaming_generator(),
            media_type=response.media_type,
            headers=response.headers
        )