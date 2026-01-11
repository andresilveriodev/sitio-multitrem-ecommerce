# 🚀 Como Executar o Sistema - Guia Passo a Passo

## Pré-requisitos

Antes de executar, certifique-se de ter:

1. ✅ Python 3.12 instalado
2. ✅ UV instalado
3. ✅ OpenAI API Key

## Passo 1: Navegar até a Pasta do Projeto

Abra o terminal (PowerShell no Windows) e navegue até a pasta:

```bash
cd "c:\Users\ilumi\Desktop\En\Adriano\Criando Agentes de IA com Agno (1)\agente_horta_multitrem"
```

Ou se você já estiver na pasta principal:

```bash
cd agente_horta_multitrem
```

## Passo 2: Verificar se as Dependências Estão Instaladas

```bash
uv sync
```

Este comando irá instalar todas as dependências necessárias se ainda não estiverem instaladas.

## Passo 3: Configurar o Arquivo .env

Se você ainda não criou o arquivo `.env`:

```bash
# Windows PowerShell
copy env.example .env

# Linux/macOS
cp env.example .env
```

Depois, edite o arquivo `.env` e adicione sua chave da OpenAI:

```env
OPENAI_API_KEY=sk-proj-sua-chave-aqui
DATABASE_PATH=tmp/data.db
```

## Passo 4: Inicializar o Banco de Dados (Primeira Vez)

Na primeira execução, você precisa inicializar o banco de dados:

```bash
uv run python init_db.py
```

Isso criará as tabelas e populará com produtos iniciais.

## Passo 5: Executar o Script de Exemplos

Agora você pode executar o script de exemplos:

```bash
uv run python exemplos_uso.py
```

## 📋 O que Esperar

Quando você executar `exemplos_uso.py`, verá um menu interativo:

```
============================================================
🌱 SISTEMA DE AGENTES - HORTA ORGÂNICA
============================================================

Escolha um exemplo para executar:
  1. Dúvida sobre produto orgânico
  2. Consulta de produtos disponíveis
  3. Pedido completo (cadastro + pedido + pagamento + entrega)
  4. Suporte técnico
  5. Estatísticas do sistema
  6. Listar dados cadastrados
  7. Executar todos os exemplos
  0. Sair

Digite sua escolha:
```

## 🔧 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'agno'"

**Solução:**
```bash
uv sync
```

### Erro: "AuthenticationError: Incorrect API key"

**Solução:**
1. Verifique se o arquivo `.env` existe
2. Verifique se a chave está correta no arquivo `.env`
3. Certifique-se de que não há espaços extras

### Erro: "No such file or directory: 'tmp/data.db'"

**Solução:**
```bash
# Criar diretório se não existir
mkdir tmp

# Executar inicialização
uv run python init_db.py
```

### Erro: "uv: command not found"

**Solução:**
Instale o UV primeiro:

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 📝 Comandos Alternativos

Se você preferir usar Python diretamente (sem UV):

```bash
# Instalar dependências manualmente
pip install agno openai python-dotenv sqlalchemy fastapi uvicorn ddgs

# Executar o script
python exemplos_uso.py
```

## 🎯 Outros Scripts Disponíveis

### Consultar Dados do Banco

```bash
uv run python consultas.py
```

### Executar o Sistema Principal

```bash
uv run python horta_organica_agent.py
```

Depois acesse: `http://localhost:8000`

## ✅ Checklist Antes de Executar

- [ ] Estou na pasta `agente_horta_multitrem`
- [ ] Executei `uv sync` para instalar dependências
- [ ] Criei o arquivo `.env` com minha API key
- [ ] Executei `uv run python init_db.py` (primeira vez)
- [ ] Tenho conexão com a internet (para API da OpenAI)

## 💡 Dica

Se você encontrar algum erro, verifique:
1. Se está na pasta correta
2. Se o arquivo `.env` existe e tem a API key
3. Se o banco de dados foi inicializado
4. Se tem créditos na conta OpenAI
