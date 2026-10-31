from openai import OpenAI
import httpx
import json
import re
from typing import List, Dict, Optional, AsyncGenerator
import logging
from app.config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    DEFAULT_AI_PROVIDER, SUPPORTED_PROVIDERS
)

logger = logging.getLogger(__name__)


class FalhaExtracao(Exception):
    """Mensagem segura para quem chamou. O detalhe técnico fica no log."""


def _sem_segredo(texto: str) -> str:
    limpo = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "sk-…", texto or "")
    return limpo[:500]


def _validar_pedidos(parsed: object) -> None:
    if not isinstance(parsed, dict) or set(parsed) != {"pedidos"}:
        raise FalhaExtracao("A resposta da extração não veio no formato esperado.")
    pedidos = parsed.get("pedidos")
    if not isinstance(pedidos, list):
        raise FalhaExtracao("A resposta da extração não veio no formato esperado.")
    for pedido in pedidos:
        if not isinstance(pedido, dict) or set(pedido) != {"data", "itens"}:
            raise FalhaExtracao("A resposta da extração não veio no formato esperado.")
        if not isinstance(pedido.get("data"), str) or not isinstance(pedido.get("itens"), list):
            raise FalhaExtracao("A resposta da extração não veio no formato esperado.")
        for item in pedido["itens"]:
            if not isinstance(item, dict) or set(item) != {"produto", "qtd", "tipo", "observacao"}:
                raise FalhaExtracao("A resposta da extração não veio no formato esperado.")
            qtd = item.get("qtd")
            if isinstance(qtd, bool) or not isinstance(qtd, int):
                raise FalhaExtracao("A resposta da extração não veio no formato esperado.")
            if not all(isinstance(item.get(campo), str) for campo in ("produto", "tipo", "observacao")):
                raise FalhaExtracao("A resposta da extração não veio no formato esperado.")


def _texto_pedidos_validados(response) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        logger.info("Extração sem choices")
        raise FalhaExtracao("A resposta da extração veio incompleta.")
    choice = choices[0]
    finish = getattr(choice, "finish_reason", None)
    message = choice.message
    if getattr(message, "refusal", None):
        logger.info("OpenAI recusou a extração")
        raise FalhaExtracao("A OpenAI não concluiu a extração.")
    content = message.content or ""
    parsed = None
    if str(content).strip():
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = None
    if parsed is not None:
        _validar_pedidos(parsed)
        return json.dumps(parsed, ensure_ascii=False)
    logger.info("Extração sem JSON utilizável finish=%s chars=%s", finish, len(str(content)))
    if finish == "length" or not str(content).strip():
        raise FalhaExtracao("A resposta da extração veio incompleta.")
    raise FalhaExtracao("A resposta da extração não veio no formato esperado.")

class AIService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.deepseek_client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        ) if DEEPSEEK_API_KEY else None
    
    async def send(
        self,
        message: str,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        response_schema: Optional[Dict] = None,
    ) -> str:
        """
        Método simples para enviar mensagem e receber resposta
        Usa o provider padrão (openai)
        """
        messages = [{"role": "user", "content": message}]
        return await self.generate_response(
            messages=messages,
            provider="openai",
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            response_schema=response_schema,
        )
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        response_schema: Optional[Dict] = None,
    ) -> str:
        """
        Gera uma resposta usando o provedor de IA especificado
        
        Args:
            messages: Lista de mensagens no formato [{'role': 'user/assistant/system', 'content': 'texto'}]
            provider: Provedor de IA ('openai', 'deepseek', 'ollama')
            model: Modelo específico a ser usado
        
        Returns:
            str: Resposta gerada pela IA
        """
        provider = provider or DEFAULT_AI_PROVIDER
        model = model or (OPENAI_MODEL if provider == "openai" else None)
        
        # Log para GPT-4.1-nano
        is_gpt41nano = model and "gpt-4.1-nano" in model.lower()
        if is_gpt41nano:
            print("\n" + "=" * 80)
            print("📡 AI_SERVICE.generate_response - GPT-4.1-NANO")
            print("=" * 80)
            print(f"Provider: {provider}")
            print(f"Model: {model}")
            print(f"Max Tokens: {max_tokens}")
            print(f"Temperature: {temperature}")
            print("=" * 80 + "\n")
        
        if provider not in SUPPORTED_PROVIDERS:
            error_msg = f"Provedor '{provider}' não suportado. Use: {SUPPORTED_PROVIDERS}"
            if is_gpt41nano:
                print(f"[ERRO] {error_msg}")
            raise ValueError(error_msg)
        
        try:
            if provider == "openai":
                result = await self._generate_openai_response(
                    messages, model or OPENAI_MODEL, max_tokens, temperature, response_schema
                )
                if is_gpt41nano:
                    print(f"\n[OK] AI_SERVICE.generate_response concluído com sucesso!")
                return result
            elif provider == "deepseek":
                return await self._generate_deepseek_response(messages, model or DEEPSEEK_MODEL, max_tokens, temperature)
            elif provider == "ollama":
                return await self._generate_ollama_response(messages, model or OLLAMA_MODEL)
        
        except FalhaExtracao:
            raise
        except Exception as e:
            logger.error("Erro ao gerar resposta da IA (%s): %s", provider, _sem_segredo(str(e)))
            if response_schema:
                raise FalhaExtracao("Falha interna ao consultar a IA.") from e
            raise Exception(f"Erro na comunicação com a IA ({provider})") from e
    
    async def _generate_openai_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        response_schema: Optional[Dict] = None,
    ) -> str:
        """Gera resposta usando OpenAI - Versão simplificada que funciona"""
        if not self.openai_client:
            raise Exception("OpenAI API key não configurada")
        
        # Logs detalhados para GPT-4.1-nano
        is_gpt41nano = "gpt-4.1-nano" in model.lower()
        
        if is_gpt41nano:
            print("=" * 80)
            print("🚀 REQUISIÇÃO GPT-4.1-NANO")
            print("=" * 80)
            print(f"Model: {model}")
            print(f"Max Tokens: {max_tokens}")
            print(f"Temperature: {temperature}")
            print(f"Messages Count: {len(messages)}")
            for i, msg in enumerate(messages):
                print(f"  Message {i+1}: role={msg.get('role')}, content={msg.get('content', '')[:50]}...")
            print("-" * 80)
        
        logger.info(
            "Chamando OpenAI modelo=%s mensagens=%s chars=%s schema=%s",
            model,
            len(messages),
            sum(len(str(item.get("content") or "")) for item in messages),
            bool(response_schema),
        )

        try:
            if is_gpt41nano:
                print("[*] Enviando requisição para OpenAI...")

            pedido = {"model": model, "messages": messages}
            if "gpt-5" in model.lower():
                # O teto inclui o raciocínio interno. Sem folga, o JSON volta vazio.
                pedido["max_completion_tokens"] = max(max_tokens, 8000) if response_schema else max_tokens
                if response_schema:
                    pedido["reasoning_effort"] = "minimal"
            else:
                pedido["max_tokens"] = max_tokens
                pedido["temperature"] = temperature
            if response_schema:
                pedido["response_format"] = {"type": "json_schema", "json_schema": response_schema}
            response = self.openai_client.chat.completions.create(**pedido)
            
            if is_gpt41nano:
                print("[OK] Requisição bem-sucedida!")
                
        except Exception as e:
            if is_gpt41nano:
                print(f"[ERRO] Falha na requisição GPT-4.1-nano:")
                print(f"  Tipo: {type(e).__name__}")
                print(f"  Mensagem: {str(e)}")
                import traceback
                print(f"  Traceback: {traceback.format_exc()}")
            logger.error("Erro ao chamar OpenAI: %s", _sem_segredo(str(e)))
            if response_schema:
                raise FalhaExtracao("A OpenAI não concluiu a extração.") from e
            raise
        
        if response_schema:
            return _texto_pedidos_validados(response)

        # Extrair conteúdo da resposta
        content = response.choices[0].message.content
        
        if is_gpt41nano:
            print("-" * 80)
            print("✅ RESPOSTA RECEBIDA:")
            print(f"  Conteúdo: {content[:200] if content else 'VAZIA'}...")
            print(f"  Tamanho: {len(content) if content else 0} caracteres")
            if hasattr(response, 'usage'):
                usage = response.usage
                print(f"  Tokens usados: {usage.total_tokens if hasattr(usage, 'total_tokens') else 'N/A'}")
            print("=" * 80)
        
        logger.info(f"Resposta recebida da OpenAI: '{content}' (tamanho: {len(content) if content else 0})")
        
        # Garante que sempre retorna uma string
        if content is None:
            if is_gpt41nano:
                print("[AVISO] Resposta vazia da OpenAI!")
            logger.warning("Resposta vazia da OpenAI, retornando string vazia")
            return ""
        
        return content
    
    async def _generate_deepseek_response(self, messages: List[Dict[str, str]], model: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Gera resposta usando DeepSeek"""
        if not self.deepseek_client:
            raise Exception("DeepSeek API key não configurada")
        
        response = self.deepseek_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    async def _generate_ollama_response(self, messages: List[Dict[str, str]], model: str) -> str:
        """Gera resposta usando Ollama"""
        async with httpx.AsyncClient() as client:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Erro Ollama: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("message", {}).get("content", "")
    
    async def generate_streaming_response(
        self, 
        messages: List[Dict[str, str]], 
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Gera uma resposta em streaming usando o provedor de IA especificado
        
        Args:
            messages: Lista de mensagens no formato [{'role': 'user/assistant/system', 'content': 'texto'}]
            provider: Provedor de IA ('openai', 'deepseek', 'ollama')
            model: Modelo específico a ser usado
        
        Yields:
            str: Chunks da resposta gerada pela IA
        """
        provider = provider or DEFAULT_AI_PROVIDER
        
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Provedor '{provider}' não suportado. Use: {SUPPORTED_PROVIDERS}")
        
        try:
            if provider == "openai":
                async for chunk in self._stream_openai_response(messages, model or OPENAI_MODEL):
                    yield chunk
            elif provider == "deepseek":
                async for chunk in self._stream_deepseek_response(messages, model or DEEPSEEK_MODEL):
                    yield chunk
            elif provider == "ollama":
                async for chunk in self._stream_ollama_response(messages, model or OLLAMA_MODEL):
                    yield chunk
        
        except Exception as e:
            logger.error(f"Erro ao gerar resposta em streaming da IA ({provider}): {str(e)}")
            raise Exception(f"Erro na comunicação com a IA ({provider}): {str(e)}")
    
    async def _stream_openai_response(self, messages: List[Dict[str, str]], model: str) -> AsyncGenerator[str, None]:
        """Stream resposta usando OpenAI - Versão simplificada"""
        if not self.openai_client:
            raise Exception("OpenAI API key não configurada")
        
        # Usa a mesma lógica simples - apenas max_tokens
        stream = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _stream_deepseek_response(self, messages: List[Dict[str, str]], model: str) -> AsyncGenerator[str, None]:
        """Stream resposta usando DeepSeek"""
        if not self.deepseek_client:
            raise Exception("DeepSeek API key não configurada")
        
        stream = self.deepseek_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _stream_ollama_response(self, messages: List[Dict[str, str]], model: str) -> AsyncGenerator[str, None]:
        """Stream resposta usando Ollama"""
        async with httpx.AsyncClient() as client:
            payload = {
                "model": model,
                "messages": messages,
                "stream": True
            }
            
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=60.0
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"Erro Ollama: {response.status_code}")
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
    
    def get_available_providers(self) -> List[str]:
        """Retorna lista de provedores disponíveis baseado nas configurações"""
        available = []
        
        if self.openai_client:
            available.append("openai")
        if self.deepseek_client:
            available.append("deepseek")
        # Ollama sempre disponível se configurado
        if OLLAMA_BASE_URL:
            available.append("ollama")
        
        return available
    
    def get_available_models(self, provider: str) -> List[str]:
        """Retorna lista de modelos disponíveis para um provedor"""
        if provider == "openai":
            return ["gpt-5-nano", "gpt-4.1-nano", "gpt-5-mini", "gpt-4o-mini"] # PROTECTED - Performance critical (não altere mais esta lista)
        elif provider == "deepseek":
            return ["deepseek-chat", "deepseek-coder"]
        elif provider == "ollama":
            return ["llama2", "codellama", "mistral", "neural-chat"]
        else:
            return []
    
    def get_default_model(self, provider: str) -> str:
        """Retorna o modelo padrão para um provedor"""
        if provider == "openai":
            return OPENAI_MODEL
        elif provider == "deepseek":
            return DEEPSEEK_MODEL
        elif provider == "ollama":
            return OLLAMA_MODEL
        else:
            return ""
    
    def get_provider_description(self, provider: str) -> str:
        """Retorna descrição do provedor"""
        descriptions = {
            "openai": "OpenAI GPT - Modelos avançados de linguagem natural",
            "deepseek": "DeepSeek - Modelos especializados em código e chat",
            "ollama": "Ollama - Modelos locais de código aberto"
        }
        return descriptions.get(provider, "Provedor desconhecido")

ai_service = AIService()