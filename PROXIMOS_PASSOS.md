# 🚀 Próximos Passos - Sistema Sítio Multitrem

## ✅ Status Atual

### Serviços Rodando:
- ✅ **Gateway** (porta 8000) - RODANDO
- ✅ **Product Service** (porta 3001) - RODANDO
- ✅ **AI Service** (porta 3007) - RODANDO

### Serviços Parados (Necessários):
- ❌ **Cart Service** (porta 3002) - PARADO
- ❌ **Order Service** (porta 3003) - PARADO
- ❌ **Payment Service** (porta 3004) - PARADO

---

## 📋 Próximos Passos

### 1. Iniciar Cart Service (PRIORIDADE ALTA)

**Por que é importante:**
- Necessário para o AI Service executar funções de carrinho:
  - `add_to_cart` - Adicionar produtos ao carrinho
  - `remove_from_cart` - Remover produtos do carrinho
  - `view_cart` - Visualizar carrinho atual

**Como iniciar:**
```powershell
cd services\cart-service
npm run start:dev
```

**Verificação:**
- Deve aparecer: `🛒 Cart Service running on port 3002`
- Swagger: http://localhost:3002/api/docs

**Pré-requisitos:**
- ✅ Redis já configurado (RedisLabs)
- ✅ Product Service rodando (já está)

---

### 2. Iniciar Order Service (PRIORIDADE ALTA)

**Por que é importante:**
- Necessário para o AI Service executar funções de pedidos:
  - `check_delivery_slots` - Verificar dias disponíveis para entrega
  - `create_order` - Criar pedido com dados do cliente

**Como iniciar:**
```powershell
cd services\order-service
npm run start:dev
```

**Verificação:**
- Deve aparecer: `📦 Order Service running on port 3003`
- Swagger: http://localhost:3003/api/docs

**Pré-requisitos:**
- ✅ PostgreSQL configurado (já está)
- ✅ Banco `sitio_multitrem` criado (já está)
- ✅ Cart Service rodando (iniciar antes)

---

### 3. Iniciar Payment Service (PRIORIDADE MÉDIA)

**Por que é importante:**
- Necessário para o AI Service executar:
  - `generate_payment_link` - Gerar link de pagamento (Pix/Boleto)

**Como iniciar:**
```powershell
cd services\payment-service
npm run start:dev
```

**Verificação:**
- Deve aparecer: `💳 Payment Service running on port 3004`
- Swagger: http://localhost:3004/api/docs

**Pré-requisitos:**
- ✅ PostgreSQL configurado (já está)
- ✅ Banco `sitio_multitrem` criado (já está)
- ⚠️ **Mercado Pago** (opcional por enquanto - pode rodar sem)

**Nota:** O Payment Service pode rodar sem as credenciais do Mercado Pago, mas não conseguirá gerar pagamentos reais.

---

## 🎯 Ordem Recomendada de Inicialização

### Terminal 1 - Gateway
```powershell
cd services\gateway
npm run start:dev
```

### Terminal 2 - Product Service
```powershell
cd services\product-service
npm run start:dev
```

### Terminal 3 - Cart Service ⭐ INICIAR AGORA
```powershell
cd services\cart-service
npm run start:dev
```

### Terminal 4 - Order Service ⭐ INICIAR AGORA
```powershell
cd services\order-service
npm run start:dev
```

### Terminal 5 - Payment Service
```powershell
cd services\payment-service
npm run start:dev
```

### Terminal 6 - AI Service
```powershell
cd services\ai-service
npm run start:dev
```

---

## 🧪 Testes Após Iniciar Todos os Serviços

### 1. Teste Básico do Chat
No frontend, teste:
- "Olá" - Deve responder
- "Quais produtos vocês têm?" - Deve listar produtos
- "Adicione 1 alface ao carrinho" - Deve adicionar (requer Cart Service)
- "Mostre meu carrinho" - Deve mostrar (requer Cart Service)

### 2. Teste no Swagger
Acesse: http://localhost:3007/api/docs
- Teste `POST /ai/chat` com diferentes mensagens
- Verifique se as funções são chamadas corretamente

### 3. Teste de Integração Completa
1. Listar produtos ✅
2. Adicionar ao carrinho (requer Cart Service)
3. Ver carrinho (requer Cart Service)
4. Criar pedido (requer Order Service)
5. Gerar pagamento (requer Payment Service)

---

## 📊 Checklist de Funcionalidades

### Funcionalidades Básicas (Já Funcionam):
- [x] Chat básico (responder mensagens)
- [x] Listar produtos
- [x] Histórico de conversas (Redis)

### Funcionalidades que Requerem Outros Serviços:
- [ ] Adicionar ao carrinho (requer Cart Service)
- [ ] Remover do carrinho (requer Cart Service)
- [ ] Ver carrinho (requer Cart Service)
- [ ] Verificar dias de entrega (requer Order Service)
- [ ] Criar pedido (requer Order Service)
- [ ] Gerar link de pagamento (requer Payment Service)

---

## 🔧 Configurações Pendentes (Opcionais)

### Payment Service - Mercado Pago
Se quiser gerar pagamentos reais:
1. Acesse: https://www.mercadopago.com.br/developers
2. Crie uma aplicação
3. Copie o Access Token e Public Key
4. Edite `services/payment-service/.env`:
```env
MERCADO_PAGO_ACCESS_TOKEN=sua_chave_aqui
MERCADO_PAGO_PUBLIC_KEY=sua_chave_publica_aqui
```

---

## 🎉 Quando Tudo Estiver Rodando

Você terá um sistema completo de e-commerce com:
- ✅ Assistente IA conversacional
- ✅ Gerenciamento de produtos
- ✅ Carrinho de compras
- ✅ Criação de pedidos
- ✅ Geração de pagamentos
- ✅ Histórico de conversas

---

## 🆘 Solução de Problemas

### Erro: "Service unavailable"
- Verifique se o serviço está rodando na porta correta
- Verifique os logs do serviço

### Erro: "Connection refused"
- Verifique se o serviço está rodando
- Verifique as URLs nos arquivos `.env`

### Erro: "Database connection failed"
- Verifique se PostgreSQL está rodando
- Verifique a senha no `.env`

---

## 📝 Resumo Rápido

**Agora mesmo você deve:**
1. ✅ Iniciar Cart Service (porta 3002)
2. ✅ Iniciar Order Service (porta 3003)
3. ⚠️ Iniciar Payment Service (porta 3004) - opcional

**Depois disso:**
- Teste o chat completo no frontend
- Verifique se todas as funções do AI estão funcionando

**Pronto!** 🎉

