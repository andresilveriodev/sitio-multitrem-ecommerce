# Auth Service

Microserviço de autenticação do Sítio Multitrem, responsável por gerenciar autenticação e autorização usando Keycloak.

## Tecnologias

- NestJS
- Keycloak Admin Client
- Keycloak Connect
- Axios (para comunicação com Keycloak)

## Instalação

```bash
npm install
```

## Configuração

1. Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Configure as variáveis de ambiente no `.env`:
```env
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=sitio-multitrem
KEYCLOAK_CLIENT_ID=sitio-app
KEYCLOAK_CLIENT_SECRET=
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_ADMIN_CLIENT_ID=admin-cli
PORT=3005
NODE_ENV=development
```

3. Configure o Keycloak:
   - Crie um realm chamado `sitio-multitrem`
   - Crie um client chamado `sitio-app`
   - Configure as URLs de redirecionamento
   - Configure o client como público ou confidencial (com secret)

## Executar

### Desenvolvimento
```bash
npm run start:dev
```

### Produção
```bash
npm run build
npm start
```

## Endpoints

- `POST /auth/register` - Criar novo usuário
- `POST /auth/login` - Obter tokens de acesso
- `POST /auth/refresh` - Renovar access token
- `POST /auth/logout` - Invalidar sessão
- `GET /auth/me` - Dados do usuário logado (protegido)

## Porta

O serviço roda na porta **3005** por padrão.

## Funcionalidades

- Registro de usuários no Keycloak
- Login com obtenção de tokens (access_token e refresh_token)
- Renovação de tokens
- Logout com invalidação de sessão
- Validação de tokens JWT em rotas protegidas
- Decorator @Public() para rotas públicas
- KeycloakGuard para proteção automática de rotas

## Uso

### Rotas Públicas
Use o decorator `@Public()` para marcar rotas que não precisam de autenticação:
```typescript
@Public()
@Post('register')
async register() { ... }
```

### Rotas Protegidas
Por padrão, todas as rotas são protegidas. O guard valida automaticamente o token JWT:
```typescript
@Get('me')
async getMe() { ... }
```

### Headers
Para rotas protegidas, inclua o token no header:
```
Authorization: Bearer <access_token>
```


