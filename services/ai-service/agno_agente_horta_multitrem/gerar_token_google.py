"""Script para gerar token OAuth do Google Calendar."""
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Configurações
credentials_path = "client_secret_2_707216253310-iikqnhv3eu0r2d941ljc3fa6reh7m6hr.apps.googleusercontent.com.json"
token_path = "token.json"
# ⚠️ IMPORTANTE: Use apenas o scope de escrita completo, não "read" e "write" separados
SCOPES = ["https://www.googleapis.com/auth/calendar"]

print("🔐 Iniciando autenticação OAuth do Google Calendar...")
print(f"📁 Credenciais: {credentials_path}")
print(f"💾 Token será salvo em: {token_path}")
print()

# Verificar se o arquivo de credenciais existe
if not os.path.exists(credentials_path):
    print(f"❌ Erro: Arquivo de credenciais não encontrado: {credentials_path}")
    print("   Certifique-se de que o arquivo está no diretório atual.")
    exit(1)

# Carregar credenciais
try:
    with open(credentials_path, 'r', encoding='utf-8') as f:
        creds_data = json.load(f)
    
    # Verificar se é formato "installed" (Desktop app)
    if "installed" not in creds_data:
        print("❌ Erro: O arquivo de credenciais deve ser do tipo 'Desktop app' (installed)")
        print("   Verifique se o arquivo tem a estrutura correta.")
        exit(1)
    
    client_config = {
        "installed": creds_data["installed"]
    }
    
except Exception as e:
    print(f"❌ Erro ao ler arquivo de credenciais: {e}")
    exit(1)

# Verificar se já existe um token
creds = None
if os.path.exists(token_path):
    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        print(f"📄 Token existente encontrado em {token_path}")
    except Exception as e:
        print(f"⚠️ Token existente inválido: {e}")
        print("   Gerando novo token...")
        creds = None

# Se não há credenciais válidas, fazer o fluxo OAuth
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        print("🔄 Token expirado, renovando...")
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"⚠️ Erro ao renovar token: {e}")
            print("   Iniciando novo fluxo de autorização...")
            creds = None
    
    if not creds:
        print("🌐 Iniciando fluxo de autorização OAuth...")
        print("   Isso abrirá o navegador para você autorizar o acesso.")
        print()
        
        try:
            # Usar a URI de redirecionamento configurada nas credenciais
            redirect_uri = client_config["installed"].get("redirect_uris", ["http://localhost"])[0]
            
            # Se não tiver porta, usar a padrão (8080) ou tentar outras
            if ":" not in redirect_uri or redirect_uri == "http://localhost":
                # Tentar portas em ordem: 8080 (padrão), 8081, 8082
                ports_to_try = [8080, 8081, 8082]
                creds = None
                
                for port in ports_to_try:
                    try:
                        redirect_uri_with_port = f"http://localhost:{port}/"
                        print(f"🔄 Tentando usar porta {port}...")
                        
                        # Criar fluxo OAuth com a URI correta
                        flow = InstalledAppFlow.from_client_config(
                            client_config,
                            SCOPES,
                            redirect_uri=redirect_uri_with_port
                        )
                        
                        creds = flow.run_local_server(port=port, open_browser=True)
                        break
                    except OSError as port_error:
                        if port == ports_to_try[-1]:
                            # Última porta falhou, usar fluxo manual
                            print(f"⚠️ Todas as portas ocupadas. Usando fluxo manual...")
                            # Criar fluxo sem servidor local
                            flow = InstalledAppFlow.from_client_config(
                                client_config,
                                SCOPES
                            )
                            auth_url, _ = flow.authorization_url(prompt='consent')
                            print()
                            print("=" * 70)
                            print("🌐 AUTORIZAÇÃO MANUAL")
                            print("=" * 70)
                            print()
                            print("1. Abra esta URL no seu navegador:")
                            print(f"   {auth_url}")
                            print()
                            print("2. Faça login e autorize o acesso")
                            print("3. Após autorizar, você será redirecionado para uma página de erro")
                            print("4. Copie a URL COMPLETA da barra de endereços (mesmo que mostre erro)")
                            print("5. Procure por 'code=' na URL e copie o valor após 'code='")
                            print()
                            print("=" * 70)
                            print()
                            
                            code = input("Cole o código de autorização aqui: ").strip()
                            # Extrair apenas o código se o usuário colou a URL completa
                            if "code=" in code:
                                code = code.split("code=")[1].split("&")[0]
                            
                            flow.fetch_token(code=code)
                            creds = flow.credentials
                        continue
            else:
                # URI já tem porta específica, usar ela
                flow = InstalledAppFlow.from_client_config(
                    client_config,
                    SCOPES,
                    redirect_uri=redirect_uri
                )
                # Extrair porta da URI
                port = int(redirect_uri.split(":")[-1].rstrip("/"))
                creds = flow.run_local_server(port=port, open_browser=True)
                    
        except Exception as e:
            print(f"❌ Erro durante autenticação: {e}")
            print()
            print("Possíveis causas:")
            print("1. Arquivo de credenciais inválido ou corrompido")
            print("2. Todas as portas estão ocupadas (pare o AgentOS primeiro)")
            print("3. Erro de rede ou conexão com Google")
            print()
            print("💡 Dica: Pare o AgentOS e tente novamente, ou use o fluxo manual acima.")
            exit(1)
    
    # Salvar token
    try:
        # Garantir que os scopes estão no formato correto (array)
        token_data = json.loads(creds.to_json())
        
        # Verificar e corrigir formato dos scopes se necessário
        if "scopes" in token_data:
            if isinstance(token_data["scopes"], dict):
                # Se for dicionário, converter para array com o scope de escrita
                print("⚠️ Corrigindo formato dos scopes no token...")
                token_data["scopes"] = ["https://www.googleapis.com/auth/calendar"]
            elif isinstance(token_data["scopes"], list):
                # Se já for array, garantir que tem o scope correto
                if "https://www.googleapis.com/auth/calendar" not in token_data["scopes"]:
                    token_data["scopes"] = ["https://www.googleapis.com/auth/calendar"]
            else:
                # Se for string ou outro formato, converter para array
                token_data["scopes"] = ["https://www.googleapis.com/auth/calendar"]
        else:
            # Se não tiver scopes, adicionar
            token_data["scopes"] = ["https://www.googleapis.com/auth/calendar"]
        
        # Salvar token corrigido
        with open(token_path, 'w', encoding='utf-8') as token:
            json.dump(token_data, token, indent=2)
        print("✅ Token salvo com sucesso!")
        print(f"✅ Scopes configurados: {token_data['scopes']}")
    except Exception as e:
        print(f"❌ Erro ao salvar token: {e}")
        exit(1)

print()
print("=" * 70)
print("✅ AUTENTICAÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 70)
print(f"✅ Token salvo em: {token_path}")
print()
print("Agora você pode usar o Google Calendar no agente!")
print("Reinicie o AgentOS para aplicar as mudanças.")
print("=" * 70)
