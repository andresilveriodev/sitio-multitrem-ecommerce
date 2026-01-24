# 📅 Configuração do Google Calendar

Este guia explica como configurar a integração do Google Calendar com o agente do Sítio Multitrem.

## 📋 Pré-requisitos

1. **Conta Google** com acesso ao Google Calendar
2. **Projeto no Google Cloud Console**
3. **Google Calendar API habilitada**
4. **Credenciais OAuth 2.0 configuradas**

## 🔧 Passo 1: Configurar Google Cloud Console

### 1.1. Criar/Selecionar Projeto

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Anote o **Project ID**

### 1.2. Habilitar Google Calendar API

1. No menu lateral, vá em **APIs & Services** > **Library**
2. Busque por "Google Calendar API"
3. Clique em **Enable**

### 1.3. Configurar OAuth 2.0

1. Vá em **APIs & Services** > **Credentials**
2. Clique em **Create Credentials** > **OAuth client ID**
3. Se for a primeira vez, configure a **OAuth consent screen**:
   - Tipo: **Internal** (para uso interno) ou **External** (para uso público)
   - Preencha os dados obrigatórios
   - Adicione os escopos: `https://www.googleapis.com/auth/calendar`
4. Crie o **OAuth client ID**:
   - Tipo de aplicação: **Desktop app** (⚠️ IMPORTANTE: Use Desktop app, não Web app)
   - Nome: "Sítio Multitrem Calendar"
   - Clique em **Create**
5. Baixe o arquivo JSON de credenciais

### 1.4. Formato do Arquivo JSON

O arquivo JSON deve ter o formato **"installed"** (Desktop app):

```json
{
  "installed": {
    "client_id": "seu-client-id.apps.googleusercontent.com",
    "project_id": "seu-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "seu-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

⚠️ **IMPORTANTE**: Se você tem um arquivo JSON do tipo "web", você precisa:
1. Criar um novo OAuth client ID do tipo "Desktop app" no Google Cloud Console
2. Baixar o novo arquivo JSON
3. Substituir o arquivo atual

## 📁 Passo 2: Configurar Arquivos no Projeto

### 2.1. Colocar Arquivo de Credenciais

1. Coloque o arquivo JSON de credenciais na pasta do projeto:
   ```
   services/ai-service/agno_agente_horta_multitrem/
   ```

2. O nome do arquivo deve corresponder ao configurado no `.env`:
   ```
   GOOGLE_CREDENTIALS_PATH=client_secret_2_707216253310-iikqnhv3eu0r2d941ljc3fa6reh7m6hr.apps.googleusercontent.com.json
   ```

### 2.2. Configurar Variáveis de Ambiente

Edite o arquivo `.env` (ou crie a partir do `env.example`):

```env
# Google Calendar Configuration
GOOGLE_CREDENTIALS_PATH=client_secret_2_707216253310-iikqnhv3eu0r2d941ljc3fa6reh7m6hr.apps.googleusercontent.com.json
GOOGLE_TOKEN_PATH=token.json
GOOGLE_CALENDAR_ID=primary
```

**Variáveis:**
- `GOOGLE_CREDENTIALS_PATH`: Caminho para o arquivo JSON de credenciais
- `GOOGLE_TOKEN_PATH`: Caminho onde o token OAuth será salvo (gerado automaticamente)
- `GOOGLE_CALENDAR_ID`: ID do calendário (use "primary" para o calendário principal)

## 🚀 Passo 3: Instalar Dependências

Instale a dependência `tzlocal`:

```bash
cd services/ai-service/agno_agente_horta_multitrem
uv pip install tzlocal
# ou
pip install tzlocal
```

## ✅ Passo 4: Primeira Execução e Autorização

1. Execute o agente:
   ```bash
   uv run python horta_organica_agent.py
   ```

2. Na primeira execução, o sistema abrirá automaticamente o navegador para autorização OAuth

3. Faça login com sua conta Google e autorize o acesso ao Google Calendar

4. O token será salvo automaticamente no arquivo `token.json`

5. ⚠️ **IMPORTANTE**: Não compartilhe o arquivo `token.json` - ele contém credenciais de acesso

## 📅 Como Funciona a Integração

### Fluxo Automático

1. **Cliente faz pedido** → Agente cria pedido no banco de dados
2. **Cliente agenda entrega** → Agente chama `agendar_entrega()`
3. **Após agendamento bem-sucedido** → Agente automaticamente:
   - Busca dados completos do pedido (cliente, produtos, pagamento)
   - Cria evento no Google Calendar com:
     - **Título**: "Entrega: [Nome do Cliente]"
     - **Data/Hora**: Data e horário da entrega
     - **Localização**: Endereço completo
     - **Descrição**: 
       - Nome do cliente
       - WhatsApp
       - Status de pagamento (PAGO/PENDENTE)
       - ID do pedido
       - Lista de produtos

### Informações no Evento

O evento criado no Google Calendar contém:

```
Título: Entrega: Maria da Silva

Data/Hora: 20/01/2025 08:00 - 09:00

Localização: Rua das Flores, 123, Apto 45 - Bairro Central - Goiânia/GO

Descrição:
Cliente: Maria da Silva
WhatsApp: +55 62 98122-5993
Status de Pagamento: PENDENTE
Pedido ID: 1
Produtos: 10x Alface Americana, 1x Coentro, 30 ovos caipiras
```

## 🔍 Verificar Configuração

### Testar Manualmente

Você pode testar a criação de eventos usando o arquivo `test_google_calendar.py`:

```bash
uv run python test_google_calendar.py
```

### Verificar no Google Calendar

1. Acesse [Google Calendar](https://calendar.google.com/)
2. Procure por eventos com o título "Entrega: [Nome]"
3. Verifique se todas as informações estão corretas

## ⚠️ Troubleshooting

### Erro: "Invalid credentials"

- Verifique se o arquivo JSON está no formato "installed" (não "web")
- Verifique se o caminho no `.env` está correto
- Tente gerar novas credenciais no Google Cloud Console

### Erro: "Token expired"

- Delete o arquivo `token.json`
- Execute o agente novamente para gerar novo token

### Erro: "Insufficient permissions"

- Verifique se o escopo `https://www.googleapis.com/auth/calendar` está configurado
- Verifique se autorizou o acesso na primeira execução

### Evento não é criado

- Verifique os logs do agente para ver se há erros
- Verifique se `agendar_entrega()` retornou sucesso antes de criar o evento
- Verifique se o formato da data/hora está correto (ISO 8601)

## 📚 Referências

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Agno Framework Documentation](https://agno.com/docs)

## 🔒 Segurança

⚠️ **IMPORTANTE**: 
- Não compartilhe o arquivo `token.json`
- Não faça commit do arquivo `token.json` no Git (deve estar no `.gitignore`)
- Mantenha o arquivo de credenciais JSON seguro
- Use variáveis de ambiente para configurações sensíveis em produção
