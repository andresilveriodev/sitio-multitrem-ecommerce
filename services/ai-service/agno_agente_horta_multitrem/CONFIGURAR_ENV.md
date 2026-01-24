# ⚙️ Configuração do Arquivo .env

## 📝 Configuração do Google Calendar

O `GoogleCalendarTools` do Agno usa um **arquivo JSON de credenciais**, não variáveis individuais. Você só precisa configurar o **caminho do arquivo** no `.env`.

### ✅ Configuração Atual (Já está correta!)

Seu arquivo JSON já está na pasta:
```
client_secret_SEU_CLIENT_ID.apps.googleusercontent.com.json
```

### 📄 Arquivo .env

Crie ou edite o arquivo `.env` na pasta `services/ai-service/agno_agente_horta_multitrem/`:

```env
# OpenAI API Key
OPENAI_API_KEY=sk-proj-sua-chave-aqui

# Configurações opcionais
OPENAI_MODEL=gpt-4o-mini
DATABASE_PATH=tmp/data.db

# Google Calendar Configuration
GOOGLE_CREDENTIALS_PATH=client_secret_SEU_CLIENT_ID.apps.googleusercontent.com.json
GOOGLE_TOKEN_PATH=token.json
GOOGLE_CALENDAR_ID=primary
```

### 🔍 Explicação das Variáveis

- **`GOOGLE_CREDENTIALS_PATH`**: Caminho para o arquivo JSON de credenciais (já está na pasta)
- **`GOOGLE_TOKEN_PATH`**: Onde o token OAuth será salvo (gerado automaticamente na primeira execução)
- **`GOOGLE_CALENDAR_ID`**: ID do calendário (use `primary` para o calendário principal do Google)

### ⚠️ Importante sobre o Formato do JSON

Seu arquivo JSON atual é do tipo **"web"**:

```json
{
  "web": {
    "client_id": "...",
    "client_secret": "...",
    ...
  }
}
```

O `GoogleCalendarTools` geralmente funciona melhor com o formato **"installed"** (Desktop app):

```json
{
  "installed": {
    "client_id": "...",
    "client_secret": "...",
    ...
  }
}
```

### 🔄 Se o Formato "web" Não Funcionar

Se você encontrar erros de autenticação, você tem duas opções:

#### Opção 1: Converter o JSON (Rápido)

Edite o arquivo JSON e mude `"web"` para `"installed"`:

```json
{
  "installed": {
    "client_id": "SEU_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "seu-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "SEU_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

**Mudanças:**
- `"web"` → `"installed"`
- `"redirect_uris"` → pode manter ou remover (não é obrigatório para "installed")

#### Opção 2: Criar Novo OAuth Client (Recomendado)

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Vá em **APIs & Services** > **Credentials**
3. Clique em **Create Credentials** > **OAuth client ID**
4. Selecione **Desktop app** (não Web app)
5. Baixe o novo arquivo JSON
6. Substitua o arquivo atual

### 🚀 Próximos Passos

1. **Criar/Editar o arquivo `.env`** com as configurações acima
2. **Instalar dependência**:
   ```bash
   cd services/ai-service/agno_agente_horta_multitrem
   uv pip install tzlocal
   ```
3. **Executar o agente**:
   ```bash
   uv run python horta_organica_agent.py
   ```
4. **Na primeira execução**, o navegador abrirá para autorização OAuth
5. **Após autorizar**, o token será salvo em `token.json`

### ✅ Verificação

Após executar, verifique se:
- O arquivo `token.json` foi criado (não faça commit deste arquivo!)
- Não há erros de autenticação nos logs
- Os eventos estão sendo criados no Google Calendar

### 📚 Mais Informações

Consulte `docs/GOOGLE_CALENDAR_CONFIG.md` para documentação completa.
