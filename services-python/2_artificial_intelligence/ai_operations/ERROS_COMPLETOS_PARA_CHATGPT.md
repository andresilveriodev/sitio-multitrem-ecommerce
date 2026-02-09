# 🐛 ERROS COMPLETOS - GPT-4.1-nano não funciona via API

## 📋 PROBLEMA PRINCIPAL

O modelo `gpt-4.1-nano` **FUNCIONA quando chamado diretamente**, mas **retorna erro 500** quando chamado via API REST.

## ✅ O QUE FUNCIONA

### Teste 1: Serviço Direto ✅
```python
from services.ai_service import ai_service
import asyncio

result = asyncio.run(ai_service.generate_response(
    messages=[{"role": "user", "content": "OK"}],
    provider="openai",
    model="gpt-4.1-nano",
    max_tokens=10,
    temperature=1.0
))
# Resultado: "OK" ✅
```

### Teste 2: Biblioteca OpenAI Direta ✅
```python
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4.1-nano",
    messages=[{"role": "user", "content": "teste"}],
    max_tokens=10,
    temperature=1.0
)
# Resultado: Funciona perfeitamente ✅
```

## ❌ O QUE NÃO FUNCIONA

### Requisição HTTP que falha:
```bash
POST http://localhost:8012/ai/generate
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "teste"
    }
  ],
  "provider": "openai",
  "model": "gpt-4.1-nano",
  "max_tokens": 50,
  "temperature": 1.0
}
```

**Resposta:**
```
Status: 500
Content-Type: text/plain; charset=utf-8
Body: "Internal Server Error"
```

**Observação**: A resposta é genérica, não mostra detalhes do erro.

## 🔍 CÓDIGO RELEVANTE

### 1. Endpoint que está falhando (`app/routers/ai_resource.py`):

```python
@router.post("/generate", response_model=AIResponse)
async def generate_ai_response(request: AIRequest):
    """
    Gera uma resposta usando o provedor de IA especificado
    """
    try:
        provider = request.provider or DEFAULT_AI_PROVIDER
        
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(
                status_code=400, 
                detail=f"Provedor '{provider}' não suportado."
            )
        
        # Converte mensagens
        messages = []
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Gera resposta usando o provedor especificado
        response = await ai_service.generate_response(
            messages=messages,
            provider=provider,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return AIResponse(
            response=response,
            provider=provider,
            model=request.model or ai_service.get_default_model(provider),
            usage={"total_tokens": len(response.split())}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Erro ao gerar resposta da IA: {error_msg}")
        logger.error(f"Tipo do erro: {error_type}")
        logger.error(f"Traceback completo: {error_trace}")
        error_detail = f"Erro: {error_msg} (Tipo: {error_type})\n\nTraceback:\n{error_trace[:800]}"
        raise HTTPException(status_code=500, detail=error_detail)
```

### 2. Serviço de IA (`services/ai_service.py`):

```python
async def _generate_openai_response(self, messages: List[Dict[str, str]], model: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    """Gera resposta usando OpenAI"""
    if not self.openai_client:
        raise Exception("OpenAI API key não configurada")
    
    logger.info(f"Chamando OpenAI com modelo: {model}, messages: {messages}")
    
    # Para modelos gpt-5 e gpt-4.1-nano, usar max_completion_tokens e temperature=1
    # Tenta primeiro com max_completion_tokens, se falhar, usa max_tokens
    if "gpt-5" in model.lower() or "gpt-4.1-nano" in model.lower():
        logger.info(f"Usando configuração para gpt-5/gpt-4.1-nano: max_completion_tokens={max_tokens}, temperature=1.0")
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=max_tokens,
                temperature=1.0
            )
        except TypeError:
            # Se max_completion_tokens não for suportado, tenta com max_tokens
            logger.info(f"max_completion_tokens não suportado, usando max_tokens")
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=1.0
            )
    else:
        logger.info(f"Usando configuração padrão: max_tokens={max_tokens}, temperature={temperature}")
        # Tenta primeiro com max_tokens, se falhar, tenta max_completion_tokens
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
        except Exception as e:
            # Se max_tokens não for suportado, tenta com max_completion_tokens
            if "max_tokens" in str(e).lower() or "unsupported" in str(e).lower():
                logger.info(f"max_tokens não suportado para este modelo, tentando max_completion_tokens")
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                raise
    
    content = response.choices[0].message.content
    
    # Garante que sempre retorna uma string
    if content is None:
        logger.warning("Resposta vazia da OpenAI, retornando string vazia")
        return ""
    
    return content
```

### 3. Middleware de Tracking (`middleware/tracking_middleware.py`):

```python
class AITrackingMiddleware(BaseHTTPMiddleware):
    """Middleware para capturar automaticamente métricas de requisições de IA"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Verificar se é um endpoint que deve ser rastreado
        if not self._should_track(request):
            return await call_next(request)
        
        # ... código de tracking ...
        
        try:
            # Processar requisição
            response = await call_next(request)
            # ... processar resposta ...
            return response
            
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
                    logger.error(f"Erro ao marcar transação como falha: {track_error}")
            
            logger.error(f"Erro no middleware de tracking: {e}")
            logger.error(f"Tipo do erro: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
```

## 🔧 MUDANÇAS REALIZADAS

1. **Corrigido `max_completion_tokens`**: Adicionado fallback para `max_tokens`
2. **Melhorado tratamento de erros**: Adicionado logging detalhado
3. **Adicionado tratamento de resposta vazia**: Garantido que sempre retorna string

## 📊 INFORMAÇÕES TÉCNICAS

- **Python**: 3.13
- **FastAPI**: 0.111.1
- **OpenAI**: 1.0.1
- **Uvicorn**: 0.29.0
- **Porta**: 8012
- **Modelo padrão**: `gpt-4o-mini`
- **Provider padrão**: `openai`

## 🎯 OBSERVAÇÕES IMPORTANTES

1. **O serviço funciona quando chamado diretamente** - Isso indica que o problema está na integração FastAPI/API REST, não no código do serviço.

2. **A resposta de erro é genérica** - O erro 500 não mostra detalhes, mesmo com logging detalhado implementado. Isso sugere que:
   - O erro está sendo capturado antes de chegar ao router
   - Há um handler de exceções global que está mascarando o erro
   - O Socket.IO pode estar interferindo

3. **Logs não mostram erros** - Os logs da aplicação não mostram mensagens de erro específicas, mesmo com logging implementado.

4. **Middleware pode estar interferindo** - O `AITrackingMiddleware` está ativo e pode estar capturando/transformando o erro.

## 🔍 POSSÍVEIS CAUSAS

1. **Erro no middleware de tracking** - Pode estar capturando o erro e não propagando corretamente
2. **Problema com Socket.IO** - A aplicação usa `socketio.ASGIApp` que pode estar interferindo
3. **Handler de exceções global** - Pode haver um handler que está mascarando o erro
4. **Problema de serialização** - O erro pode estar ocorrendo durante a serialização da resposta

## 📝 ARQUIVOS CRIADOS PARA DEBUG

- `erros_log.txt` - Últimos 200 linhas do log da aplicação
- `erro_api_detalhado.txt` - Resposta completa da API com erro
- `teste_direto_sucesso.txt` - Teste direto que funciona

## 🚨 ERRO ESPECÍFICO

**Requisição:**
```json
POST /ai/generate
{
  "messages": [{"role": "user", "content": "teste"}],
  "provider": "openai",
  "model": "gpt-4.1-nano",
  "max_tokens": 50,
  "temperature": 1.0
}
```

**Resposta:**
```
HTTP/1.1 500 Internal Server Error
Content-Type: text/plain; charset=utf-8
Content-Length: 21

Internal Server Error
```

**Observação**: Não há detalhes do erro na resposta, mesmo com tratamento de exceções implementado.

---

**PERGUNTA PARA O CHATGPT:**

Por que o modelo `gpt-4.1-nano` funciona quando chamado diretamente através do serviço Python, mas retorna erro 500 genérico quando chamado via API REST FastAPI? O código de tratamento de erros está implementado, mas a resposta não mostra detalhes do erro. O que pode estar causando isso?





