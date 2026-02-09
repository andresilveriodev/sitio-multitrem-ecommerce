from openai import OpenAI
import httpx
import json
from typing import List, Dict, Optional, AsyncGenerator
import logging
from app.config import (
    OPENAI_API_KEY, OPENAI_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    DEFAULT_AI_PROVIDER, SUPPORTED_PROVIDERS
)

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self.deepseek_client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        ) if DEEPSEEK_API_KEY else None
    
    async def send(self, message: str, model: str = "gpt-4o-mini", max_tokens: int = 1000, temperature: float = 0.7) -> str:
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
            temperature=temperature
        )
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
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
                result = await self._generate_openai_response(messages, model or OPENAI_MODEL, max_tokens, temperature)
                if is_gpt41nano:
                    print(f"\n[OK] AI_SERVICE.generate_response concluído com sucesso!")
                return result
            elif provider == "deepseek":
                return await self._generate_deepseek_response(messages, model or DEEPSEEK_MODEL, max_tokens, temperature)
            elif provider == "ollama":
                return await self._generate_ollama_response(messages, model or OLLAMA_MODEL)
        
        except Exception as e:
            error_msg = f"Erro na comunicação com a IA ({provider}): {str(e)}"
            if is_gpt41nano:
                print(f"\n[ERRO] AI_SERVICE.generate_response falhou:")
                print(f"  Erro: {error_msg}")
                import traceback
                print(f"  Traceback: {traceback.format_exc()}")
            logger.error(f"Erro ao gerar resposta da IA ({provider}): {str(e)}")
            raise Exception(error_msg)
    
    async def _generate_openai_response(self, messages: List[Dict[str, str]], model: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
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
        
        logger.info(f"Chamando OpenAI com modelo: {model}, messages: {messages}")
        
        # Usa a mesma lógica simples do ai_service_simple que funciona
        # Usa apenas max_tokens (max_completion_tokens não existe nesta versão da lib)
        try:
            if is_gpt41nano:
                print("[*] Enviando requisição para OpenAI...")
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if is_gpt41nano:
                print("[OK] Requisição bem-sucedida!")
                
        except Exception as e:
            if is_gpt41nano:
                print(f"[ERRO] Falha na requisição GPT-4.1-nano:")
                print(f"  Tipo: {type(e).__name__}")
                print(f"  Mensagem: {str(e)}")
                import traceback
                print(f"  Traceback: {traceback.format_exc()}")
            logger.error(f"Erro ao chamar OpenAI: {e}")
            raise
        
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