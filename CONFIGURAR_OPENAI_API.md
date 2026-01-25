# 🤖 Configuração da OpenAI API Key

## ⚠️ PROBLEMA ATUAL
O **AI Service** está funcionando, mas precisa de uma **chave válida do OpenAI** para processar conversas.

**Erro atual:** `Incorrect API key provided: sua_chav*********aqui`

---

## 🔧 COMO RESOLVER

### 1️⃣ **Obter Chave do OpenAI:**
1. Acesse: https://platform.openai.com/account/api-keys
2. Faça login na sua conta OpenAI
3. Clique em "Create new secret key"
4. Copie a chave (formato: `sk-proj-...`)

### 2️⃣ **Configurar no Projeto:**

**Opção A - Editar .env diretamente:**
```bash
# No arquivo raiz .env, adicione:
OPENAI_API_KEY=sk-proj-SUA_CHAVE_REAL_AQUI
```

**Opção B - Usando env.docker.unified:**
1. Edite o arquivo `env.docker.unified`
2. Substitua: `OPENAI_API_KEY=sua_chave_openai_aqui`
3. Por: `OPENAI_API_KEY=sk-proj-SUA_CHAVE_REAL_AQUI`

### 3️⃣ **Reiniciar o AI Service:**
```bash
docker-compose restart ai-service
```

### 4️⃣ **Testar:**
```bash
# Teste via PowerShell:
$body = @{
    visitorId = "teste-123"
    message = "Oi, quero ver produtos de hortaliças"
    source = "web"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:3007/ai/chat" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

---

## 📊 STATUS ATUAL

### ✅ **FUNCIONANDO:**
- Container `sitio_ai_service` rodando
- NestJS iniciado corretamente
- Rotas mapeadas:
  - `POST /ai/chat` - Processar mensagens
  - `GET /ai/conversation/:visitorId` - Buscar histórico
- Swagger docs: http://localhost:3007/api/docs
- Redis conectado
- Integração com microserviços configurada

### ❌ **FALTANDO:**
- Chave válida do OpenAI

---

## 🎯 DEPOIS DE CONFIGURAR

Com a chave configurada, o AI Service será capaz de:

1. **Processar conversas** usando GPT-4o-mini
2. **Executar funções**:
   - Listar produtos
   - Adicionar ao carrinho
   - Criar pedidos
   - Gerar links de pagamento
3. **Salvar histórico** no Redis
4. **Integrar** com todos os microserviços

---

## 💡 DICAS

- **Segurança**: Nunca comite a chave real no Git
- **Custos**: Monitore uso na dashboard OpenAI
- **Modelos**: Padrão é `gpt-4o-mini` (mais barato)
- **Limites**: Configure `OPENAI_MAX_TOKENS` se necessário