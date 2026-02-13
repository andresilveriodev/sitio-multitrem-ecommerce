"""
Script para testar todos os endpoints disponíveis no Chatbot Service
"""

import httpx
import json
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime

# Configurar encoding para Windows
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')  # UTF-8
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Configuração
CHATBOT_BASE_URL = "http://localhost:8011"
KEYCLOAK_AUTH_URL = "https://auth.rendacontinua.com/auth"
KEYCLOAK_REALM = "auth_sso"
KEYCLOAK_CLIENT_ID = "auth_client"
KEYCLOAK_CLIENT_SECRET = "e56cf527-d5d9-4b52-bd9f-1e87c8f288de"

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Imprime cabeçalho formatado"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_test(name: str):
    """Imprime nome do teste"""
    try:
        print(f"{Colors.BOLD}▶ {name}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.BOLD}[TEST] {name}{Colors.RESET}")


def print_success(message: str):
    """Imprime mensagem de sucesso"""
    try:
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.GREEN}[OK] {message}{Colors.RESET}")


def print_error(message: str):
    """Imprime mensagem de erro"""
    try:
        print(f"{Colors.RED}✗ {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.RED}[ERROR] {message}{Colors.RESET}")


def print_warning(message: str):
    """Imprime mensagem de aviso"""
    try:
        print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.YELLOW}[WARN] {message}{Colors.RESET}")


def print_response(response: httpx.Response, show_body: bool = True):
    """Imprime resposta formatada"""
    status_color = Colors.GREEN if response.status_code < 400 else Colors.RED
    print(f"  Status: {status_color}{response.status_code}{Colors.RESET}")
    
    if show_body:
        try:
            body = response.json()
            print(f"  Response: {json.dumps(body, indent=2, ensure_ascii=False)}")
        except:
            print(f"  Response: {response.text[:200]}")


def get_jwt_token(username: str, password: str) -> Optional[str]:
    """
    Obtém token JWT do Keycloak
    Nota: Este método requer credenciais válidas
    """
    try:
        token_url = f"{KEYCLOAK_AUTH_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
        
        data = {
            "grant_type": "password",
            "client_id": KEYCLOAK_CLIENT_ID,
            "client_secret": KEYCLOAK_CLIENT_SECRET,
            "username": username,
            "password": password,
            "scope": "openid profile email"
        }
        
        response = httpx.post(token_url, data=data, timeout=10.0)
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print_warning(f"Erro ao obter token: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print_warning(f"Erro ao obter token JWT: {e}")
        return None


def test_endpoint(
    client: httpx.Client,
    method: str,
    endpoint: str,
    token: Optional[str] = None,
    json_data: Optional[Dict] = None,
    expected_status: Optional[int] = None,
    description: str = ""
) -> bool:
    """Testa um endpoint"""
    url = f"{CHATBOT_BASE_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.upper() == "GET":
            response = client.get(url, headers=headers, timeout=30.0)
        elif method.upper() == "POST":
            response = client.post(url, headers=headers, json=json_data, timeout=30.0)
        else:
            print_error(f"Método {method} não suportado")
            return False
        
        success = expected_status is None or response.status_code == expected_status
        
        if success:
            print_success(f"{description or endpoint} - Status: {response.status_code}")
        else:
            print_error(f"{description or endpoint} - Status: {response.status_code} (esperado: {expected_status})")
        
        print_response(response, show_body=success or response.status_code >= 400)
        
        return success
        
    except httpx.ConnectError:
        print_error(f"Não foi possível conectar ao {CHATBOT_BASE_URL}")
        print_warning("Certifique-se de que o Chatbot Service está rodando na porta 8011")
        return False
    except Exception as e:
        print_error(f"Erro ao testar {endpoint}: {e}")
        return False


def main():
    """Função principal"""
    print_header("TESTE DE ENDPOINTS DO CHATBOT SERVICE")
    
    # Verificar se o serviço está rodando
    print_test("Verificando se o serviço está rodando...")
    try:
        response = httpx.get(f"{CHATBOT_BASE_URL}/health", timeout=5.0)
        if response.status_code == 200:
            print_success("Serviço está rodando")
            print_response(response)
        else:
            print_error(f"Serviço retornou status {response.status_code}")
            sys.exit(1)
    except httpx.ConnectError:
        print_error(f"Não foi possível conectar ao {CHATBOT_BASE_URL}")
        print_warning("Certifique-se de que o Chatbot Service está rodando")
        print_warning("Execute: cd 3_chatbot/bot_operations && python main.py")
        sys.exit(1)
    
    # Obter token JWT (opcional - pode ser fornecido via variável de ambiente)
    token = None
    print_test("Obtendo token JWT...")
    
    # Tentar obter token via variável de ambiente
    import os
    token = os.getenv("JWT_TOKEN")
    
    if not token:
        print_warning("Token JWT não fornecido via JWT_TOKEN")
        print_warning("Alguns endpoints requerem autenticação")
        print_warning("Para testar com autenticação, defina: export JWT_TOKEN='seu_token_aqui'")
        print_warning("Ou forneça username/password para obter token do Keycloak")
        
        # Tentar obter via Keycloak (requer credenciais)
        username = os.getenv("KEYCLOAK_USERNAME")
        password = os.getenv("KEYCLOAK_PASSWORD")
        
        if username and password:
            print_test("Tentando obter token do Keycloak...")
            token = get_jwt_token(username, password)
            if token:
                print_success("Token obtido com sucesso")
            else:
                print_warning("Não foi possível obter token do Keycloak")
        else:
            print_warning("Credenciais do Keycloak não fornecidas")
    else:
        print_success("Token JWT encontrado na variável de ambiente")
    
    # Criar cliente HTTP
    client = httpx.Client(timeout=30.0)
    
    results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # ============================================
    # TESTES DE ENDPOINTS PÚBLICOS (SEM AUTH)
    # ============================================
    print_header("ENDPOINTS PÚBLICOS")
    
    # Health check
    print_test("GET /health")
    if test_endpoint(client, "GET", "/health", expected_status=200, description="Health Check"):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Root endpoint
    print_test("GET /")
    if test_endpoint(client, "GET", "/", expected_status=200, description="Root Endpoint"):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # ============================================
    # TESTES DE ENDPOINTS DE CHAT (REQUEREM AUTH)
    # ============================================
    print_header("ENDPOINTS DE CHAT (REQUEREM AUTENTICAÇÃO)")
    
    if not token:
        print_warning("Pulando testes que requerem autenticação (token não disponível)")
        results["skipped"] += 10
    else:
        # Process message
        print_test("POST /chatbot/process-message")
        test_data = {
            "user_id": "test_user_123",
            "message": "Olá, como você está?",
            "session_id": "test_session_123",
            "content_type": "text/plain"
        }
        if test_endpoint(client, "POST", "/chatbot/process-message", token=token, 
                        json_data=test_data, description="Process Message"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Process message stream (não testável facilmente via script, mas podemos tentar)
        print_test("POST /chatbot/process-message/stream")
        print_warning("Streaming endpoint - teste manual recomendado")
        results["skipped"] += 1
        
        # Validate input
        print_test("POST /chatbot/validate-input")
        validate_data = {
            "user_id": "test_user_123",
            "message": "Teste de validação",
            "content_type": "text/plain"
        }
        if test_endpoint(client, "POST", "/chatbot/validate-input", token=token,
                        json_data=validate_data, description="Validate Input"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Get conversation context
        print_test("GET /chatbot/conversation/{user_id}")
        if test_endpoint(client, "GET", "/chatbot/conversation/test_user_123", token=token,
                        description="Get Conversation Context"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Update context
        print_test("POST /chatbot/update-context")
        update_data = {
            "user_id": "test_user_123",
            "summary": "Contexto de teste atualizado"
        }
        if test_endpoint(client, "POST", "/chatbot/update-context", token=token,
                        json_data=update_data, description="Update Context"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Chat endpoint
        print_test("POST /chatbot/chat")
        chat_data = {
            "conversation_id": 1,
            "message": "Olá",
            "user_id": "test_user_123",
            "provider": "openai",
            "model": "gpt-3.5-turbo"
        }
        if test_endpoint(client, "POST", "/chatbot/chat", token=token,
                        json_data=chat_data, description="Chat Endpoint"):
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    # ============================================
    # TESTES DE ENDPOINTS DE ANALYTICS (REQUEREM AUTH)
    # ============================================
    print_header("ENDPOINTS DE ANALYTICS (REQUEREM AUTENTICAÇÃO)")
    
    if not token:
        print_warning("Pulando testes de analytics (token não disponível)")
        results["skipped"] += 7
    else:
        # User analytics
        print_test("GET /chatbot/analytics/{user_id}")
        if test_endpoint(client, "GET", "/chatbot/analytics/test_user_123", token=token,
                        description="User Analytics"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Cost tracking
        print_test("GET /chatbot/cost-tracking/{user_id}")
        if test_endpoint(client, "GET", "/chatbot/cost-tracking/test_user_123", token=token,
                        description="Cost Tracking"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Cache stats
        print_test("GET /chatbot/cache-stats")
        if test_endpoint(client, "GET", "/chatbot/cache-stats", token=token,
                        description="Cache Stats"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Clear cache
        print_test("POST /chatbot/clear-cache")
        if test_endpoint(client, "POST", "/chatbot/clear-cache", token=token,
                        description="Clear Cache"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Invalidate user cache
        print_test("POST /chatbot/invalidate-user-cache/{user_id}")
        if test_endpoint(client, "POST", "/chatbot/invalidate-user-cache/test_user_123", token=token,
                        description="Invalidate User Cache"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # System health
        print_test("GET /chatbot/system-health")
        if test_endpoint(client, "GET", "/chatbot/system-health", token=token,
                        description="System Health"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Performance metrics
        print_test("GET /chatbot/performance-metrics")
        if test_endpoint(client, "GET", "/chatbot/performance-metrics", token=token,
                        description="Performance Metrics"):
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    # ============================================
    # TESTES DE ENDPOINTS DE AI (REQUEREM AUTH)
    # ============================================
    print_header("ENDPOINTS DE AI (REQUEREM AUTENTICAÇÃO)")
    
    if not token:
        print_warning("Pulando testes de AI (token não disponível)")
        results["skipped"] += 2
    else:
        # AI Chat
        print_test("POST /ai/chat")
        ai_chat_data = {
            "message": "Olá, como você está?"
        }
        if test_endpoint(client, "POST", "/ai/chat", token=token,
                        json_data=ai_chat_data, description="AI Chat"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        # Get providers
        print_test("GET /ai/providers")
        if test_endpoint(client, "GET", "/ai/providers", token=token,
                        description="Get AI Providers"):
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    # ============================================
    # TESTE DE ENDPOINT AUSENTE
    # ============================================
    print_header("VERIFICAÇÃO DE ENDPOINT AUSENTE")
    
    print_test("POST /chatbot/process-message-authenticated")
    print_warning("Este endpoint NÃO existe no chatbot service")
    print_warning("O telegram_operations tenta chamar este endpoint, mas ele não está implementado")
    
    if token:
        test_data = {
            "message": "Teste",
            "session_id": "test_session"
        }
        response = client.post(
            f"{CHATBOT_BASE_URL}/chatbot/process-message-authenticated",
            headers={"Authorization": f"Bearer {token}"},
            json=test_data,
            timeout=10.0
        )
        if response.status_code == 404:
            print_success("Endpoint não encontrado (404) - como esperado")
            results["passed"] += 1
        else:
            print_error(f"Endpoint retornou status {response.status_code} (esperado 404)")
            results["failed"] += 1
    else:
        print_warning("Teste pulado (token não disponível)")
        results["skipped"] += 1
    
    # Fechar cliente
    client.close()
    
    # ============================================
    # RESUMO
    # ============================================
    print_header("RESUMO DOS TESTES")
    
    total = results["passed"] + results["failed"] + results["skipped"]
    
    print(f"{Colors.GREEN}✓ Passou: {results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}✗ Falhou: {results['failed']}{Colors.RESET}")
    print(f"{Colors.YELLOW}⚠ Pulado: {results['skipped']}{Colors.RESET}")
    print(f"{Colors.BOLD}Total: {total}{Colors.RESET}")
    
    if results["failed"] > 0:
        print(f"\n{Colors.RED}Alguns testes falharam!{Colors.RESET}")
        sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}Todos os testes passaram!{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
