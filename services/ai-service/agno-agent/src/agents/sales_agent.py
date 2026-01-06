from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
import os

load_dotenv()

# Importar ferramentas
from src.tools.ecommerce_tools import (
    list_products,
    add_to_cart,
    remove_from_cart,
    view_cart,
    check_delivery_slots,
    create_order,
    generate_payment_link
)

# Importar prompt
from src.prompts.sales_prompt import SYSTEM_PROMPT

def create_sales_agent(visitor_id: str = None):
    """
    Cria uma instancia do agente de vendas do Sitio Multitrem.
    
    Args:
        visitor_id: ID unico do visitante para rastrear sessao
    
    Returns:
        Agent: Instancia configurada do agente
    """
    
    # Configuracoes do modelo via .env
    model_id = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '500'))
    
    # Criar agente
    agent = Agent(
        name="Assistente Sitio Multitrem",
        model=OpenAIChat(
            id=model_id,
            temperature=temperature,
            max_tokens=max_tokens
        ),
        tools=[
            list_products,
            add_to_cart,
            remove_from_cart,
            view_cart,
            check_delivery_slots,
            create_order,
            generate_payment_link
        ],
        instructions=SYSTEM_PROMPT,
        num_history_messages=10,
        markdown=True,
        debug_mode=os.getenv('DEBUG', 'false').lower() == 'true'
    )
    
    return agent

