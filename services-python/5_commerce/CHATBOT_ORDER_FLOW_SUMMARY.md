# Resumo: Fluxo de Criação de Pedidos - Chatbot

## Fluxo Rápido

### 1. Identificar Cliente

**WhatsApp:**
```
GET v1/customers/phone/{phone_e164}
- Se 200: cliente existe → usar customer_id
- Se 404: cliente não existe → seguir para cadastro
```

**Telegram:**
```
Verificar conversation.channel_account.customer_id
- Se existe: usar customer_id
- Se não existe: cliente não cadastrado → pedir telefone e criar
```

### 2A. Cliente Existe
```
1. Buscar endereço padrão: GET v1/customers/{id}/addresses
2. Coletar itens do pedido durante conversa
3. Criar pedido: POST v1/chatbot/orders
4. Confirmar: POST v1/orders/{id}/confirm
```

### 2B. Cliente NÃO Existe ⚠️ IMPORTANTE

**PASSO 1: Guardar pedido na memória**
```
Armazenar na memória/contexto:
- items: [{product_id, qty, notes}]
- notes: observações do pedido
- status: "pending_customer_registration"
```

**PASSO 2: Coletar dados do cliente**
```
Perguntar:
- Nome completo
- Tipo (restaurante/empório/varejo) → price_profile
- CPF/CNPJ (opcional)
- Observações (opcional)
```

**PASSO 3: Coletar endereço**
```
Perguntar:
- Rua/Logradouro
- Número
- Bairro
- Cidade (confirmar Goiânia)
- Estado (confirmar GO)
- CEP
- Referência (opcional)
- URL Google Maps (opcional)
```

**PASSO 4: Criar cliente**
```
POST v1/customers
Body: {
  "name": "{nome}",
  "phone_e164": "{telefone_e164}",
  "price_profile": "{RESTAURANTE_HIGH|RESTAURANTE_LOW|VAREJO}",
  "document": "{cpf_cnpj}",
  "notes": "{obs}"
}
→ Guardar customer_id retornado
→ Se Telegram: vincular customer_id ao ChannelAccount
```

**PASSO 5: Criar endereço**
```
POST v1/customers/addresses
Body: {
  "customer_id": {customer_id},
  "label": "Principal",
  "street": "{rua}",
  "number": "{numero}",
  "district": "{bairro}",
  "city": "{cidade}",
  "state": "{estado}",
  "zip": "{cep}",
  "reference": "{ref}",
  "location_url": "{url_maps}",
  "is_default": true
}
→ Guardar delivery_address_id retornado
```

**PASSO 6: Recuperar pedido da memória e criar**
```
POST v1/chatbot/orders
Body: {
  "conversation_id": "{conversation_id}",
  "customer_id": {customer_id_criado},
  "items": [recuperar da memória],
  "delivery_address_id": {delivery_address_id_criado},
  "notes": "{obs_do_pedido}"
}
→ Limpar memória após sucesso
```

## Estrutura de Memória

```json
{
  "pending_order": {
    "status": "pending_customer_registration",
    "items": [
      {"product_id": 1, "qty": 5, "notes": null}
    ],
    "notes": "Observações do pedido"
  }
}
```

## Regras Críticas

1. ✅ **SEMPRE guarde pedido na memória** se cliente não existe
2. ✅ **NUNCA crie pedido** sem cliente cadastrado
3. ✅ **SEMPRE crie cliente primeiro**, depois endereço, depois pedido
4. ✅ **Limpe memória** após criar pedido com sucesso
5. ✅ **Valide produtos** antes de criar pedido
6. ✅ **WhatsApp**: usar telefone diretamente da mensagem
7. ✅ **Telegram**: verificar `channel_account.customer_id`, se não existir pedir telefone
8. ✅ **Telegram**: vincular `customer_id` ao `ChannelAccount` após criar cliente

## Exemplo de Conversa

```
Cliente: "Quero fazer um pedido"
Bot: "Qual seu nome?"
Cliente: "Wesley"
Bot: "Você é restaurante, empório ou cliente final?"
Cliente: "Empório"
Bot: "Qual o endereço?"
Cliente: "Av. Sen. Péricles, 334, Setor Negrão de Lima, Goiânia, 74650-270"
Bot: "O que você quer pedir?"
Cliente: "5 alfaces e 3 rúculas"
Bot: "Criando seu cadastro e pedido..."

[Executa: POST /customers → POST /addresses → POST /orders]

Bot: "Pedido criado! Total: R$ 24,50. Confirma?"
```
