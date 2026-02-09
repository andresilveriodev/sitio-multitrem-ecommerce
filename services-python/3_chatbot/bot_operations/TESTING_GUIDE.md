# Guia de Testes - Sistema de Pedidos e Entregas

## Pré-requisitos

1. **Serviços em execução:**
   - AI Service (porta 8003)
   - Chatbot Service (porta 8002)
   - Telegram Service (porta 8021) - opcional

2. **Dependências instaladas:**
   ```bash
   cd 3_chatbot/bot_operations
   pip install -r requirements.txt
   ```

3. **Variáveis de ambiente:**
   - Verifique o arquivo `.env` ou `env.example`
   - Configure `AI_SERVICE_URL` se necessário

## Passo 1: Iniciar o Chatbot Service

```bash
cd 3_chatbot/bot_operations
python main.py
```

Ou em modo desenvolvimento:
```bash
python start_dev.py
```

O serviço estará disponível em: `http://localhost:8002`

## Passo 2: Testar Endpoints da API

### 2.1. Criar um Pedido

```bash
curl -X POST http://localhost:8002/orders/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "items": [
      {
        "product_id": "prod_001",
        "product_name": "Tomate",
        "quantity": 2,
        "unit_price": 15.50,
        "total_price": 31.00
      },
      {
        "product_id": "prod_002",
        "product_name": "Cebola",
        "quantity": 1,
        "unit_price": 8.00,
        "total_price": 8.00
      }
    ],
    "delivery_address": {
      "street": "Rua Exemplo",
      "number": "123",
      "neighborhood": "Centro",
      "city": "São Paulo",
      "state": "SP",
      "zip_code": "01234-567"
    },
    "payment_method": "pix",
    "notes": "Entregar de manhã"
  }'
```

**Resposta esperada:**
```json
{
  "success": true,
  "order": {
    "id": "...",
    "order_number": "PED-2024-0001",
    "status": "pending",
    "total_amount": 39.00,
    ...
  }
}
```

### 2.2. Buscar Pedido

```bash
# Por ID
curl http://localhost:8002/orders/{order_id}

# Por número
curl http://localhost:8002/orders/number/PED-2024-0001
```

### 2.3. Listar Pedidos do Usuário

```bash
curl http://localhost:8002/orders/user/test_user_123
```

### 2.4. Acompanhar Pedido (com IA)

```bash
curl -X POST http://localhost:8002/orders/{order_id}/process-with-ai \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Onde está meu pedido?",
    "context": {}
  }'
```

### 2.5. Avançar Etapa do Pedido

```bash
curl -X POST http://localhost:8002/orders/{order_id}/advance-stage \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "separacao"
  }'
```

### 2.6. Cancelar Pedido

```bash
curl -X POST http://localhost:8002/orders/{order_id}/cancel
```

## Passo 3: Testar Processamento de Mensagens

### 3.1. Processar Mensagem Relacionada a Pedidos

```bash
curl -X POST http://localhost:8002/chatbot/process-message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "message": "Onde está meu pedido?",
    "session_id": "test_session_001"
  }'
```

**O sistema deve:**
1. Detectar que é relacionado a pedidos
2. Buscar pedidos recentes do usuário
3. Processar com IA
4. Retornar resposta contextualizada

### 3.2. Criar Pedido via Chat

```bash
curl -X POST http://localhost:8002/chatbot/process-message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "message": "Quero fazer um pedido com 2kg de tomate",
    "session_id": "test_session_001"
  }'
```

## Passo 4: Testar Comandos

### 4.1. Criar Pedido via Comando

```bash
curl -X POST http://localhost:8002/chatbot/process-message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "message": "criar pedido",
    "session_id": "test_session_001"
  }'
```

### 4.2. Listar Pedidos via Comando

```bash
curl -X POST http://localhost:8002/chatbot/process-message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "message": "meus pedidos",
    "session_id": "test_session_001"
  }'
```

### 4.3. Acompanhar Pedido via Comando

```bash
curl -X POST http://localhost:8002/chatbot/process-message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "message": "rastrear pedido",
    "session_id": "test_session_001"
  }'
```

## Passo 5: Testar via Telegram (Opcional)

### 5.1. Iniciar Telegram Service

```bash
cd 4_messages_apps/telegram_operations
python main.py
```

### 5.2. Enviar Mensagem no Telegram

1. Abra o bot no Telegram
2. Envie: "Onde está meu pedido?"
3. O sistema deve processar e responder

## Passo 6: Testar Fluxo Completo

### Cenário: Pedido Completo

1. **Criar Pedido:**
   ```bash
   curl -X POST http://localhost:8002/orders/create \
     -H "Content-Type: application/json" \
     -d '{...}'
   ```
   Anote o `order_id` retornado.

2. **Confirmar Pagamento:**
   ```bash
   curl -X PUT http://localhost:8002/orders/{order_id} \
     -H "Content-Type: application/json" \
     -d '{
       "payment_status": "confirmed",
       "status": "payment_confirmed"
     }'
   ```

3. **Avançar para Colheita:**
   ```bash
   curl -X POST http://localhost:8002/orders/{order_id}/advance-stage \
     -H "Content-Type: application/json" \
     -d '{"stage": "colheita"}'
   ```

4. **Avançar para Separação:**
   ```bash
   curl -X POST http://localhost:8002/orders/{order_id}/advance-stage \
     -H "Content-Type: application/json" \
     -d '{"stage": "separacao"}'
   ```

5. **Avançar para Envio:**
   ```bash
   curl -X POST http://localhost:8002/orders/{order_id}/advance-stage \
     -H "Content-Type: application/json" \
     -d '{"stage": "envio"}'
   ```

6. **Verificar Status:**
   ```bash
   curl http://localhost:8002/orders/{order_id}
   ```

## Verificações Importantes

### ✅ Checklist de Testes

- [ ] Chatbot Service inicia sem erros
- [ ] Endpoint `/health` responde corretamente
- [ ] Criar pedido funciona
- [ ] Buscar pedido funciona
- [ ] Listar pedidos funciona
- [ ] Processar com IA funciona
- [ ] Avançar etapas funciona
- [ ] Cancelar pedido funciona
- [ ] Mensagens relacionadas a pedidos são detectadas
- [ ] IA processa pedidos corretamente
- [ ] Comandos de pedidos funcionam

## Troubleshooting

### Erro: "AI Service não está disponível"
- Verifique se o AI Service está rodando na porta 8003
- Verifique a variável `AI_SERVICE_URL` no `.env`

### Erro: "Pedido não encontrado"
- Verifique se o `order_id` está correto
- Lembre-se que pedidos são armazenados em memória (reinicia ao reiniciar o serviço)

### Erro: "Comando não reconhecido"
- Verifique se a mensagem contém palavras-chave relacionadas a pedidos
- Verifique os logs para ver qual intent foi detectado

## Logs

Para ver logs detalhados:
```bash
# Chatbot Service
LOG_LEVEL=DEBUG python main.py

# Telegram Service
LOG_LEVEL=DEBUG python main.py
```

## Próximos Passos

Após testar:
1. Integrar com banco de dados persistente
2. Adicionar testes automatizados (pytest)
3. Configurar notificações em tempo real
4. Integrar com sistemas de pagamento
5. Adicionar dashboard de acompanhamento
