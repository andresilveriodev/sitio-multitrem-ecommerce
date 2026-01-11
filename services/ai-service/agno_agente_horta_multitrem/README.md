# 🌱 Sítio Multitrem - Sistema de Atendimento IA

Sistema completo de atendimento automatizado para o **Sítio Multitrem**, produtor de alimentos orgânicos certificados, utilizando **Agno Framework** com um agente único responsável por todo o processo.

## 🚀 Início Rápido

### 1. Instalar dependências

```bash
uv sync
```

### 2. Configurar ambiente

Copie o arquivo de exemplo e configure sua API key:

```bash
copy env.example .env
# Edite o arquivo .env e adicione sua OPENAI_API_KEY
```

### 3. Executar o sistema

```bash
uv run python horta_organica_agent.py
```

### 4. Acessar a interface

Abra seu navegador em: `http://localhost:8000`

## 📚 Documentação Completa

Toda a documentação está organizada na pasta [`docs/`](./docs/):

- **[Documentação Completa](./docs/DOCUMENTACAO_HORTA_ORGANICA.md)**: Guia completo do sistema
- **[Guia de Instalação](./docs/INSTALACAO.md)**: Passo a passo de instalação
- **[Como Executar](./docs/COMO_EXECUTAR.md)**: Como executar o sistema
- **[Exemplos de Uso](./docs/EXEMPLOS.md)**: Exemplos práticos
- **[Prompts Atualizados](./docs/PROMPTS_ATUALIZADOS.md)**: Detalhes dos prompts
- **[Teste Rápido](./docs/TESTE_RAPIDO.md)**: Guia de testes
- **[Comandos Rápidos](./docs/COMANDOS_RAPIDOS.md)**: Referência rápida

## 🏗️ Arquitetura

- **Agente Único - Assistente Sítio Multitrem**: Responsável por todo o atendimento ao cliente:
  - 🛒 **Vendas**: Apresenta produtos, calcula descontos e cria pedidos
  - 💬 **Suporte**: Tira dúvidas sobre benefícios, receitas e armazenamento
  - 📅 **Agendamento**: Organiza entregas e coleta endereços completos
  - 💳 **Pagamento**: Processa pagamentos (PIX, cartão, dinheiro)

## 🌟 Funcionalidades

✅ **Sistema Completo** com informações reais do Sítio Multitrem:
- Lista completa de produtos e preços (Hortaliças, Ovos Caipiras, Kits)
- Regras de desconto (20% para pedidos acima de 3 hortaliças)
- Frete grátis para pedidos acima de R$ 30,00
- Horários de entrega (Segunda, Quarta, Sexta e Sábado - manhã)
- Métodos de pagamento (PIX, Cartão de Crédito, Débito, Dinheiro)
- Fluxo completo: Vendas → Agendamento → Pagamento
- Suporte a dúvidas sobre produtos orgânicos

📄 Veja detalhes completos em: **[docs/PROMPTS_ATUALIZADOS.md](./docs/PROMPTS_ATUALIZADOS.md)**

## 📦 Estrutura do Projeto

```
agente_horta_multitrem/
├── horta_organica_agent.py    # Arquivo principal
├── models.py                   # Modelos SQLAlchemy
├── db_tools.py                 # Tools com persistência real
├── utils.py                    # Utilitários e consultas
├── init_db.py                  # Script de inicialização
├── exemplos_uso.py             # Exemplos interativos
├── consultas.py                # Script de consultas ao banco
├── README.md                   # Este arquivo
├── pyproject.toml              # Dependências
├── .env                        # Configurações (não versionado)
├── docs/                       # 📚 Toda a documentação
│   ├── DOCUMENTACAO_HORTA_ORGANICA.md
│   ├── INSTALACAO.md
│   ├── COMO_EXECUTAR.md
│   ├── EXEMPLOS.md
│   ├── PROMPTS_ATUALIZADOS.md
│   ├── TESTE_RAPIDO.md
│   └── COMANDOS_RAPIDOS.md
├── tmp/                        # Banco de dados SQLite
├── tools/                      # Tools customizadas
└── files/                      # Documentos e PDFs
```

## 🛠️ Tecnologias

- **Agno Framework**: Framework para criação de agentes IA
- **OpenAI GPT**: Modelos de linguagem
- **SQLite**: Banco de dados
- **FastAPI**: Servidor web
- **SQLAlchemy**: ORM para banco de dados

## 📚 Documentação e Exemplos

Toda a documentação está na pasta [`docs/`](./docs/):

- **[Documentação Completa](./docs/DOCUMENTACAO_HORTA_ORGANICA.md)**: Guia completo do sistema
- **[Guia de Instalação](./docs/INSTALACAO.md)**: Passo a passo de instalação
- **[Como Executar](./docs/COMO_EXECUTAR.md)**: Como executar o sistema
- **[Exemplos de Uso](./docs/EXEMPLOS.md)**: Exemplos práticos
- **[Prompts Atualizados](./docs/PROMPTS_ATUALIZADOS.md)**: ⭐ Detalhes dos prompts
- **[Teste Rápido](./docs/TESTE_RAPIDO.md)**: Guia de testes
- **[Comandos Rápidos](./docs/COMANDOS_RAPIDOS.md)**: Referência rápida

## 🎮 Scripts Úteis

### Executar Exemplos Interativos
```bash
uv run python exemplos_uso.py
```

### Consultar Dados do Banco
```bash
uv run python consultas.py
```

### Inicializar Banco de Dados
```bash
uv run python init_db.py
```

## 📝 Licença

Este projeto é fornecido como exemplo educacional. Use e modifique livremente.
