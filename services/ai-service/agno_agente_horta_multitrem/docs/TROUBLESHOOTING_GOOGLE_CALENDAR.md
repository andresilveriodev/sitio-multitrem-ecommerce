# 🔧 Troubleshooting - Google Calendar

## ✅ Verificação de Inicialização

Quando você executa o agente, você deve ver uma das seguintes mensagens:

### ✅ Sucesso
```
✅ Google Calendar Tools inicializado com sucesso!
```

### ⚠️ Aviso (Arquivo não encontrado)
```
⚠️ Aviso: Arquivo de credenciais não encontrado: client_secret_2_707216253310-iikqnhv3eu0r2d941ljc3fa6reh7m6hr.apps.googleusercontent.com.json
   O agente funcionará normalmente, mas não criará eventos no Google Calendar.
   Configure o arquivo de credenciais para habilitar a integração com Google Calendar.
```

### ⚠️ Aviso (Erro na inicialização)
```
⚠️ Aviso: Erro ao inicializar Google Calendar Tools: [mensagem do erro]
   O agente funcionará normalmente, mas não criará eventos no Google Calendar.
   Verifique a configuração do Google Calendar se precisar desta funcionalidade.
```

## 🔍 Problemas Comuns e Soluções

### 1. Arquivo de Credenciais Não Encontrado

**Sintoma:**
```
⚠️ Aviso: Arquivo de credenciais não encontrado
```

**Solução:**
1. Verifique se o arquivo JSON está na pasta do projeto:
   ```
   services/ai-service/agno_agente_horta_multitrem/
   ```
2. Verifique o nome do arquivo no `.env`:
   ```env
   GOOGLE_CREDENTIALS_PATH=client_secret_2_707216253310-iikqnhv3eu0r2d941ljc3fa6reh7m6hr.apps.googleusercontent.com.json
   ```
3. O nome do arquivo deve corresponder exatamente ao configurado no `.env`

### 2. Erro de Formato do JSON

**Sintoma:**
```
⚠️ Aviso: Erro ao inicializar Google Calendar Tools: Invalid credentials
```

**Solução:**
1. Verifique se o arquivo JSON tem o formato correto:
   ```json
   {
     "installed": {
       "client_id": "...",
       "client_secret": "...",
       ...
     }
   }
   ```
2. Se o arquivo tiver formato "web", converta para "installed":
   - Mude `"web"` para `"installed"`
   - Ajuste `"redirect_uris"` se necessário

### 3. Erro de Autenticação OAuth

**Sintoma:**
- Na primeira execução, o navegador não abre para autorização
- Erro ao criar eventos: "Token expired" ou "Insufficient permissions"

**Solução:**
1. Delete o arquivo `token.json` se existir
2. Execute o agente novamente
3. O navegador deve abrir automaticamente para autorização
4. Faça login e autorize o acesso ao Google Calendar
5. O token será salvo automaticamente

### 4. Erro ao Criar Eventos

**Sintoma:**
- Agendamento é salvo no banco, mas evento não é criado no Google Calendar
- Erro: "Insufficient permissions" ou "Invalid scope"

**Solução:**
1. Verifique se o escopo está correto no código:
   ```python
   scopes=["https://www.googleapis.com/auth/calendar"]  # Escopo de escrita
   ```
2. Verifique se autorizou o acesso na primeira execução
3. Delete `token.json` e autorize novamente

### 5. Agente Funciona, Mas Google Calendar Não

**Sintoma:**
- Agente inicia normalmente
- Agendamentos são salvos no banco
- Mas eventos não aparecem no Google Calendar

**Verificação:**
1. Verifique os logs do agente ao criar um agendamento
2. Procure por mensagens de erro relacionadas ao `create_event`
3. Verifique se a ferramenta `create_event` está disponível:
   - Se não estiver, o Google Calendar Tools não foi inicializado corretamente

## 🧪 Teste Manual

Para testar se o Google Calendar está funcionando:

1. **Execute o agente:**
   ```bash
   uv run python horta_organica_agent.py
   ```

2. **Verifique a mensagem de inicialização:**
   - Deve aparecer: `✅ Google Calendar Tools inicializado com sucesso!`

3. **Faça um teste completo:**
   - Crie um pedido
   - Agende uma entrega
   - Verifique se o evento aparece no Google Calendar

4. **Verifique o Google Calendar:**
   - Acesse [Google Calendar](https://calendar.google.com/)
   - Procure por eventos com título "Entrega: [Nome do Cliente]"
   - Verifique se todas as informações estão corretas

## 📝 Logs Úteis

Quando o agente tenta criar um evento, você verá nos logs:

### Sucesso:
```
Evento criado no Google Calendar com sucesso!
```

### Erro:
```
Erro ao criar evento no Google Calendar: [mensagem do erro]
Agendamento confirmado! (Erro ao criar evento no calendário, mas está salvo no sistema)
```

## 🔒 Segurança

⚠️ **IMPORTANTE:**
- Não compartilhe o arquivo `token.json`
- Não faça commit do arquivo `token.json` no Git
- Mantenha o arquivo de credenciais JSON seguro
- Use variáveis de ambiente para configurações sensíveis em produção

## 📚 Mais Informações

- [Guia de Configuração Completo](./GOOGLE_CALENDAR_CONFIG.md)
- [Configuração do .env](../CONFIGURAR_ENV.md)

## 🆘 Ainda com Problemas?

Se nenhuma das soluções acima funcionar:

1. Verifique se todas as dependências estão instaladas:
   ```bash
   uv pip install tzlocal
   ```

2. Verifique se o arquivo `.env` está configurado corretamente

3. Verifique se o Google Calendar API está habilitada no Google Cloud Console

4. Verifique se o OAuth client está configurado corretamente (tipo: Desktop app)

5. Consulte a documentação do Agno Framework para mais detalhes sobre GoogleCalendarTools
