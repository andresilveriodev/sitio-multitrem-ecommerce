import urllib.request
import urllib.parse
import json

def send_request(data):
    url = "http://localhost:8012/ai/generate"
    json_data = json.dumps(data).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=json_data,
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req) as response:
        return response, json.loads(response.read().decode('utf-8'))

def test_gpt5_nano():
    base_data = {
        "messages": [
            {"role": "user", "content": "Qual modelo você é?"}
        ],
        "provider": "openai",
        "temperature": 0.7
    }

    try:
        # Primeiro tenta com max_completion_tokens
        data = base_data.copy()
        data["max_completion_tokens"] = 100
        response, result = send_request(data)

    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"⚠️ Erro inicial: {error_msg}")

        # Se foi erro de parâmetro, tenta com max_tokens
        if "max_completion_tokens" in error_msg or "unsupported_parameter" in error_msg:
            print("🔄 Tentando novamente com `max_tokens`...")
            data = base_data.copy()
            data["max_tokens"] = 100
            response, result = send_request(data)
        else:
            raise

    # Exibe resultado
    print(f"Status Code: {response.status}")
    print(f"Response JSON:\n{json.dumps(result, indent=2, ensure_ascii=False)}")

    resposta = None
    if 'response' in result:
        resposta = result['response']
    elif "choices" in result and len(result["choices"]) > 0:
        escolha = result["choices"][0]
        if "message" in escolha and "content" in escolha["message"]:
            resposta = escolha["message"]["content"]

    if resposta:
        print(f"\nResposta da IA: {resposta}")
    else:
        print("\n⚠️ Não encontrei resposta no JSON retornado.")

if __name__ == "__main__":
    test_gpt5_nano()
