# Chatbot Middleware API

Middleware FastAPI para chatbot com integração de IA usando OpenAI GPT.

## 🚀 Características

- **FastAPI**: Framework web moderno e rápido
- **Socket.IO**: Comunicação em tempo real
- **PostgreSQL**: Banco de dados robusto
- **OpenAI Integration**: Integração com GPT-4/GPT-3.5
- **SQLAlchemy**: ORM para Python
- **Logging**: Sistema completo de logs

## 📁 Estrutura do Projeto

```
chatbot_middleware/
├── .env
├── requirements.txt
├── main.py
├── README.md
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── logger.py
│   ├── socketio_instance.py
│   └── routers/
│       ├── __init__.py
│       ├── chatbot_resource.py
│       └── ai_resource.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── conversation.py
│   └── user.py
└── services/
    ├── __init__.py
    ├── chatbot_service.py
    └── ai_service.py
```

## 🛠️ Instalação

### 1. Clone o repositório
```bash
git clone <repository-url>
cd b3_fastapi_ai
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv
```

### 3. Ative o ambiente virtual
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 4. Instale as dependências
```bash
pip install -r requirements.txt
```

### 5. Configure as variáveis de ambiente
Edite o arquivo `.env` com suas configurações:

```env
DATABASE_URI=postgresql://postgres:123456@localhost:5434/chatbot_middleware
HTTP_PORT=5000
CORS_ORIGINS=*
OPENAI_API_KEY=your_openai_api_key_here
AI_MODEL=gpt-4
LOG_LEVEL=INFO
```

### 6. Configure o banco de dados PostgreSQL
Certifique-se de que o PostgreSQL está rodando e crie o banco de dados:

```sql
CREATE DATABASE chatbot_middleware;
```

## 🚀 Execução

### Desenvolvimento
```bash
uvicorn main:application --port 5000 --reload
```

### Produção
```bash
uvicorn main:application --host 0.0.0.0 --port 5000
```

## 📚 API Endpoints

### Principais Endpoints

- `GET /` - Informações da API
- `GET /health` - Status de saúde
- `GET /docs` - Documentação Swagger

### Chatbot Endpoints

- `POST /chatbot/users` - Criar usuário
- `GET /chatbot/users/{user_id}` - Buscar usuário
- `POST /chatbot/conversations` - Criar conversa
- `GET /chatbot/conversations/{conversation_id}` - Buscar conversa
- `GET /chatbot/users/{user_id}/conversations` - Listar conversas do usuário
- `GET /chatbot/conversations/{conversation_id}/messages` - Listar mensagens
- `POST /chatbot/chat` - Enviar mensagem e receber resposta da IA

### AI Endpoints

- `POST /ai/generate` - Gerar resposta da IA
- `POST /ai/generate/stream` - Gerar resposta em streaming
- `GET /ai/models` - Listar modelos disponíveis
- `POST /ai/validate` - Validar conexão com OpenAI

## 🔧 Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URI` | URI de conexão PostgreSQL | - |
| `HTTP_PORT` | Porta do servidor | 5000 |
| `CORS_ORIGINS` | Origens permitidas CORS | * |
| `OPENAI_API_KEY` | Chave da API OpenAI | - |
| `AI_MODEL` | Modelo de IA a usar | gpt-4 |
| `LOG_LEVEL` | Nível de log | INFO |

## 📝 Uso

### Exemplo de uso básico:

1. **Criar um usuário:**
```bash
curl -X POST "http://localhost:5000/chatbot/users" \
     -H "Content-Type: application/json" \
     -d '{"username": "user1", "email": "user1@example.com"}'
```

2. **Criar uma conversa:**
```bash
curl -X POST "http://localhost:5000/chatbot/conversations" \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1, "title": "Minha primeira conversa"}'
```

3. **Enviar mensagem:**
```bash
curl -X POST "http://localhost:5000/chatbot/chat" \
     -H "Content-Type: application/json" \
     -d '{"conversation_id": 1, "message": "Olá, como você está?"}'
```

## 🔍 Logs

Os logs são salvos na pasta `logs/` e também exibidos no console. O formato inclui:
- Timestamp
- Nome do logger
- Nível de log
- Função e linha
- Mensagem

## 🛡️ Segurança

- Configure adequadamente as variáveis de ambiente
- Use HTTPS em produção
- Mantenha a chave da OpenAI segura
- Configure CORS adequadamente para produção

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.