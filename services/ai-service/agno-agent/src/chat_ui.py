"""
Interface de Chat com Gradio para testar o Agente de Vendas.
"""

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from src.agents.sales_agent import create_sales_agent
from src.tools.ecommerce_tools import set_visitor_id

# Criar agente
agent = create_sales_agent("gradio-user")
set_visitor_id("gradio-user")

def chat(message, history):
    """Processa mensagem e retorna resposta do agente."""
    try:
        result = agent.run(message)
        return result.content or "Desculpe, nao consegui processar sua mensagem."
    except Exception as e:
        return f"Erro: {str(e)}"

# Criar interface Gradio
demo = gr.ChatInterface(
    fn=chat,
    title="Assistente Sitio Multitrem",
    description="Assistente de vendas do Sitio Multitrem - Hortalicas frescas e ovos caipiras",
    examples=[
        "Ola, bom dia!",
        "Quais produtos voces vendem?",
        "Quais dias voces entregam?",
        "Quero fazer um pedido"
    ]
)

if __name__ == "__main__":
    demo.launch(server_port=7788, share=False)

