# User Service - E-commerce

Serviço de autenticação e autorização com integração Keycloak e sistema ACL (Access Control List).

## 🎯 Funcionalidades

### Autenticação
- ✅ Integração com Keycloak remoto
- ✅ **CPF como username** (login com CPF ou email)
- ✅ Sincronização automática de usuários
- ✅ Gerenciamento de sessões
- ✅ Tokens JWT com refresh automático
- ✅ Logout seguro

### Cadastro de Usuários
- ✅ **Cadastro via API** com validação completa
- ✅ **CPF obrigatório** como identificador principal
- ✅ **Telefone internacional** (formato +pais-dd-telefone)
- ✅ **Verificação de duplicatas** (CPF/email)
- ✅ **Email de verificação** automático
- ✅ **Senha opcional** (gerada automaticamente se não fornecida)

### Autorização (ACL)
- ✅ Sistema de perfis de usuário
- ✅ Permissões granulares por recurso/ação
- ✅ Controle de escopo (own/all)
- ✅ Cache de permissões para alta performance
- ✅ Auditoria de ações

### Gestão de Perfil de Usuário
- ✅ Dados pessoais completos (nome, CPF, endereço, etc.)
- ✅ Preferências de interface (tema, idioma, notificações)
- ✅ Configurações de conta (privacidade, 2FA, etc.)
- ✅ Histórico de atividades do usuário
- ✅ Perfil completo integrado com ACL

### Segurança
- ✅ Validação de tokens JWT
- ✅ Rate limiting
- ✅ Logs de auditoria
- ✅ CORS configurável
- ✅ Headers de segurança

## 🏗️ Arquitetura

```
auth_service/
├── main.py                    # ✅ Ponto de entrada consolidado
├── config.py                  # Configurações
├── requirements.txt           # Dependências
├── models/
│   ├── auth.py               # Modelos de autenticação
│   ├── acl.py                # Modelos de ACL (User, Profile, Permission)
│   └── user_profile.py       # Modelos de perfil de usuário
├── services/
│   ├── auth_service.py       # Serviço principal de autenticação
│   ├── keycloak_service.py   # Integração com Keycloak
│   ├── acl_service.py        # Serviço de ACL
│   └── user_profile_service.py # Serviço de perfil de usuário
├── routes/
│   ├── auth.py               # Rotas de autenticação
│   ├── acl.py                # Rotas de ACL
│   └── user_profile.py       # Rotas de perfil de usuário
├── frontend-examples/        # ✅ Exemplos de implementação frontend
├── init_db.py                # Inicialização do banco
├── start.sh                  # Script de inicialização
└── Dockerfile                # Containerização
```

## 🚀 Configuração

### Variáveis de Ambiente

```bash
# Keycloak
KEYCLOAK_AUTH_SERVER_URL=https://auth.rendacontinua.com/auth
KEYCLOAK_REALM=auth_sso
KEYCLOAK_RESOURCE=auth_client
KEYCLOAK_CREDENTIALS_SECRET=e56cf527-d5d9-4b52-bd9f-1e87c8f288de

# Keycloak Admin (para criação de usuários)
KEYCLOAK_ADMIN_REALM=master
KEYCLOAK_ADMIN_CLIENT_ID=admin-cli
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=Senh@123

# Banco de dados
DATABASE_URI=postgresql://postgres:123456@localhost:5434/sitio_multitrem

# Redis (cache)
REDIS_URL=redis://localhost:6379/0

# Segurança
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Configuração Keycloak

**Importante:** O Keycloak deve estar configurado com:
- ❌ **"Email as username" DESABILITADO**
- ✅ **"User registration" HABILITADO**
- ✅ **Username policy** para aceitar CPF: `^[0-9]{11}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`

## 📡 Endpoints

### Autenticação

```http
POST /api/v1/auth/login              # Login com CPF ou email
POST /api/v1/auth/refresh            # Renovar token
POST /api/v1/auth/logout             # Logout
GET  /api/v1/auth/user               # Dados do usuário atual
POST /api/v1/auth/register           # ✅ Cadastro de usuário
GET  /api/v1/auth/check-user         # ✅ Verificar se usuário existe
```

### ACL

```http
POST /api/v1/acl/check                    # Verificar permissão
GET  /api/v1/acl/permissions/summary/{id} # Resumo de permissões
POST /api/v1/acl/permissions              # Criar permissão
POST /api/v1/acl/profiles                 # Criar perfil
POST /api/v1/acl/profiles/{id}/assign/{user_id}  # Atribuir perfil
POST /api/v1/acl/cache/clear              # Limpar cache
```

### Usuários

```http
GET /api/v1/users                    # Listar usuários (admin)
GET /api/v1/users/{user_id}          # Obter usuário específico
POST /api/v1/users                   # Criar usuário (admin)
PUT /api/v1/users/{user_id}          # Atualizar usuário
DELETE /api/v1/users/{user_id}       # Deletar usuário (admin)
```

## 🔐 Exemplos de Uso

### Cadastro de Usuário

```bash
curl -X POST "http://localhost:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "cpf": "12345678901",
    "email": "usuario@exemplo.com",
    "first_name": "João",
    "last_name": "Silva",
    "phone": "+55-11-99999-9999",
    "password": "senha123"
  }'
```

### Login com CPF

```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=12345678901&password=senha123"
```

### Login com Email

```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=usuario@exemplo.com&password=senha123"
```

### Obter Dados do Token JWT

```bash
curl -X GET "http://localhost:8001/api/v1/auth/user-data" \
  -H "Authorization: Bearer {access_token}"
```

**Resposta:**
```json
{
  "keycloak_id": "12345678-1234-1234-1234-123456789012",
  "username": "adriano.santos",
  "email": "adriano.santos.bm@gmail.com",
  "first_name": "Adriano",
  "last_name": "Lourenco dos Santos",
  "roles": ["user", "trader"],
  "exp": 1703123456,
  "iat": 1703120000,
  "id": null,
  "is_active": null,
  "is_verified": null,
  "last_login": null,
  "created_at": null,
  "updated_at": null,
  "profiles": [],
  "permissions": [],
  "session_info": null
}
```

**Nota:** Este endpoint apenas decodifica o token JWT e retorna os dados contidos no token, sem consultar o banco de dados. Os campos locais (id, is_active, etc.) retornam `null` pois não são consultados.

### Verificar se Usuário Existe

```bash
curl -X GET "http://localhost:8001/api/v1/auth/check-user?cpf=12345678901"
curl -X GET "http://localhost:8001/api/v1/auth/check-user?email=usuario@exemplo.com"
```

### Gestão de Usuários

#### Listar Usuários (Admin)

```bash
curl -X GET "http://localhost:8001/api/v1/users?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Obter Usuário Específico

```bash
curl -X GET "http://localhost:8001/api/v1/users/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Criar Usuário (Admin)

```bash
curl -X POST "http://localhost:8001/api/v1/users" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "novo_usuario",
    "email": "novo@exemplo.com",
    "first_name": "João",
    "last_name": "Silva",
    "password": "senha123"
  }'
```

#### Atualizar Usuário

```bash
curl -X PUT "http://localhost:8001/api/v1/users/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "João Pedro",
    "last_name": "Silva Santos"
  }'
```

#### Deletar Usuário (Admin)

```bash
curl -X DELETE "http://localhost:8001/api/v1/users/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Verificar Permissão

```bash
curl -X POST "http://localhost:8001/api/v1/acl/check" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "resource": "trading",
    "action": "write",
    "scope": "own"
  }'
```

### Gestão de Perfil de Usuário

#### Obter Dados Pessoais

```bash
curl -X GET "http://localhost:8001/api/v1/users/1/profile" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Criar/Atualizar Dados Pessoais

```bash
curl -X PUT "http://localhost:8001/api/v1/users/1/profile" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "João Silva",
    "cpf": "123.456.789-01",
    "phone": "+55-11-99999-9999",
    "address": "Rua das Flores, 123",
    "city": "São Paulo",
    "state": "SP"
  }'
```

#### Obter Preferências

```bash
curl -X GET "http://localhost:8001/api/v1/users/1/preferences" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Atualizar Preferências

```bash
curl -X PUT "http://localhost:8001/api/v1/users/1/preferences" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "dark",
    "language": "pt-BR",
    "notifications_enabled": true,
    "refresh_interval": 10000
  }'
```

#### Obter Perfil Completo

```bash
curl -X GET "http://localhost:8001/api/v1/users/1/complete" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🎨 Frontend Integration

### Exemplos Prontos

O projeto inclui exemplos completos de implementação frontend:

- **React + TypeScript**: `frontend-examples/registration-example.tsx`
- **CSS Moderno**: `frontend-examples/registration-example.css`
- **Documentação**: `frontend-examples/README.md`

### Características dos Exemplos

- ✅ **Validação em tempo real**
- ✅ **Estados visuais** (loading, sucesso, erro)
- ✅ **Responsividade**
- ✅ **Acessibilidade**
- ✅ **Integração completa** com a API

## 🗄️ Banco de Dados

### Tabelas Principais

- **users** - Usuários do sistema
- **profiles** - Perfis de acesso
- **permissions** - Permissões granulares
- **user_sessions** - Sessões ativas
- **audit_logs** - Logs de auditoria
- **user_profiles_data** - Dados pessoais completos
- **user_preferences** - Preferências de interface
- **user_settings** - Configurações de conta
- **user_activities** - Histórico de atividades

### Relacionamentos

```
users <-> profiles (many-to-many)
profiles <-> permissions (many-to-many)
users -> user_sessions (one-to-many)
users -> audit_logs (one-to-many)
users -> user_profiles_data (one-to-one)
users -> user_preferences (one-to-one)
users -> user_settings (one-to-one)
users -> user_activities (one-to-many)
```

## ⚡ Performance

- **Cache de permissões** com TTL configurável
- **Pool de conexões** otimizado
- **Validação de tokens** em cache
- **Logs estruturados** para monitoramento

## 🔧 Desenvolvimento

### Instalação Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Inicializar banco
python init_db.py

# Migrar tabelas de perfil de usuário (se necessário)
python migrate_user_profile.py

# Migrar campos first_name e last_name (se necessário)
python migrate_user_fields.py

# Executar
python main.py

## 🧪 Testes

### Executar Todos os Testes
```bash
python run_tests.py
```

### Testes Individuais
```bash
# Testes de persistência
python test_persistence.py

# Testes da API (requer servidor rodando)
python test_api_endpoints.py
```

### Arquivos Gerados pelos Testes
- `json_examples.json` - Exemplos de JSON para persistência
- `api_examples.json` - Exemplos de endpoints da API
```

### Docker

```bash
# Construir imagem
docker build -t auth-service .

# Executar
docker run -p 8001:8001 --env-file .env auth-service
```

## 📊 Monitoramento

- **Health Check**: `GET /health`
- **Métricas**: Prometheus (futuro)
- **Logs**: Structlog com JSON
- **Auditoria**: Tabela audit_logs

## 🔒 Segurança

- Tokens JWT assinados
- Refresh tokens seguros
- Rate limiting
- Validação de CORS
- Headers de segurança
- Logs de auditoria completos
- **CPF como identificador principal**

## 🚨 Troubleshooting

### Problemas Comuns

1. **Erro de conexão Keycloak**
   - Verificar URL e credenciais
   - Verificar se o realm existe
   - **Verificar se "Email as username" está DESABILITADO**

2. **Erro de banco de dados**
   - Verificar DATABASE_URI
   - Executar `python init_db.py`

3. **Permissões não funcionando**
   - Verificar cache: `POST /api/v1/acl/cache/clear`
   - Verificar atribuição de perfis

4. **CPF não aceito como username**
   - Verificar configuração do Keycloak
   - Executar script de migração se necessário

## 📝 Logs

O serviço usa structlog para logs estruturados:

```json
{
  "event": "Usuário autenticado com sucesso",
  "user_id": 123,
  "username": "12345678901",
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "info"
}
```

## 🔄 Migração de Usuários

Para migrar usuários existentes de email para CPF como username:

1. **Configurar Keycloak** (desabilitar "Email as username")
2. **Executar script de migração** (se necessário)
3. **Verificar configuração** com script de validação

## 📚 Documentação Adicional

- **Guia Frontend**: `FRONTEND_REGISTRATION_GUIDE.md`
- **Usuários Existentes**: `USUARIOS_EXISTENTES_SSO.md`
- **Keycloak Admin**: `README_KEYCLOAK_ADMIN.md`
- **Ambiente Virtual**: `README_VENV.md`

