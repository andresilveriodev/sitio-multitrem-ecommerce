# Variáveis de Ambiente - Sítio Multitrem

Este documento lista todas as variáveis de ambiente necessárias para o projeto.

## Como usar

1. Copie o arquivo `.env.example` para `.env` na raiz do projeto
2. Copie os arquivos `.env.example` de cada serviço para `.env` dentro de cada serviço
3. Preencha os valores conforme seu ambiente

## Variáveis Globais

### Banco de Dados (PostgreSQL)
```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=sua_senha
DATABASE_NAME=sitio_multitrem
```

### Redis (Cache e Filas)
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

### Keycloak (Autenticação)
```env
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=sitio-multitrem
KEYCLOAK_CLIENT_ID=sitio-app
KEYCLOAK_CLIENT_SECRET=
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_ADMIN_CLIENT_ID=admin-cli
```

### Mercado Pago (Pagamentos)
```env
MERCADO_PAGO_ACCESS_TOKEN=
MERCADO_PAGO_PUBLIC_KEY=
MERCADO_PAGO_WEBHOOK_SECRET=
```

### Evolution API (WhatsApp)
```env
EVOLUTION_API_URL=http://localhost:8081
EVOLUTION_API_KEY=
EVOLUTION_INSTANCE=sitio-multitrem
```

### OpenAI (Assistente IA)
```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=500
```

## URLs dos Serviços

### Desenvolvimento Local
```env
PRODUCT_SERVICE_URL=http://localhost:3001
CART_SERVICE_URL=http://localhost:3002
ORDER_SERVICE_URL=http://localhost:3003
PAYMENT_SERVICE_URL=http://localhost:3004
AUTH_SERVICE_URL=http://localhost:3005
WHATSAPP_SERVICE_URL=http://localhost:3006
AI_SERVICE_URL=http://localhost:3007
GATEWAY_URL=http://localhost:8000
```

### Frontend (Next.js)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080
NEXT_PUBLIC_KEYCLOAK_REALM=sitio-multitrem
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=sitio-app
```

## Configurações Gerais
```env
NODE_ENV=development
PORT=3000
```

## Notas Importantes

1. **NUNCA** commite arquivos `.env` no Git
2. Cada serviço tem seu próprio `.env.example` com variáveis específicas
3. Para produção, use variáveis de ambiente do servidor/plataforma
4. URLs dos serviços devem apontar para o Gateway em produção
5. Variáveis `NEXT_PUBLIC_*` são expostas no frontend (não coloque secrets)

## Portas dos Serviços

- **Gateway**: 8000
- **Product Service**: 3001
- **Cart Service**: 3002
- **Order Service**: 3003
- **Payment Service**: 3004
- **Auth Service**: 3005
- **WhatsApp Service**: 3006
- **AI Service**: 3007

## Como Obter as Chaves

### Mercado Pago
1. Acesse https://www.mercadopago.com.br/developers
2. Crie uma aplicação
3. Copie o Access Token e Public Key

### OpenAI
1. Acesse https://platform.openai.com/api-keys
2. Crie uma nova chave de API
3. Copie a chave

### Evolution API
1. Configure sua instância da Evolution API
2. Obtenha a API Key do painel
3. Configure a instância com o nome `sitio-multitrem`

### Keycloak
1. Instale o Keycloak (Docker ou standalone)
2. Crie um realm chamado `sitio-multitrem`
3. Crie um client chamado `sitio-app`
4. Configure as URLs de redirecionamento







