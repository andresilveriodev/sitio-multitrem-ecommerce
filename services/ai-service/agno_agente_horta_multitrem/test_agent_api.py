"""
Script de teste para verificar se o agente está acessível via API
"""
import requests
import json

def test_agent():
    base_url = "http://localhost:7777"
    
    # 1. Verificar se o AgentOS está rodando
    print("🔍 Testando conexão com AgentOS...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ AgentOS está rodando! Status: {response.status_code}")
    except Exception as e:
        print(f"❌ AgentOS não está acessível: {e}")
        return
    
    # 2. Listar agentes disponíveis
    print("\n🔍 Listando agentes disponíveis...")
    try:
        response = requests.get(f"{base_url}/agents", timeout=5)
        agents = response.json()
        print(f"✅ Agentes encontrados: {json.dumps(agents, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Erro ao listar agentes: {e}")
        return
    
    # 3. Testar chamada ao agente
    print("\n🔍 Testando chamada ao agente 'assistente_sitio_multitrem'...")
    try:
        import io
        files = {
            'message': (None, 'Olá, quero saber mais sobre os produtos'),
            'stream': (None, 'false'),
            'user_id': (None, 'test_user'),
            'session_id': (None, 'test_session'),
        }
        
        response = requests.post(
            f"{base_url}/agents/assistente_sitio_multitrem/runs",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Resposta recebida!")
            print(f"📝 Conteúdo: {result.get('content', 'N/A')[:200]}...")
        else:
            print(f"❌ Erro na resposta: {response.status_code}")
            print(f"📝 Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao chamar agente: {e}")

if __name__ == "__main__":
    test_agent()
