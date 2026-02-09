from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
from services.ai_service import ai_service
from services.subscription_service import subscription_service
from app.config import SUPPORTED_PROVIDERS, DEFAULT_AI_PROVIDER
from app.db import get_db
from sqlalchemy.orm import Session
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

# Schemas Pydantic
class AIMessage(BaseModel):
    role: str  # user, assistant, system
    content: str

class AIRequest(BaseModel):
    messages: List[AIMessage]
    provider: Optional[str] = None  # openai, deepseek, ollama
    model: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7

class AIResponse(BaseModel):
    response: str
    provider: str
    model: str
    usage: Dict = {}

class AIStreamRequest(BaseModel):
    messages: List[AIMessage]
    provider: Optional[str] = None  # openai, deepseek, ollama
    model: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7

class ProviderInfo(BaseModel):
    name: str
    available: bool
    models: List[str]
    description: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# Request format do serviço externo (chatbot service)
class ExternalAIRequest(BaseModel):
    user_id: Optional[str] = None
    message: str
    context_summary: Optional[str] = None
    metadata: Optional[Dict] = None
    user_preferences: Optional[Dict] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

@router.post("/test-nano")
async def test_nano():
    """
    Endpoint de teste mínimo para gpt-4.1-nano
    SEM middleware, SEM tracking, SEM response_model
    """
    print("=" * 60)
    print("CHEGOU NO /ai/test-nano")
    print("=" * 60)
    
    try:
        from services.ai_service_simple import ai_service_simple
        
        print("[*] Chamando ai_service_simple.send...")
        result = await ai_service_simple.send(
            user_message="teste",
            model="gpt-4.1-nano",
            max_tokens=50,
            temperature=0.7
        )
        
        print(f"[OK] Sucesso! Resultado: {result}")
        return {"ok": True, "result": result, "model": "gpt-4.1-nano"}
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERRO] Falhou: {e}")
        print(f"Traceback: {error_trace}")
        return {
            "ok": False,
            "error": str(e),
            "type": type(e).__name__,
            "traceback": error_trace
        }

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Endpoint simples de chat
    """
    reply = await ai_service.send(req.message)
    return ChatResponse(reply=reply)

@router.post("/chat-simple", response_model=ChatResponse)
async def chat_simple(req: ChatRequest):
    """
    Endpoint simples de chat usando o service simplificado
    """
    print("=" * 60)
    print("CHEGOU NO /ai/chat-simple")
    print(f"Message: {req.message}")
    print("=" * 60)
    
    try:
        from services.ai_service_simple import ai_service_simple
        
        print("[*] Chamando ai_service_simple.send...")
        reply = await ai_service_simple.send(
            user_message=req.message,
            model="gpt-4o-mini",
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"[OK] Resposta: {reply[:100] if reply else 'VAZIA'}")
        return ChatResponse(reply=reply)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERRO] Falhou: {e}")
        print(f"Traceback: {error_trace}")
        logger.error(f"Erro no chat-simple: {e}")
        logger.error(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro: {str(e)} (Tipo: {type(e).__name__})"
        )

@router.post("/test-nano-old")
async def test_nano_old():
    """
    Endpoint de teste com o serviço antigo (para comparação)
    """
    print("=" * 60)
    print("CHEGOU NO /ai/test-nano-old")
    print("=" * 60)
    
    try:
        from services.ai_service import ai_service
        
        print("[*] Chamando ai_service.generate_response...")
        result = await ai_service.generate_response(
            messages=[{"role": "user", "content": "teste"}],
            provider="openai",
            model="gpt-4.1-nano",
            max_tokens=50,
            temperature=1.0
        )
        
        print(f"[OK] Sucesso! Resultado: {result}")
        return {"ok": True, "result": result, "model": "gpt-4.1-nano"}
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERRO] Falhou: {e}")
        print(f"Traceback: {error_trace}")
        return {
            "ok": False,
            "error": str(e),
            "type": type(e).__name__,
            "traceback": error_trace
        }

@router.post("/generate", response_model=AIResponse)
async def generate_ai_response(request: Request):
    """
    Gera uma resposta usando o provedor de IA especificado (OpenAI, DeepSeek ou Ollama)
    Aceita dois formatos:
    1. Formato padrão: {messages: [...], provider, model, ...}
    2. Formato externo: {message: "...", user_id, ...}
    """
    print("=" * 60)
    print("CHEGOU NO /ai/generate")
    
    try:
        # Lê o body da requisição
        try:
            body = await request.json()
            print(f"[*] Body recebido: {json.dumps(body, indent=2)[:200]}...")
        except Exception as e:
            print(f"[ERRO] Erro ao ler body: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=400, detail=f"Erro ao ler body da requisição: {str(e)}")
        
        # Detecta qual formato foi enviado
        if "message" in body and "messages" not in body:
            # Formato EXTERNO (chatbot service)
            print("[*] Formato EXTERNO detectado (message)")
            print(f"Message: {body.get('message', '')[:50]}...")
            print(f"User ID: {body.get('user_id')}")
            print(f"Model: {body.get('model')}")
            print(f"Provider: {body.get('provider')}")
            
            # Converte para formato padrão
            messages = [{"role": "user", "content": body.get("message", "")}]
            provider = body.get("provider") or DEFAULT_AI_PROVIDER
            model = body.get("model")
            max_tokens = body.get("max_tokens") or 1000
            temperature = body.get("temperature") or 0.7
        else:
            # Formato PADRÃO (messages array)
            print("[*] Formato PADRAO detectado (messages)")
            print(f"Model: {body.get('model')}")
            print(f"Provider: {body.get('provider')}")
            
            messages = []
            for msg in body.get("messages", []):
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            provider = body.get("provider") or DEFAULT_AI_PROVIDER
            model = body.get("model")
            max_tokens = body.get("max_tokens", 1000)
            temperature = body.get("temperature", 0.7)
        
        print("=" * 60)
        
        # Valida se o provedor é suportado
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=400, 
                detail=f"Provedor '{provider}' não suportado. Provedores disponíveis: {', '.join(SUPPORTED_PROVIDERS)}"
            )
        
        print(f"[*] Provider definido: {provider}")
        print(f"[*] Mensagens convertidas: {len(messages)} mensagens")
        
        # Gera resposta usando o provedor especificado
        print(f"[*] Chamando ai_service.generate_response...")
        response = await ai_service.generate_response(
            messages=messages,
            provider=provider,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        print(f"[OK] Resposta recebida: {response[:100] if response else 'VAZIA'}")
        
        # Verifica se response é string
        if not isinstance(response, str):
            print(f"[ERRO] Response não é string! Tipo: {type(response)}")
            response = str(response) if response else ""
        
        model_name = model or ai_service.get_default_model(provider)
        print(f"[*] Modelo usado: {model_name}")
        
        result = AIResponse(
            response=response,
            provider=provider,
            model=model_name,
            usage={"total_tokens": len(response.split())}
        )
        print(f"[OK] AIResponse criado com sucesso")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"[ERRO] Erro capturado no endpoint:")
        print(f"  Tipo: {error_type}")
        print(f"  Mensagem: {error_msg}")
        print(f"  Traceback: {error_trace}")
        
        logger.error(f"Erro ao gerar resposta da IA: {error_msg}")
        logger.error(f"Tipo do erro: {error_type}")
        logger.error(f"Traceback completo: {error_trace}")
        # Retorna o erro como string para debug
        error_detail = f"Erro: {error_msg} (Tipo: {error_type})\n\nTraceback:\n{error_trace[:800]}"
        raise HTTPException(status_code=500, detail=error_detail)

@router.post("/generate/stream")
async def generate_ai_response_stream(request: AIStreamRequest):
    """
    Gera uma resposta em streaming usando o provedor de IA especificado (OpenAI, DeepSeek ou Ollama)
    """
    try:
        # Define o provedor (usa o padrão se não especificado)
        provider = request.provider or DEFAULT_AI_PROVIDER
        
        # Valida se o provedor é suportado
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=400, 
                detail=f"Provedor '{provider}' não suportado. Provedores disponíveis: {', '.join(SUPPORTED_PROVIDERS)}"
            )
        
        # Converte mensagens para formato da API
        messages = []
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        async def generate():
            try:
                async for chunk in ai_service.generate_streaming_response(
                    messages=messages,
                    provider=provider,
                    model=request.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                ):
                    # Formato Server-Sent Events
                    yield f"data: {json.dumps({'content': chunk, 'provider': provider})}\n\n"
                
                # Sinal de fim do stream
                yield f"data: {json.dumps({'content': '[DONE]'})}\n\n"
            
            except Exception as e:
                logger.error(f"Erro no streaming: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    except Exception as e:
        logger.error(f"Erro ao iniciar streaming da IA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers")
def get_available_providers():
    """
    Retorna os provedores de IA disponíveis e seus modelos
    """
    providers = []
    
    for provider in SUPPORTED_PROVIDERS:
        try:
            models = ai_service.get_available_models(provider)
            providers.append(ProviderInfo(
                name=provider,
                available=True,
                models=models,
                description=ai_service.get_provider_description(provider)
            ).dict())
        except Exception as e:
            logger.warning(f"Provedor {provider} não disponível: {str(e)}")
            providers.append(ProviderInfo(
                name=provider,
                available=False,
                models=[],
                description=f"Erro: {str(e)}"
            ).dict())
    
    return {
        "providers": providers,
        "default_provider": DEFAULT_AI_PROVIDER,
        "supported_providers": SUPPORTED_PROVIDERS
    }

@router.get("/models")
def get_available_models(provider: Optional[str] = Query(None, description="Provedor específico (openai, deepseek, ollama)")):
    """
    Retorna os modelos disponíveis para um provedor específico ou todos
    """
    if provider:
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Provedor '{provider}' não suportado. Provedores disponíveis: {', '.join(SUPPORTED_PROVIDERS)}"
            )
        
        try:
            models = ai_service.get_available_models(provider)
            return {
                "provider": provider,
                "models": models,
                "default_model": ai_service.get_default_model(provider)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter modelos do provedor {provider}: {str(e)}")
    
    # Retorna modelos de todos os provedores
    all_models = {}
    for prov in SUPPORTED_PROVIDERS:
        try:
            all_models[prov] = {
                "models": ai_service.get_available_models(prov),
                "default_model": ai_service.get_default_model(prov)
            }
        except Exception as e:
            all_models[prov] = {
                "models": [],
                "default_model": None,
                "error": str(e)
            }
    
    return {
        "providers": all_models,
        "default_provider": DEFAULT_AI_PROVIDER
    }

@router.get("/health")
def health_check():
    """
    Endpoint de verificação de saúde do serviço de IA
    """
    return {
        "status": "healthy",
        "service": "ai",
        "model": ai_service.model
    }

@router.post("/validate")
async def validate_ai_connection():
    """
    Valida a conexão com a API da OpenAI
    """
    try:
        test_messages = [
            {"role": "user", "content": "Hello, this is a test message."}
        ]
        
        response = await ai_service.generate_response(test_messages)
        
        return {
            "status": "connected",
            "model": ai_service.model,
            "test_response": response[:100] + "..." if len(response) > 100 else response
        }
    
    except Exception as e:
        logger.error(f"Erro na validação da IA: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/user-subscription/{user_id}")
async def get_user_subscription(user_id: str, db: Session = Depends(get_db)):
    """
    Obtém a assinatura ativa do usuário
    Aceita user_id como UUID (string)
    """
    print("=" * 80)
    print(f"[AI_RESOURCE] GET /ai/user-subscription/{user_id}")
    print("=" * 80)
    
    try:
        print(f"[*] Buscando assinatura para user_id={user_id}")
        
        subscription = subscription_service.get_user_subscription(db, user_id)
        
        if not subscription:
            print(f"[AVISO] Assinatura não encontrada para user_id={user_id}")
            logger.warning(f"Assinatura não encontrada para usuário {user_id}")
            raise HTTPException(status_code=404, detail="Assinatura não encontrada")
        
        print(f"[OK] Assinatura encontrada: status={subscription.status}")
        print(f"  Subscription ID: {subscription.subscription_id}")
        print(f"  Status: {subscription.status}")
        print("=" * 80)
        
        return subscription.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        error_type = type(e).__name__
        
        print(f"[ERRO] Erro ao buscar assinatura:")
        print(f"  Tipo: {error_type}")
        print(f"  Mensagem: {error_msg}")
        print(f"  Traceback: {error_trace}")
        print("=" * 80)
        
        logger.error(f"Erro ao buscar assinatura do usuário {user_id}: {error_msg}")
        logger.error(f"Tipo: {error_type}")
        logger.error(f"Traceback: {error_trace}")
        
        raise HTTPException(status_code=500, detail=f"Erro ao buscar assinatura: {error_msg}")