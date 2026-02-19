# CRUD de Produtos via Telegram

Sistema completo para cadastrar, listar, editar e deletar produtos do e-commerce via Telegram.

## 📋 Funcionalidades

- ✅ **Cadastrar Produtos** - Fluxo conversacional guiado
- ✅ **Listar Produtos** - Visualizar todos os produtos cadastrados
- ✅ **Editar Produtos** - Atualizar campos específicos
- ✅ **Deletar Produtos** - Soft delete (marca como inativo)
- ✅ **Autenticação** - Validação via token do Telegram
- ✅ **Validação de Segurança** - Sanitização de entrada

## 🏗️ Arquitetura

```
Telegram → /chatbot/process-message-authenticated → ProductConversationFlow → ProductService → PostgreSQL
```

### Componentes Criados

1. **models/product_models.py** - Modelos SQLAlchemy e Pydantic
2. **services/database_service.py** - Conexão com PostgreSQL
3. **services/product_service.py** - CRUD de produtos
4. **services/product_conversation_flow.py** - Fluxo conversacional (state machine)
5. **routes/telegram_router.py** - Rota do Telegram

## 🚀 Configuração

### 1. Configurar Banco de Dados

No arquivo `.env`:
```env
DATABASE_URL=postgresql://postgres:123456@localhost:5434/sitio_multitrem
```

### 2. Configurar Token do Telegram

No arquivo `.env`:
```env
TELEGRAM_BOT_TOKEN=seu_token_do_bot_telegram
```

### 3. Criar Tabela de Produtos

Execute o script de inicialização:
```bash
python scripts/init_products_table.py
```

## 📱 Comandos do Telegram

### Cadastrar Produto
```
/produto
ou
/cadastrar
ou
novo produto
```

O bot guiará você através de:
1. Nome do produto
2. Descrição (opcional - digite "pular")
3. Preço
4. Quantidade em estoque
5. SKU (opcional - digite "pular")
6. Categoria (opcional - digite "pular")
7. Confirmação

### Listar Produtos
```
/listar
ou
/produtos
ou
meus produtos
```

### Editar Produto
```
/editar
ou
/atualizar
ou
editar produto
```

Fluxo:
1. Escolha o produto pelo ID
2. Escolha o campo para editar (1-6)
3. Informe o novo valor

### Deletar Produto
```
/deletar
ou
/remover
ou
deletar produto
```

Fluxo:
1. Escolha o produto pelo ID
2. Confirme a deleção

### Cancelar Operação
```
/cancelar
ou
sair
```

## 🔧 Configuração do Webhook do Telegram

### 1. Obter Token do Bot

1. Crie um bot com [@BotFather](https://t.me/botfather)
2. Use `/newbot` e siga as instruções
3. Copie o token fornecido
4. Adicione no `.env` como `TELEGRAM_BOT_TOKEN`

### 2. Configurar Webhook

```bash
curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://seu-dominio.com/chatbot/process-message-authenticated",
    "secret_token": "seu_token_secreto"
  }'
```

### 3. Autenticação

O endpoint espera o token no header:
```
X-Telegram-Bot-Token: seu_token_aqui
```

Ou configure o webhook do Telegram para enviar o `secret_token` que será validado.

## 📊 Modelo de Dados

### Tabela: products

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    sku VARCHAR(100) UNIQUE,
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100) NOT NULL,  -- Telegram user_id
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🔒 Segurança

- ✅ Validação de entrada com `input_validator`
- ✅ Sanitização de dados
- ✅ Autenticação via token
- ✅ Validação de propriedade (usuário só edita seus produtos)
- ✅ Soft delete (não remove fisicamente)

## 📝 Exemplo de Uso

### Fluxo de Cadastro

```
Usuário: /produto
Bot: Vamos cadastrar um novo produto! Por favor, informe o NOME do produto:

Usuário: Notebook Dell
Bot: Ótimo! Nome: Notebook Dell. Agora informe a DESCRIÇÃO do produto (ou digite 'pular'):

Usuário: Notebook Dell Inspiron 15
Bot: Agora informe o PREÇO do produto (ex: 99.90):

Usuário: 2500.00
Bot: Preço: R$ 2500.00. Agora informe a QUANTIDADE EM ESTOQUE (ou digite '0'):

Usuário: 5
Bot: Estoque: 5 unidades. Agora informe o SKU do produto (ou digite 'pular'):

Usuário: DELL-001
Bot: Agora informe a CATEGORIA do produto (ou digite 'pular'):

Usuário: Eletrônicos
Bot: Resumo do produto: [mostra resumo]. Confirma o cadastro? (sim/não)

Usuário: sim
Bot: ✅ Produto cadastrado com sucesso! ID: 1, Nome: Notebook Dell, Preço: R$ 2500.00
```

## 🐛 Troubleshooting

### Erro: "Banco de dados não está conectado"

1. Verifique se o PostgreSQL está rodando
2. Verifique a `DATABASE_URL` no `.env`
3. Execute `python scripts/init_products_table.py`

### Erro: "Token inválido"

1. Verifique se `TELEGRAM_BOT_TOKEN` está no `.env`
2. Verifique se o token está correto
3. Em desenvolvimento, o sistema permite sem token (remova em produção!)

### Erro: "Tabela não existe"

Execute o script de inicialização:
```bash
python scripts/init_products_table.py
```

## 📚 Estrutura de Arquivos

```
bot_operations/
├── models/
│   └── product_models.py          # Modelos de dados
├── services/
│   ├── database_service.py        # Conexão PostgreSQL
│   ├── product_service.py          # CRUD de produtos
│   └── product_conversation_flow.py # Fluxo conversacional
├── routes/
│   └── telegram_router.py         # Rota do Telegram
└── scripts/
    └── init_products_table.py     # Script de inicialização
```

## 🎯 Próximos Passos

- [ ] Adicionar upload de imagens
- [ ] Adicionar busca de produtos
- [ ] Adicionar relatórios
- [ ] Adicionar notificações
- [ ] Melhorar validações
- [ ] Adicionar testes automatizados
