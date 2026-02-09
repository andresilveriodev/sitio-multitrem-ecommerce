# Refatoração do Sistema de Pedidos e Entregas

## Visão Geral

Este documento descreve a refatoração dos módulos `telegram_operations` e `bot_operations` para permitir livre comunicação com a IA para processar pedidos e entregas dos clientes, incluindo todas as etapas do processo de compra.

## Etapas do Processo de Compra

O sistema agora suporta as seguintes etapas:

1. **Pedido** - Criação e confirmação do pedido
2. **Colheita ou Compra no Fornecedor** - Preparação dos produtos
3. **Separação** - Separação dos itens do pedido
4. **Envio** - Envio do pedido para entrega
5. **Pagamento** - Processamento e confirmação do pagamento

## Arquitetura

### Modelos de Dados

**Arquivo:** `models/order_models.py`

- `Order`: Modelo principal de pedido
- `OrderStatus`: Enum com status do pedido (pending, confirmed, in_harvest, in_purchase, in_separation, ready_to_ship, shipped, in_transit, delivered, cancelled, payment_pending, payment_confirmed, payment_failed)
- `OrderItem`: Item do pedido
- `DeliveryAddress`: Endereço de entrega
- `PaymentStatus`: Status do pagamento
- `PaymentMethod`: Método de pagamento
- `OrderStage`: Etapa do processo de pedido
- `OrderUpdate`: Atualização de pedido
- `OrderQuery`: Query para buscar pedidos

### Serviços

**Arquivo:** `services/order_service.py`

O `OrderService` gerencia:
- Criação de pedidos
- Atualização de status e etapas
- Processamento com IA
- Busca e listagem de pedidos
- Cancelamento de pedidos

**Principais métodos:**
- `create_order()`: Cria um novo pedido
- `get_order()`: Busca pedido por ID
- `get_order_by_number()`: Busca pedido por número
- `get_user_orders()`: Lista pedidos do usuário
- `update_order()`: Atualiza pedido
- `advance_order_stage()`: Avança pedido para próxima etapa
- `process_order_with_ai()`: Processa pedido usando IA
- `cancel_order()`: Cancela pedido

### Comandos

**Arquivo:** `services/commands/order_commands.py`

Comandos disponíveis:
- `create_order`: Cria um novo pedido
- `view_order`: Visualiza detalhes de um pedido
- `list_orders`: Lista pedidos do usuário
- `track_order`: Acompanha o status e etapas de um pedido
- `update_order_stage`: Avança pedido para próxima etapa
- `cancel_order`: Cancela um pedido
- `process_order_with_ai`: Processa pedido usando IA

### Integração com IA

O sistema integra com a IA através do método `process_order_with_ai()` que:

1. Prepara contexto completo do pedido (status, itens, etapas)
2. Cria prompt especializado para a IA processar pedidos
3. Envia para o AI Service
4. Extrai ações sugeridas pela IA
5. Executa ações automaticamente (ex: avançar etapas)

**Exemplo de prompt gerado:**
```
Você é um assistente de e-commerce especializado em processar pedidos e gerenciar entregas.

PEDIDO ATUAL:
- Número: PED-2024-001
- Status: in_separation
- Status de Pagamento: confirmed
- Valor Total: R$ 150.00
- Itens: 3 item(s)

ETAPAS DO PROCESSO:
- pedido: completed
- pagamento: completed
- separacao: in_progress

MENSAGEM DO USUÁRIO:
Onde está meu pedido?

INSTRUÇÕES:
1. Analise a mensagem do usuário e determine a intenção
2. Identifique se o usuário quer:
   - Acompanhar o pedido
   - Atualizar informações
   - Cancelar o pedido
   - Verificar status de pagamento
   - Solicitar informações sobre entrega
   - Outra ação relacionada ao pedido
...
```

## Rotas da API

**Arquivo:** `routes/order_router.py`

### Endpoints Disponíveis

- `POST /orders/create`: Cria um novo pedido
- `GET /orders/{order_id}`: Busca pedido por ID
- `GET /orders/number/{order_number}`: Busca pedido por número
- `GET /orders/user/{user_id}`: Lista pedidos do usuário
- `PUT /orders/{order_id}`: Atualiza pedido
- `POST /orders/{order_id}/advance-stage`: Avança pedido para próxima etapa
- `POST /orders/{order_id}/cancel`: Cancela pedido
- `POST /orders/{order_id}/process-with-ai`: Processa pedido usando IA

## Integração no Chat Router

O `chat_router.py` foi atualizado para:

1. **Detectar mensagens relacionadas a pedidos** através de palavras-chave:
   - "pedido", "entrega", "rastrear", "acompanhar", "status", "colheita", "separação", "envio", "pagamento", "compra"

2. **Processar automaticamente com IA** quando detectado interesse em pedidos:
   - Busca pedidos recentes do usuário
   - Processa com IA usando o pedido mais recente
   - Executa ações sugeridas pela IA
   - Retorna resposta contextualizada

## Uso no Telegram

O serviço do Telegram (`telegram_operations`) já está integrado e processa automaticamente comandos de pedidos através do chatbot service.

### Exemplos de Uso

**Criar Pedido:**
```
Usuário: "Quero fazer um pedido com 2kg de tomate e 1kg de cebola"
Bot: [Processa com IA e cria pedido]
```

**Acompanhar Pedido:**
```
Usuário: "Onde está meu pedido?"
Bot: [Busca pedido mais recente e processa com IA]
     "Seu pedido PED-2024-001 está em separação. 
      Previsão de envio: amanhã"
```

**Atualizar Etapa:**
```
Usuário: "Meu pedido já foi separado?"
Bot: [Processa com IA e atualiza etapa se necessário]
     "Sim! Seu pedido foi separado e está pronto para envio."
```

## Fluxo de Processamento

1. **Usuário envia mensagem** (via Telegram ou Web)
2. **Chatbot detecta** se é relacionado a pedidos
3. **Busca pedidos** recentes do usuário
4. **Processa com IA** usando contexto completo do pedido
5. **IA analisa** intenção e sugere ações
6. **Sistema executa** ações automaticamente (ex: avançar etapas)
7. **Retorna resposta** contextualizada ao usuário

## Melhorias Futuras

- [ ] Integração com banco de dados persistente
- [ ] Notificações em tempo real de mudanças de status
- [ ] Dashboard de acompanhamento de pedidos
- [ ] Integração com sistemas de pagamento
- [ ] Integração com sistemas de entrega/logística
- [ ] Histórico completo de interações com pedidos
- [ ] Análise preditiva de atrasos
- [ ] Recomendações automáticas baseadas em histórico

## Notas Técnicas

- O `OrderService` atualmente usa armazenamento em memória (dicionário)
- Em produção, deve ser substituído por banco de dados
- A IA processa pedidos de forma contextualizada
- Comandos de pedidos requerem permissões apropriadas
- Sistema de confirmação para ações críticas (cancelamento, etc.)

## Exemplo de Resposta da IA

```json
{
  "success": true,
  "response": "Seu pedido PED-2024-001 está em separação. Os produtos estão sendo preparados e devem ser enviados amanhã. Você receberá uma notificação quando o pedido for despachado.",
  "actions": [
    {
      "type": "update_stage",
      "stage": "envio",
      "order_id": "abc123"
    }
  ],
  "order": {
    "id": "abc123",
    "order_number": "PED-2024-001",
    "status": "in_separation",
    ...
  }
}
```
