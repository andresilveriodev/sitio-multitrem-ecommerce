"""
Router para processamento de mensagens do chat
"""

import uuid
import time
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
import structlog

from models.conversation_context import Message, MessageType
from services.cache_service import cache_service
from services.context_service import context_service
from services.ai_integration import ai_integration
from services.filters.message_filters import message_filters
from services.filters.intent_classifier import Intent, intent_classifier
from services.filters.intent_router import intent_router
from services.filters.rate_limiter import rate_limiter
from services.security import input_validator, ValidationLevel
from services.commands import CommandAnalyzer, CommandExecutor, CommandRequest

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chat"])

# Instâncias dos serviços de comando
command_analyzer = CommandAnalyzer()
command_executor = CommandExecutor()


# Funções auxiliares
def _convert_user_preferences_to_dict(user_preferences) -> Optional[Dict]:
    """Converte user_preferences para dict, removendo campos desnecessários"""
    if not user_preferences:
        return None
    
    try:
        # Tenta usar .dict() primeiro (Pydantic v1), depois .model_dump() (Pydantic v2)
        if hasattr(user_preferences, 'dict'):
            prefs_dict = user_preferences.dict(exclude={'created_at', 'updated_at', 'user_id'})
        elif hasattr(user_preferences, 'model_dump'):
            prefs_dict = user_preferences.model_dump(exclude={'created_at', 'updated_at', 'user_id'})
        else:
            # Fallback: se for dict, remove campos desnecessários
            if isinstance(user_preferences, dict):
                prefs_dict = {k: v for k, v in user_preferences.items() 
                            if k not in ('created_at', 'updated_at', 'user_id')}
            else:
                return None
        
        # Garante que qualquer datetime restante seja convertido para string ISO
        if prefs_dict:
            for key, value in list(prefs_dict.items()):
                if isinstance(value, datetime):
                    prefs_dict[key] = value.isoformat()
        
        return prefs_dict if prefs_dict else None
    except Exception as e:
        logger.warning(f"Erro ao converter user_preferences para dict: {e}", exc_info=True)
        return None


class ChatRequest:
    """Request para processamento de mensagem"""
    def __init__(self, user_id: str, message: str, session_id: Optional[str] = None, content_type: str = "text/plain"):
        self.user_id = user_id
        self.message = message
        self.session_id = session_id
        self.content_type = content_type


async def get_chat_request(request: Request) -> ChatRequest:
    """Extrai dados da requisição"""
    body = await request.json()
    return ChatRequest(
        user_id=body.get("user_id"),
        message=body.get("message"),
        session_id=body.get("session_id"),
        content_type=body.get("content_type", "text/plain")
    )


async def get_chat_request_with_context(request: Request) -> tuple:
    """
    Extrai dados da requisição incluindo contexto de investimentos
    Retorna (ChatRequest, context_dict)
    """
    body = await request.json()
    chat_request = ChatRequest(
        user_id=body.get("user_id"),
        message=body.get("message"),
        session_id=body.get("session_id"),
        content_type=body.get("content_type", "text/plain")
    )
    context = body.get("context")  # Contexto opcional do frontend
    return chat_request, context


@router.post("/process-message")
async def process_message(request: Request):
    """Processa mensagem do usuário com validação de segurança e contexto opcional do frontend"""
    start_time = time.time()
    
    try:
        # Extrai dados da requisição (incluindo contexto opcional do frontend)
        body = await request.json()
        chat_request = ChatRequest(
            user_id=body.get("user_id"),
            message=body.get("message"),
            session_id=body.get("session_id"),
            content_type=body.get("content_type", "text/plain")
        )
        frontend_context = body.get("context")  # Contexto opcional do frontend
        
        # Validação básica
        if not chat_request.user_id or not chat_request.message:
            raise HTTPException(status_code=400, detail="user_id e message são obrigatórios")
        
        # VALIDAÇÃO DE SEGURANÇA - Gate 0
        security_validation = input_validator.validate_message(
            user_id=chat_request.user_id,
            message=chat_request.message,
            content_type=chat_request.content_type
        )
        
        if not security_validation.is_valid:
            # Retorna erro apropriado baseado no nível de validação
            if security_validation.level == ValidationLevel.REJECT:
                status_code = 400
                if "RATE_LIMIT_EXCEEDED" in str(security_validation.details):
                    status_code = 429
                elif "CONTENT_MODERATION" in str(security_validation.details):
                    status_code = 451
                elif "TOKEN_LIMIT_EXCEEDED" in str(security_validation.details):
                    status_code = 413
                
                raise HTTPException(
                    status_code=status_code,
                    detail=security_validation.message
                )
            else:
                # Para warnings, continua mas registra
                logger.warning(f"Validação com warning: {security_validation.message}")
        
        # Usar conteúdo sanitizado se disponível
        sanitized_message = security_validation.sanitized_content or chat_request.message
        
        # ============================================================
        # FIREWALL DE CONVERSA - Pipeline de Filtros
        # ============================================================
        
        # 1. RATE LIMITING (Anti-Spam)
        from services.filters.rate_limiter import rate_limiter
        from services.classification_logger import classification_logger
        
        rate_allowed, rate_reason = rate_limiter.check_rate_limit(
            chat_request.user_id,
            sanitized_message
        )
        
        if not rate_allowed:
            return {
                "success": False,
                "error": rate_reason,
                "response": None,
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "requires_ai": False,
                    "cache_hit": False,
                    "rate_limited": True,
                    "security_validation": security_validation.details
                }
            }
        
        # 2. NORMALIZAÇÃO
        normalized = intent_classifier.normalize_message(sanitized_message)
        
        # 3. CLASSIFICAÇÃO DE INTENTS (sem IA - barato)
        intent, intent_metadata = intent_classifier.classify_intent(sanitized_message)
        score = intent_metadata.get("score", 0)
        rules_hit = intent_metadata.get("rules_hit", [])
        
        logger.info(
            "Intent classificado",
            user_id=chat_request.user_id,
            intent=intent.value,
            score=score,
            rules_hit_count=len(rules_hit)
        )
        
        # 4. ROTEAMENTO BASEADO EM INTENT
        logger.info(
            "Roteando intent",
            intent=intent.value,
            method=intent_metadata.get("method", "unknown"),
            metadata_keys=list(intent_metadata.keys())
        )
        
        routing_result = await intent_router.route(
            intent,
            sanitized_message,
            intent_metadata,
            chat_request.user_id
        )
        
        decision = routing_result.get("decision", "ALLOW_AI")
        requires_ai = routing_result.get("requires_ai", False)
        router_response = routing_result.get("response")
        
        logger.info(
            "Roteamento concluído",
            decision=decision,
            requires_ai=requires_ai,
            has_response=bool(router_response)
        )
        
        # 5. LOG DE CLASSIFICAÇÃO (para auditoria e melhoria)
        conversation_id = chat_request.session_id or f"conv_{chat_request.user_id}"
        await classification_logger.log_classification(
            conversation_id=conversation_id,
            inbound_message_id=None,  # Pode ser obtido do request
            message=sanitized_message,
            intent=intent.value,
            score=score,
            rules_hit=rules_hit,
            decision=decision,
            requires_ai=requires_ai,
            user_id=chat_request.user_id
        )
        
        # 6. PROCESSAMENTO BASEADO NA DECISÃO
        
        # DECISÃO: BLOCK (DANGEROUS/ABUSE)
        if decision == "BLOCK":
            return {
                "success": False,
                "error": router_response or "Mensagem bloqueada",
                "response": None,
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "requires_ai": False,
                    "cache_hit": False,
                    "intent": intent.value,
                    "blocked": True,
                    "security_validation": security_validation.details
                }
            }
        
        # DECISÃO: NO_AI_TEMPLATE (OFFTOPIC, UNKNOWN, SUPPORT, etc)
        if decision == "NO_AI_TEMPLATE":
            # Se não tem resposta do router, usa escape do classifier
            if not router_response:
                router_response = intent_classifier.get_escape_response(intent)
            
            if router_response:
            response_data = {
                "response": router_response,
                "confidence": intent_metadata.get("confidence", 0.8),
                "category": f"intent_{intent.value.lower()}"
            }
            
            # Cache da resposta
            context_hash = await _get_context_hash(chat_request.user_id)
            await cache_service.cache_response(
                chat_request.user_id,
                sanitized_message,
                response_data,
                context_hash,
                ttl=3600  # 1 hora
            )
            
            logger.info(
                "Resposta de template enviada (sem IA)",
                user_id=chat_request.user_id,
                intent=intent.value,
                decision=decision
            )
            
            return {
                "success": True,
                "response": response_data,
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "requires_ai": False,  # NÃO chama IA
                    "cache_hit": False,
                    "intent": intent.value,
                    "decision": decision,
                    "score": score,
                    "security_validation": security_validation.details
                }
            }
        
        # DECISÃO: ASK_CLARIFY (UNKNOWN)
        if decision == "ASK_CLARIFY" and router_response:
            response_data = {
                "response": router_response,
                "confidence": 0.5,
                "category": "clarification_needed"
            }
            
            return {
                "success": True,
                "response": response_data,
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "requires_ai": False,
                    "cache_hit": False,
                    "intent": intent.value,
                    "decision": decision,
                    "security_validation": security_validation.details
                }
            }
        
        # DECISÃO: ALLOW_AI (continua para processamento com IA)
        # Verifica cache antes de chamar IA
        context_hash = await _get_context_hash(chat_request.user_id)
        cached_response = await cache_service.get_cached_response(
            chat_request.user_id, 
            sanitized_message, 
            context_hash
        )
        
        if cached_response:
            logger.info(f"Cache hit para usuário {chat_request.user_id}")
            return {
                "success": True,
                "response": cached_response["response"],
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "requires_ai": False,
                    "cache_hit": True,
                    "cached_at": cached_response.get("cached_at"),
                    "intent": intent.value,
                    "security_validation": security_validation.details
                }
            }
        
        # Se chegou aqui, a decisão foi ALLOW_AI
        # Continua para processamento com IA (apenas se realmente necessário)
        if not requires_ai:
            # Se o roteador disse que não precisa de IA, mas chegou aqui,
            # algo deu errado - retorna resposta padrão
            logger.warning(
                "Decisão ALLOW_AI mas requires_ai=False - usando fallback",
                user_id=chat_request.user_id,
                intent=intent.value
            )
            return {
                "success": True,
                "response": {
                    "response": "Não entendi completamente. Você quer fazer um pedido ou ver o cardápio? Digite *cardapio* ou *pedido*.",
                    "confidence": 0.5
                },
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "requires_ai": False,
                    "cache_hit": False,
                    "intent": intent.value,
                    "decision": "FALLBACK",
                    "security_validation": security_validation.details
                }
            }
        
        # Verifica se a mensagem é um comando do e-commerce
        # Permissões padrão para usuário anônimo/teste (pode ser ajustado)
        user_permissions = ["view_orders", "view_products", "view_cart", 
                          "create_order", "modify_cart", "view_history"]
        
        try:
            command_analysis = await command_analyzer.analyze_message(
                sanitized_message,
                user_permissions
            )
            
            if command_analysis.is_command and command_analysis.confidence > 0.5:
                logger.info(f"Comando detectado: {command_analysis.command_id} (confiança: {command_analysis.confidence})")
                
                # Criar requisição de comando
                command_request = CommandRequest(
                    command_id=command_analysis.command_id,
                    parameters=command_analysis.parameters,
                    user_id=chat_request.user_id
                )
                
                # Executar comando
                success, message, result, confirmation = await command_executor.execute_command(
                    command_request,
                    user_permissions
                )
                
                if success:
                    if confirmation:
                        # Comando precisa de confirmação
                        response_data = {
                            "response": f"{message}. Confirmação necessária.",
                            "command_id": command_analysis.command_id,
                            "confirmation_required": True,
                            "confirmation": {
                                "id": confirmation.execution_id,
                                "message": confirmation.message,
                                "command": confirmation.command.id,
                                "parameters": confirmation.parameters
                            },
                            # Flag para o frontend processar confirmação
                            "frontend_action": {
                                "type": "await_confirmation",
                                "command_id": confirmation.command.id,
                                "confirmation_id": confirmation.execution_id,
                                "parameters": confirmation.parameters
                            }
                        }
                    else:
                        # Comando executado com sucesso - formatar para frontend executar ação
                        command_result_data = result.data if result else {}
                        frontend_action_type = command_result_data.get("action") if command_result_data else None
                        
                        # Se o comando retornou uma ação para o frontend, incluir metadados
                        if frontend_action_type and command_result_data.get("target") == "frontend":
                            # Extrair parâmetros excluindo campos internos
                            frontend_params = {
                                k: v for k, v in command_result_data.items() 
                                if k not in ["action", "target"]
                            }
                            
                            response_data = {
                                "response": result.message if result else message,
                                "command_id": command_analysis.command_id,
                                "command_result": command_result_data,
                                "action": "command_executed",
                                # Flag estruturada para o frontend executar a ação
                                "frontend_action": {
                                    "type": frontend_action_type,
                                    "parameters": frontend_params,
                                    "command_id": command_analysis.command_id
                                }
                            }
                        else:
                            # Comando sem ação específica para frontend (apenas resposta)
                            response_data = {
                                "response": result.message if result else message,
                                "command_id": command_analysis.command_id,
                                "command_result": command_result_data,
                                "action": "command_executed"
                            }
                    
                    # Adiciona mensagem ao contexto
                    await _add_message_to_context(chat_request, False, "command", sanitized_message)
                    
                    return {
                        "success": True,
                        "response": response_data,
                        "metadata": {
                            "processing_time": time.time() - start_time,
                            "requires_ai": False,
                            "cache_hit": False,
                            "command_executed": True,
                            "command_id": command_analysis.command_id,
                            "security_validation": security_validation.details
                        }
                    }
                else:
                    # Comando falhou na validação ou execução
                    logger.warning(f"Comando falhou: {message}")
                    # Continua para processar com IA como fallback
                    pass
        except Exception as e:
            logger.error(f"Erro ao analisar/executar comando: {e}", exc_info=True)
            # Continua para processar com IA como fallback
            pass
        
        # Continua para processamento com IA (já validado pelo firewall de intents acima)
        
        # VALIDAÇÃO DE ASSINATURA DESABILITADA TEMPORARIAMENTE
        # Verifica limites do usuário
        # limits_check = await ai_integration.check_user_limits(chat_request.user_id)
        # if not limits_check["can_proceed"]:
        #     return {
        #         "success": False,
        #         "error": limits_check["reason"],
        #         "response": None,
        #         "metadata": {
        #             "processing_time": time.time() - start_time,
        #             "requires_ai": True,
        #             "cache_hit": False,
        #             "limits": limits_check["limits"],
        #             "security_validation": security_validation.details
        #         }
        #     }
        
        # Busca contexto da conversa
        context = await context_service.get_conversation_context(chat_request.user_id)
        
        # Busca preferências do usuário (opcional)
        user_preferences = await context_service.get_user_preferences(chat_request.user_id)
        user_preferences_dict = _convert_user_preferences_to_dict(user_preferences)
        
        # Atualiza conversation_metadata com contexto do frontend (se houver)
        if frontend_context:
            if frontend_context.get("current_plan_id"):
                context.conversation_metadata["current_plan_id"] = frontend_context.get("current_plan_id")
            if frontend_context.get("current_periodo_id"):
                context.conversation_metadata["current_periodo_id"] = frontend_context.get("current_periodo_id")
            await context_service.save_conversation_context(context)
        
        # Gera resposta da IA (usando mensagem sanitizada)
        ai_response = await ai_integration.generate_response(
            user_id=chat_request.user_id,
            message=sanitized_message,
            conversation_id=context.conversation_metadata.get("conversation_id"),
            context_summary=context.context_summary,
            user_preferences=user_preferences_dict
        )
        
        if not ai_response:
            return {
                "success": False,
                "error": "Erro ao gerar resposta da IA",
                "response": None,
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "requires_ai": True,
                    "cache_hit": False,
                    "security_validation": security_validation.details
                }
            }
        
        # Adiciona mensagem ao contexto
        await _add_message_to_context(chat_request, True, ai_response.get("provider"), sanitized_message)
        
        # Verifica se a resposta tem o campo 'response'
        if "response" not in ai_response:
            logger.error(
                "Resposta da IA não contém campo 'response'",
                user_id=chat_request.user_id,
                ai_response_keys=list(ai_response.keys()) if isinstance(ai_response, dict) else None,
                ai_response=ai_response
            )
            return {
                "success": False,
                "error": "Resposta da IA em formato inválido",
                "response": None,
                "metadata": {
                    "processing_time": time.time() - start_time,
                    "requires_ai": True,
                    "cache_hit": False,
                    "security_validation": security_validation.details
                }
            }
        
        # Retornar resposta normal da IA
        # Cache da resposta
        response_data = {
            "response": ai_response.get("response", ""),
            "provider": ai_response.get("provider"),
            "conversation_id": ai_response.get("conversation_id"),
            "tokens_used": ai_response.get("tokens_used", 0)
        }
        
        await cache_service.cache_response(
            chat_request.user_id,
            sanitized_message,
            response_data,
            context_hash,
            ttl=1800  # 30 minutos
        )
        
        return {
            "success": True,
            "response": response_data,
            "metadata": {
                "processing_time": time.time() - start_time,
                "requires_ai": True,
                "cache_hit": False,
                "intent": intent.value,
                "score": score,
                "decision": decision,
                "security_validation": security_validation.details
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")


@router.post("/process-message/stream")
async def process_message_stream(chat_request: ChatRequest = Depends(get_chat_request)):
    """Processa mensagem em streaming com validação de segurança"""
    
    async def generate_stream():
        try:
            # Validação básica
            if not chat_request.user_id or not chat_request.message:
                yield f"data: {_format_sse_error('user_id e message são obrigatórios')}\n\n"
                return
            
            # VALIDAÇÃO DE SEGURANÇA
            security_validation = input_validator.validate_message(
                user_id=chat_request.user_id,
                message=chat_request.message,
                content_type=chat_request.content_type
            )
            
            if not security_validation.is_valid:
                yield f"data: {_format_sse_error(security_validation.message)}\n\n"
                return
            
            # Usar conteúdo sanitizado
            sanitized_message = security_validation.sanitized_content or chat_request.message
            
            # FIREWALL DE CONVERSA (mesmo pipeline do endpoint não-streaming)
            # Rate limiting
            rate_allowed, rate_reason = rate_limiter.check_rate_limit(
                chat_request.user_id,
                sanitized_message
            )
            if not rate_allowed:
                yield f"data: {_format_sse_error(rate_reason)}\n\n"
                return
            
            # Classificação de intents
            intent, intent_metadata = intent_classifier.classify_intent(sanitized_message)
            routing_result = await intent_router.route(
                intent,
                sanitized_message,
                intent_metadata,
                chat_request.user_id
            )
            
            decision = routing_result.get("decision", "ALLOW_AI")
            requires_ai = routing_result.get("requires_ai", False)
            router_response = routing_result.get("response")
            
            # Se não precisa de IA, retorna resposta de template
            if decision in ["NO_AI_TEMPLATE", "ASK_CLARIFY"] and router_response:
                yield f"data: {_format_sse_response(router_response, {'category': f'intent_{intent.value.lower()}'})}\n\n"
                return
            
            # Se bloqueado, retorna erro
            if decision == "BLOCK":
                yield f"data: {_format_sse_error(router_response or 'Mensagem bloqueada')}\n\n"
                return
            
            # VALIDAÇÃO DE ASSINATURA DESABILITADA TEMPORARIAMENTE
            # Verifica limites do usuário
            # limits_check = await ai_integration.check_user_limits(chat_request.user_id)
            # if not limits_check["can_proceed"]:
            #     yield f"data: {_format_sse_error(limits_check['reason'])}\n\n"
            #     return
            
            # Busca contexto e preferências
            context = await context_service.get_conversation_context(chat_request.user_id)
            user_preferences = await context_service.get_user_preferences(chat_request.user_id)
            user_preferences_dict = _convert_user_preferences_to_dict(user_preferences)
            
            # Streaming da resposta da IA
            async for chunk in ai_integration.generate_streaming_response(
                user_id=chat_request.user_id,
                message=sanitized_message,
                conversation_id=context.conversation_metadata.get("conversation_id"),
                context_summary=context.context_summary,
                user_preferences=user_preferences_dict
            ):
                yield f"data: {chunk}\n\n"
            
            # Adiciona mensagem ao contexto
            await _add_message_to_context(chat_request, True, "streaming", sanitized_message)
            
        except Exception as e:
            logger.error(f"Erro no streaming: {e}")
            yield f"data: {_format_sse_error('Erro interno do servidor')}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.post("/validate-input")
async def validate_input(request: Request):
    """Endpoint para validar entrada sem processar"""
    try:
        body = await request.json()
        user_id = body.get("user_id")
        message = body.get("message")
        content_type = body.get("content_type", "text/plain")
        
        if not user_id or not message:
            raise HTTPException(status_code=400, detail="user_id e message são obrigatórios")
        
        # Validação completa
        validation_result = input_validator.validate_message(
            user_id=user_id,
            message=message,
            content_type=content_type
        )
        
        return {
            "success": validation_result.is_valid,
            "validation": {
                "is_valid": validation_result.is_valid,
                "level": validation_result.level.value,
                "message": validation_result.message,
                "details": validation_result.details,
                "sanitized_content": validation_result.sanitized_content
            }
        }
        
    except Exception as e:
        logger.error(f"Erro na validação: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/conversation/{user_id}")
async def get_conversation_context(user_id: str):
    """Busca contexto da conversa do usuário"""
    try:
        context = await context_service.get_conversation_context(user_id)
        # Converte context para dict de forma segura
        context_dict = None
        if context:
            try:
                if hasattr(context, 'dict'):
                    context_dict = context.dict()
                elif hasattr(context, 'model_dump'):
                    context_dict = context.model_dump()
                else:
                    context_dict = context if isinstance(context, dict) else None
            except Exception as e:
                logger.warning(f"Erro ao converter context para dict: {e}", exc_info=True)
                context_dict = None
        
        return {
            "success": True,
            "context": context_dict or {},
            "message_count": len(context.message_history) if context else 0
        }
    except Exception as e:
        logger.error(f"Erro ao buscar contexto: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")


@router.post("/update-context")
async def update_context(request: Request):
    """Atualiza contexto da conversa"""
    try:
        body = await request.json()
        user_id = body.get("user_id")
        summary = body.get("summary")
        
        if not user_id or not summary:
            raise HTTPException(status_code=400, detail="user_id e summary são obrigatórios")
        
        success = await context_service.update_context_summary(user_id, summary)
        
        return {
            "success": success,
            "message": "Contexto atualizado com sucesso" if success else "Erro ao atualizar contexto"
        }
    except Exception as e:
        logger.error(f"Erro ao atualizar contexto: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/chat")
async def chat(request: Request):
    """Endpoint simplificado para chat com suporte a provider e model"""
    try:
        body = await request.json()
        conversation_id = body.get("conversation_id")
        message = body.get("message")
        provider = body.get("provider")
        model = body.get("model")
        
        # Validação básica
        if not conversation_id or not message:
            raise HTTPException(
                status_code=400, 
                detail="conversation_id e message são obrigatórios"
            )
        
        # Usa user_id padrão baseado no conversation_id se não fornecido
        # Em produção, você pode querer buscar o user_id do conversation_id
        user_id = body.get("user_id", f"user_{conversation_id}")
        
        # Busca contexto da conversa
        context = await context_service.get_conversation_context(user_id)
        
        # Busca preferências do usuário (opcional)
        user_preferences = await context_service.get_user_preferences(user_id)
        user_preferences_dict = _convert_user_preferences_to_dict(user_preferences)
        
        # Gera resposta da IA com provider e model opcionais
        ai_response = await ai_integration.generate_response(
            user_id=user_id,
            message=message,
            conversation_id=conversation_id,
            context_summary=context.context_summary,
            user_preferences=user_preferences_dict,
            provider=provider,
            model=model
        )
        
        if not ai_response:
            raise HTTPException(
                status_code=500,
                detail="Erro ao gerar resposta da IA"
            )
        
        # Retorna resposta no formato esperado
        return {
            "user_message": message,
            "ai_response": ai_response.get("response", ""),
            "conversation_id": conversation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no endpoint /chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# Funções auxiliares
async def _get_context_hash(user_id: str) -> str:
    """Gera hash do contexto atual"""
    context = await context_service.get_conversation_context(user_id)
    return str(hash(context.context_summary + str(len(context.message_history))))


async def _add_message_to_context(chat_request: ChatRequest, requires_ai: bool, provider: Optional[str], sanitized_message: str = None):
    """Adiciona mensagem ao contexto"""
    try:
        message = Message(
            id=str(uuid.uuid4()),
            user_id=chat_request.user_id,
            content=sanitized_message or chat_request.message,
            timestamp=datetime.utcnow(),
            message_type=MessageType.USER,
            requires_ai=requires_ai,
            ai_provider_used=provider
        )
        
        await context_service.add_message_to_context(chat_request.user_id, message)
    except Exception as e:
        logger.error(f"Erro ao adicionar mensagem ao contexto: {e}")


def _format_sse_response(response: str, metadata: Dict = None) -> str:
    """Formata resposta para SSE"""
    data = {
        "type": "response",
        "content": response,
        "metadata": metadata or {}
    }
    return f"data: {data}"


def _format_sse_error(error: str) -> str:
    """Formata erro para SSE"""
    data = {
        "type": "error",
        "content": error
    }
    return f"data: {data}"
