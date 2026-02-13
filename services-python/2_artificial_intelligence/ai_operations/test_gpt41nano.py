import requests
import json

# Configuração da API
url = "http://localhost:8000/ai/generate"
headers = {"Content-Type": "application/json"}

# Teste com gpt-4.1-nano
data = {
    "message": "Analise a seguinte operação de homebroker: Compra de 100 ações PETR4 a R$ 35,50",
    "provider": "openai",
    "model": "gpt-4.1-nano",
    "max_tokens": 150,
    "temperature": 0.7
}

print("Testando modelo gpt-4.1-nano...")
print(f"Dados enviados: {json.dumps(data, indent=2)}")
print("\n" + "="*50 + "\n")

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Provider: {result.get('provider')}")
        print(f"Model: {result.get('model')}")
        print(f"Total Tokens: {result.get('total_tokens')}")
        print(f"Response Type: {type(result.get('response'))}")
        print(f"Response Length: {len(str(result.get('response', '')))}")
        print("\nResposta:")
        print(result.get('response', 'Resposta vazia'))
    else:
        print(f"Erro: {response.text}")
        
except Exception as e:
    print(f"Erro na requisição: {e}")