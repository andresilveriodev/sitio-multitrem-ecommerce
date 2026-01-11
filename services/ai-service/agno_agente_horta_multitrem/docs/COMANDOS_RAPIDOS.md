# ⚡ Comandos Rápidos - Agente Horta Multitrem

## ✅ O que já foi feito:

1. ✅ UV instalado
2. ✅ Dependências instaladas (`uv sync`)
3. ✅ Arquivo `.env` criado
4. ✅ Banco de dados inicializado

## 🚀 Para Executar Agora:

### Opção 1: Executar Exemplos (Recomendado)

```powershell
# Adicionar UV ao PATH (necessário a cada nova sessão do PowerShell)
$env:Path = "C:\Users\ilumi\.local\bin;$env:Path"

# Navegar até a pasta
cd "c:\Users\ilumi\Desktop\En\Adriano\Criando Agentes de IA com Agno (1)\agente_horta_multitrem"

# Executar exemplos
uv run python exemplos_uso.py
```

### Opção 2: Usar o Script Automático

```powershell
cd "c:\Users\ilumi\Desktop\En\Adriano\Criando Agentes de IA com Agno (1)\agente_horta_multitrem"
.\EXECUTAR_AGORA.ps1
```

## ⚠️ IMPORTANTE: Configurar API Key

Antes de executar, você **DEVE** editar o arquivo `.env` e adicionar sua chave da OpenAI:

1. Abra o arquivo `.env` na pasta do projeto
2. Substitua `sk-proj-sua-chave-aqui` pela sua chave real
3. Salve o arquivo

**Onde obter a API Key:**
- Acesse: https://platform.openai.com/api-keys
- Faça login
- Crie uma nova chave
- Copie e cole no arquivo `.env`

## 📋 Outros Comandos Úteis

### Consultar Dados do Banco

```powershell
$env:Path = "C:\Users\ilumi\.local\bin;$env:Path"
cd "c:\Users\ilumi\Desktop\En\Adriano\Criando Agentes de IA com Agno (1)\agente_horta_multitrem"
uv run python consultas.py
```

### Executar o Sistema Principal (Interface Web)

```powershell
$env:Path = "C:\Users\ilumi\.local\bin;$env:Path"
cd "c:\Users\ilumi\Desktop\En\Adriano\Criando Agentes de IA com Agno (1)\agente_horta_multitrem"
uv run python horta_organica_agent.py
```

Depois acesse: `http://localhost:8000`

## 🔧 Adicionar UV ao PATH Permanentemente

Para não precisar adicionar o UV ao PATH toda vez, adicione ao seu perfil do PowerShell:

```powershell
# Editar perfil
notepad $PROFILE

# Adicionar esta linha:
$env:Path = "C:\Users\ilumi\.local\bin;$env:Path"
```

## ✅ Checklist Antes de Executar

- [ ] Arquivo `.env` configurado com OPENAI_API_KEY
- [ ] Banco de dados inicializado (já feito ✅)
- [ ] Dependências instaladas (já feito ✅)
- [ ] UV no PATH (ou usar `$env:Path = "C:\Users\ilumi\.local\bin;$env:Path"`)

## 🎯 Próximo Passo

**Configure sua API Key no arquivo `.env` e execute:**

```powershell
$env:Path = "C:\Users\ilumi\.local\bin;$env:Path"
cd "c:\Users\ilumi\Desktop\En\Adriano\Criando Agentes de IA com Agno (1)\agente_horta_multitrem"
uv run python exemplos_uso.py
```
