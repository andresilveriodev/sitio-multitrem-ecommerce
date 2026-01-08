"""
AgentOS - Sítio Multitrem E-commerce
Sistema Multi-Agente com:
- Vendedor (Sales)
- Agendamento (Scheduling) 
- Pagamento (Payment)
- Suporte (Support)
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.sqlite import AsyncSqliteDb
from agno.os import AgentOS
from dotenv import load_dotenv
import os

load_dotenv()

# Verificar OPENAI_API_KEY
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️ AVISO: OPENAI_API_KEY não encontrada no .env")
    print("Configure sua chave da OpenAI no arquivo .env")

# ============================================
# AGENTE 1: VENDEDOR (SALES AGENT)
# ============================================
sales_agent = Agent(
    name="Vendedor",
    model=OpenAIChat(id="gpt-4o-mini"),
    db=AsyncSqliteDb(db_file="sitio_multitrem.db"),
    instructions=[
        "Você é o Vendedor do Sítio Multitrem, uma fazenda em Terezópolis de Goiás.",
        "Vende hortaliças frescas colhidas no dia e ovos caipiras.",
        "Seja simpático, prestativo e use emojis com moderação (🥬 🥚 🌿)",
        "Ajude o cliente a escolher produtos, explique preços e crie pedidos.",
        "Entregas: quarta a sábado, período da manhã.",
        "WhatsApp: (62) 98122-5993",
        "Instagram: @sitio.multitrem",
    ],
    markdown=True,
)

# ============================================
# AGENTE 2: AGENDAMENTO (SCHEDULING AGENT)
# ============================================
scheduling_agent = Agent(
    name="Agendamento",
    model=OpenAIChat(id="gpt-4o-mini"),
    db=AsyncSqliteDb(db_file="sitio_multitrem.db"),
    instructions=[
        "Você é o Assistente de Agendamento do Sítio Multitrem.",
        "Responsável por agendar e gerenciar entregas.",
        "Entregas disponíveis: quarta a sábado, período da manhã (8h-12h).",
        "Confirme sempre o endereço completo antes de finalizar.",
        "Seja claro sobre horários e datas disponíveis.",
    ],
    markdown=True,
)

# ============================================
# AGENTE 3: PAGAMENTO (PAYMENT AGENT)
# ============================================
payment_agent = Agent(
    name="Pagamento",
    model=OpenAIChat(id="gpt-4o-mini"),
    db=AsyncSqliteDb(db_file="sitio_multitrem.db"),
    instructions=[
        "Você é o Assistente de Pagamento do Sítio Multitrem.",
        "Responsável por processar pagamentos via Pix e Boleto.",
        "Gere links de pagamento, confirme recebimentos e envie comprovantes.",
        "Seja claro sobre valores e métodos de pagamento disponíveis.",
        "Métodos aceitos: Pix (instantâneo) e Boleto (vencimento 3 dias).",
    ],
    markdown=True,
)

# ============================================
# AGENTE 4: SUPORTE (SUPPORT AGENT)
# ============================================
support_agent = Agent(
    name="Suporte",
    model=OpenAIChat(id="gpt-4o-mini"),
    db=AsyncSqliteDb(db_file="sitio_multitrem.db"),
    instructions=[
        "Você é o Atendente de Suporte do Sítio Multitrem.",
        "Ajude com problemas, cancelamentos, rastreamento e dúvidas gerais.",
        "Seja empático e resolva problemas rapidamente.",
        "Se não conseguir resolver, escale para atendimento humano.",
        "Priorize a satisfação do cliente.",
    ],
    markdown=True,
)

# ============================================
# CRIAR AGENTOS (Multi-Agent System)
# ============================================
agent_os = AgentOS(
    id="sitio-multitrem-os",
    name="Sítio Multitrem AgentOS",
    description="Sistema Multi-Agente para E-commerce de Produtos Orgânicos",
    agents=[
        sales_agent,
        scheduling_agent,
        payment_agent,
        support_agent,
    ],
)

# Exportar app para o uvicorn
app = agent_os.get_app()

if __name__ == "__main__":
    print("=" * 60)
    print("SITIO MULTITREM - AGENTOS")
    print("=" * 60)
    print("Porta: 7777 (padrao AgentOS)")
    print("App Interface: http://localhost:7777")
    print("API Docs: http://localhost:7777/docs")
    print("Config: http://localhost:7777/config")
    print("")
    print("Agentes Disponiveis:")
    print("  1. Vendedor - Vendas e produtos")
    print("  2. Agendamento - Entregas e horarios")
    print("  3. Pagamento - Pix e boleto")
    print("  4. Suporte - Ajuda e problemas")
    print("=" * 60)
    print("")
    
    # Iniciar servidor (porta 7777 e padrao do AgentOS)
    agent_os.serve(app="my_os:app", reload=True)

