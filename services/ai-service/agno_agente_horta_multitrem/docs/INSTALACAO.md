# 🚀 Guia de Instalação - Agente Horta Multitrem

## Passo a Passo Completo

### 1. Pré-requisitos

Certifique-se de ter instalado:
- Python 3.12 (ou superior, mas < 3.13)
- UV (gerenciador de pacotes Python)

### 2. Instalar UV (se ainda não tiver)

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Navegar até o Projeto

```bash
cd agente_horta_multitrem
```

### 4. Instalar Dependências

```bash
uv sync
```

Isso irá instalar todas as dependências listadas no `pyproject.toml`:
- agno
- openai
- fastapi
- uvicorn
- sqlalchemy
- python-dotenv
- ddgs
- chromadb
- pandas
- pypdf

### 5. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e configure sua API key:

```bash
# Windows
copy env.example .env

# Linux/macOS
cp env.example .env
```

Edite o arquivo `.env` e adicione sua chave da OpenAI:

```env
OPENAI_API_KEY=sk-proj-sua-chave-aqui
DATABASE_PATH=tmp/data.db
```

**Onde obter a API Key:**
1. Acesse https://platform.openai.com/api-keys
2. Faça login na sua conta OpenAI
3. Clique em "Create new secret key"
4. Copie a chave e cole no arquivo `.env`

### 6. Inicializar o Banco de Dados

Execute o script de inicialização:

```bash
uv run python init_db.py
```

Isso irá:
- Criar todas as tabelas necessárias
- Popular o banco com produtos iniciais

### 7. Executar o Sistema

```bash
uv run python horta_organica_agent.py
```

O sistema irá:
- Inicializar o banco de dados automaticamente
- Popular produtos iniciais (se necessário)
- Iniciar o servidor na porta 8000

### 8. Acessar a Interface

Abra seu navegador e acesse:

```
http://localhost:8000
```

Você verá a interface do AgentOS com:
- Lista de agentes disponíveis
- Interface de chat interativa
- Histórico de conversas

## ✅ Verificação

Para verificar se tudo está funcionando:

1. **Verificar dependências instaladas:**
   ```bash
   uv pip list
   ```

2. **Verificar banco de dados:**
   ```bash
   # O arquivo deve existir em tmp/data.db
   ls tmp/data.db  # Linux/macOS
   dir tmp\data.db  # Windows
   ```

3. **Testar importação:**
   ```bash
   uv run python -c "from models import init_db; print('✅ Models OK')"
   uv run python -c "from db_tools import consultar_produtos_disponiveis; print('✅ Tools OK')"
   ```

## 🔧 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'agno'"

**Solução:**
```bash
uv sync
```

### Erro: "AuthenticationError: Incorrect API key"

**Solução:**
- Verifique se o arquivo `.env` existe
- Verifique se a chave começa com `sk-`
- Certifique-se de que não há espaços extras na chave

### Erro: "Address already in use: 8000"

**Solução:**
- Feche outros processos usando a porta 8000
- Ou use outra porta editando o código

### Erro ao criar banco de dados

**Solução:**
```bash
# Criar diretório manualmente
mkdir -p tmp  # Linux/macOS
mkdir tmp     # Windows

# Executar novamente
uv run python init_db.py
```

## 📝 Próximos Passos

Após a instalação bem-sucedida:

1. ✅ Teste o agente principal fazendo perguntas sobre produtos orgânicos
2. ✅ Teste o team fazendo um pedido completo
3. ✅ Verifique os dados salvos no banco de dados
4. ✅ Consulte a documentação completa em `docs/DOCUMENTACAO_HORTA_ORGANICA.md`

## 🎉 Pronto!

Seu sistema de agentes IA para horta orgânica está pronto para uso!
