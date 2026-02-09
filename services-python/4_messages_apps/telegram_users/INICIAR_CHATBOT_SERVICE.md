# Como Iniciar o Chatbot Service

## Problema

O erro "All connection attempts failed" indica que o **Chatbot Service não está rodando** na porta 8002.

O Telegram Service está funcionando corretamente e recebendo mensagens, mas não consegue se comunicar com o Chatbot Service.

## Solução

### 1. Navegar para o diretório do Chatbot Service

```bash
cd 3_chatbot_service
```

### 2. Verificar se o arquivo .env existe

```bash
# Se não existir, copiar do exemplo
cp env.example .env
```

### 3. Iniciar o Chatbot Service

**Opção 1: Usando o script de desenvolvimento**
```bash
python start_dev.py
```

**Opção 2: Usando uvicorn diretamente**
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

**Opção 3: Usando main.py**
```bash
python main.py
```

### 4. Verificar se está rodando

Abra outro terminal e teste:

```bash
curl http://localhost:8002/health
```

Deve retornar:
```json
{
  "status": "healthy",
  "service": "chatbot_service"
}
```

## Arquitetura

```
Telegram → Telegram Service (Porta 8021) → Chatbot Service (Porta 8002) → AI Service (Porta 8003)
```

## Ordem de Inicialização Recomendada

1. **AI Service** (porta 8003) - se necessário
2. **Chatbot Service** (porta 8002) - **OBRIGATÓRIO**
3. **Telegram Service** (porta 8021) - já está rodando

## Verificação Rápida

Execute este comando para verificar todos os serviços:

```bash
# Verificar Telegram Service
curl http://localhost:8021/health

# Verificar Chatbot Service
curl http://localhost:8002/health

# Verificar AI Service (se necessário)
curl http://localhost:8003/health
```

## Após Iniciar o Chatbot Service

1. O Telegram Service automaticamente conseguirá se comunicar com ele
2. Envie uma nova mensagem no Telegram
3. A mensagem deve ser processada corretamente
