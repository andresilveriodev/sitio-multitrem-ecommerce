# Guia de Integração Keycloak - Validador JWT Independente

## 🎯 Problema Resolvido

Este guia resolve o problema de validação de tokens JWT do Keycloak sem depender de atributos internos da biblioteca `python-keycloak`.

## 📁 Arquivos Necessários

### 1. Validador JWT Independente
```
auth/
├── __init__.py
└── jwt_validator.py
```

### 2. Configuração Atualizada
```
config.py  # (apenas as configurações do Keycloak)
```

## 🔧 Configuração

### config.py
```python
# Configurações do Keycloak
KEYCLOAK_AUTH_SERVER_URL: str = "https://auth.rendacontinua.com/auth"
KEYCLOAK_REALM: str = "auth_sso"
KEYCLOAK_RESOURCE: str = "auth_client"
KEYCLOAK_PUBLIC_CLIENT: bool = False
KEYCLOAK_BEARER_ONLY: bool = True
KEYCLOAK_PRINCIPAL_ATTRIBUTE: str = "preferred_username"
KEYCLOAK_CREDENTIALS_SECRET: str = "e56cf527-d5d9-4b52-bd9f-1e87c8f288de"
KEYCLOAK_USE_RESOURCE_ROLE_MAPPINGS: bool = True
```

## 🚀 Como Usar

### Exemplo Básico
```python
from fastapi import APIRouter, Request, HTTPException
from auth.jwt_validator import verify_bearer_token_or_401

router = APIRouter()

@router.get("/meu-endpoint")
async def meu_endpoint(request: Request):
    try:
        # Validar token e obter dados do usuário
        claims = verify_bearer_token_or_401(request)
        
        # Dados disponíveis do token
        user_id = claims.get('sub')  # Keycloak ID
        username = claims.get('preferred_username')
        email = claims.get('email')
        first_name = claims.get('given_name')
        last_name = claims.get('family_name')
        roles = claims.get('realm_access', {}).get('roles', [])
        
        # Sua lógica aqui...
        return {
            "user_id": user_id,
            "username": username,
            "email": email,
            "roles": roles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        )
```

### Exemplo com Dependency
```python
from fastapi import Depends
from auth.jwt_validator import verify_bearer_token_or_401

def get_current_user(request: Request):
    """Dependency para obter usuário atual"""
    return verify_bearer_token_or_401(request)

@router.get("/protegido")
async def endpoint_protegido(
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": f"Olá {current_user.get('preferred_username')}!",
        "user_id": current_user.get('sub')
    }
```

## 🔍 Dados Disponíveis no Token

O validador retorna todos os claims do JWT:

```python
claims = verify_bearer_token_or_401(request)

# Dados principais
user_id = claims.get('sub')                    # ID único do usuário
username = claims.get('preferred_username')    # Nome de usuário
email = claims.get('email')                    # Email
first_name = claims.get('given_name')          # Primeiro nome
last_name = claims.get('family_name')          # Sobrenome

# Roles e permissões
roles = claims.get('realm_access', {}).get('roles', [])
resource_roles = claims.get('resource_access', {})

# Metadados
exp = claims.get('exp')                        # Expiração
iat = claims.get('iat')                        # Emitido em
iss = claims.get('iss')                        # Emissor
aud = claims.get('aud')                        # Audiência
```

## ⚠️ Tratamento de Erros

### Erro 401 - Token Inválido
```python
try:
    claims = verify_bearer_token_or_401(request)
except HTTPException as e:
    if e.status_code == 401:
        # Token inválido, expirado ou ausente
        # Frontend deve fazer login novamente
        pass
```

### Erro 500 - Problema de Configuração
```python
try:
    claims = verify_bearer_token_or_401(request)
except HTTPException as e:
    if e.status_code == 500:
        # Problema de configuração do Keycloak
        # Verificar conectividade e configurações
        pass
```

## 🎯 Vantagens desta Solução

1. **Independente**: Não depende de atributos internos da lib
2. **Robusto**: Cache inteligente e suporte a rotação de chaves
3. **Performático**: Cache de 10 minutos para JWKS
4. **Padrão**: Usa `.well-known` + JWKS (OpenID Connect)
5. **Confiável**: Tratamento correto de erros (401 vs 500)

## 📋 Checklist de Implementação

- [ ] Copiar `auth/jwt_validator.py`
- [ ] Copiar `auth/__init__.py`
- [ ] Atualizar `config.py` com configurações do Keycloak
- [ ] Instalar dependências: `httpx`, `python-jose`
- [ ] Testar com token válido
- [ ] Implementar tratamento de erros
- [ ] Documentar endpoints protegidos

## 🔗 Dependências

```bash
pip install httpx python-jose[cryptography]
```

## 📞 Suporte

Em caso de problemas:
1. Verificar logs do validador JWT
2. Testar conectividade com Keycloak
3. Verificar configurações no `config.py`
4. Validar token no frontend
