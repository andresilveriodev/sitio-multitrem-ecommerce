# ai_service_simple.py
# Service simples e funcional para GPT-4.1-nano

from openai import OpenAI
import os
import logging

logger = logging.getLogger(__name__)

class AIServiceSimple:
    """
    Service simples e limpo para GPT-4.1-nano
    Sem lógica complexa, sem fallbacks, apenas o essencial
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY não configurada")
        self.client = OpenAI(api_key=api_key)
        logger.info("AIServiceSimple inicializado com sucesso")
    
    async def send(self, user_message: str, model: str = "gpt-4.1-nano", max_tokens: int = 100, temperature: float = 0.7):
        """
        Envia mensagem do chatbot para o GPT
        e retorna a resposta em texto.
        """
        is_gpt41nano = "gpt-4.1-nano" in model.lower()
        
        if is_gpt41nano:
            print("\n" + "=" * 80)
            print("🚀 AI_SERVICE_SIMPLE.send - GPT-4.1-NANO")
            print("=" * 80)
            print(f"Model: {model}")
            print(f"Max Tokens: {max_tokens}")
            print(f"Temperature: {temperature}")
            print(f"User Message: {user_message[:100]}...")
            print("-" * 80)
        
        try:
            logger.info(f"Enviando mensagem para {model}: {user_message[:50]}...")
            
            if is_gpt41nano:
                print("[*] Enviando requisição para OpenAI...")
            
            # Usa max_tokens (max_completion_tokens não existe nesta versão da lib)
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if is_gpt41nano:
                print("[OK] Requisição bem-sucedida!")
            
            # Extrai conteúdo da resposta
            reply = response.choices[0].message.content
            
            if is_gpt41nano:
                print("-" * 80)
                print("✅ RESPOSTA RECEBIDA:")
                print(f"  Conteúdo: {reply[:200] if reply else 'VAZIA'}...")
                print(f"  Tamanho: {len(reply) if reply else 0} caracteres")
                if hasattr(response, 'usage'):
                    usage = response.usage
                    print(f"  Tokens usados: {usage.total_tokens if hasattr(usage, 'total_tokens') else 'N/A'}")
                print("=" * 80 + "\n")
            
            logger.info(f"Resposta recebida: {reply[:50] if reply else 'VAZIA'}...")
            return reply or ""
            
        except Exception as e:
            if is_gpt41nano:
                print(f"\n[ERRO] AI_SERVICE_SIMPLE.send falhou:")
                print(f"  Tipo: {type(e).__name__}")
                print(f"  Mensagem: {str(e)}")
                import traceback
                print(f"  Traceback: {traceback.format_exc()}")
                print("=" * 80 + "\n")
            
            logger.error(f"Erro no AIServiceSimple: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Erro ao processar mensagem: {str(e)}")

# Instância reutilizável
ai_service_simple = AIServiceSimple()

