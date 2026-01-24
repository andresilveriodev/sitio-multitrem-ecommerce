# 🔧 Como Regenerar o Token do Google Calendar

## Problema
O token.json estava com formato incorreto nos scopes, causando o erro:
```
invalid_scope: Some requested scopes were invalid. {invalid=[read, write]}
```

## Solução

### Passo 1: Deletar o token antigo
O arquivo `token.json` já foi deletado automaticamente. Se ainda existir, delete manualmente:
```bash
rm token.json
# ou no Windows:
del token.json
```

### Passo 2: Regenerar o token
Execute o script de geração:
```bash
cd services/ai-service/agno_agente_horta_multitrem
uv run python gerar_token_google.py
```

Ou se estiver usando o ambiente virtual da raiz:
```bash
python gerar_token_google.py
```

### Passo 3: Autorizar no navegador
1. O script abrirá o navegador automaticamente
2. Faça login com sua conta Google
3. Autorize o acesso ao Google Calendar
4. O token será salvo automaticamente

### Passo 4: Reiniciar o AgentOS
Após gerar o token, reinicie o AgentOS:
```bash
uv run python horta_organica_agent.py
```

### Verificação
Você deve ver a mensagem:
```
✅ Google Calendar Tools inicializado com sucesso!
```

## Formato Correto do Token

O token.json deve ter os scopes como um **array**, não como dicionário:

✅ **Correto:**
```json
{
  "scopes": ["https://www.googleapis.com/auth/calendar"]
}
```

❌ **Incorreto:**
```json
{
  "scopes": {
    "read": "https://www.googleapis.com/auth/calendar.readonly",
    "write": "https://www.googleapis.com/auth/calendar"
  }
}
```

## Se o Erro Persistir

1. Verifique se o arquivo de credenciais existe:
   - `client_secret_2_707216253310-iikqnhv3eu0r2d941ljc3fa6reh7m6hr.apps.googleusercontent.com.json`

2. Verifique se o arquivo de credenciais está no formato "installed" (Desktop app)

3. Verifique se a Google Calendar API está habilitada no Google Cloud Console

4. Verifique se os scopes estão configurados corretamente no OAuth consent screen:
   - `https://www.googleapis.com/auth/calendar`
