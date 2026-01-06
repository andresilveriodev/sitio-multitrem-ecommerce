from src.agents.sales_agent import create_sales_agent
from dotenv import load_dotenv

load_dotenv()

def test_basic_conversation():
    """Testa uma conversa basica com o agente."""
    agent = create_sales_agent("test-user")
    
    # Teste 1: Saudacao
    response = agent.run("Ola, bom dia!")
    print(f"Resposta 1: {response.content}\n")
    
    # Teste 2: Listar produtos
    response = agent.run("Quais produtos voces tem?")
    print(f"Resposta 2: {response.content}\n")
    
    # Teste 3: Pergunta sobre entrega
    response = agent.run("Quais dias voces entregam?")
    print(f"Resposta 3: {response.content}\n")

if __name__ == "__main__":
    test_basic_conversation()

