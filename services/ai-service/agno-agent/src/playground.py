"""
Agno OS - Servidor para conectar ao Playground em app.agno.com
"""

from agno.os.app import AgentOS
from src.agents.sales_agent import create_sales_agent
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# Criar agente para o playground
agent = create_sales_agent("playground-user")

# Criar app do Agno OS
agno_os = AgentOS(agents=[agent])
app = agno_os.get_app()

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Servidor Agno OS iniciado!")
    print("="*50)
    print("\nPara usar o Playground:")
    print("1. Acesse: https://app.agno.com")
    print("2. Conecte ao servidor local: http://localhost:7777")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=7777)

