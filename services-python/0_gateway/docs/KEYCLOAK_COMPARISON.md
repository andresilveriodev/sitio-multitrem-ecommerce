# Comparação Keycloak: Gateway vs Trade Service

## 📋 Resumo

O **Gateway Service** está funcionando corretamente com Keycloak, enquanto o **Trade Service** está tendo problemas. Este documento compara as implementações para identificar diferenças.

---

## 🔍 Arquivos Usados

### Gateway Service (Funcionando ✅)

**Arquivo:** `auth/jwt_validator.py`

**Características:**
- ✅ Usa `logging` padrão do Python
- ✅ ISSUER hardcoded: `"https://auth.rendacontinua.com/auth/realms/auth_sso"`
- ✅ Cache de JWKS por 10 minutos
- ✅ Refresh automático de cache quando chave não encontrada
- ✅ Validação completa: `.well-known` → `jwks_uri` → validação JWT

**Estrutura:**
```python
# Configuração do Keycloak
ISSUER = "https://auth.rendacontinua.com/auth/realms/auth_sso"

@lru_cache(maxsize=1)
def _get_openid_config() -> Dict[str, Any]:
    """Obtém configuração OpenID do .well-known"""
    url = f"{ISSUER}/.well-known/openid-configuration"
    # ... usa httpx.Client com verify=False

_jwks_cache = {"keys": None, "exp": 0}

def _get_jwks() -> Dict[str, Any]:
    """Obtém JWKS com cache de 10 minutos"""
    # ... implementação com cache

def _get_signing_key(kid: str) -> Optional[Dict[str, Any]]:
    """Obtém chave de assinatura pelo kid"""
    # ... busca chave e força refresh se necessário

def verify_bearer_token_or_401(request: Request) -> Dict[str, Any]:
    """Valida token Bearer e retorna claims ou levanta 401"""
    # ... validação completa do token
```

---

### Trade Service (Com Problemas ❌)

**Arquivo:** `services/keycloak_service.py`

**Características:**
- ⚠️ Usa `structlog` (pode ter problemas de configuração)
- ✅ ISSUER hardcoded: `"https://auth.rendacontinua.com/auth/realms/auth_sso"` (igual ao Gateway)
- ✅ Cache de JWKS por 10 minutos (igual)
- ✅ Refresh automático de cache quando chave não encontrada (igual)
- ✅ Validação completa: `.well-known` → `jwks_uri` → validação JWT (igual)

**Estrutura:**
```python
# Configuração do Keycloak - ISSUER hardcoded igual ao gateway
ISSUER = "https://auth.rendacontinua.com/auth/realms/auth_sso"

@lru_cache(maxsize=1)
def _get_openid_config() -> Dict[str, Any]:
    """Obtém configuração OpenID do .well-known"""
    # ... mesma implementação

_jwks_cache = {"keys": None, "exp": 0}

def _get_jwks() -> Dict[str, Any]:
    """Obtém JWKS com cache de 10 minutos"""
    # ... mesma implementação

def _get_signing_key(kid: str) -> Optional[Dict[str, Any]]:
    """Obtém chave de assinatura pelo kid"""
    # ... mesma implementação

def verify_bearer_token_or_401(request: Request) -> Dict[str, Any]:
    """Valida token Bearer e retorna claims ou levanta 401"""
    # ... mesma implementação
```

---

## 🔑 Diferenças Principais

### 1. Sistema de Logging

**Gateway:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Mensagem")
```

**Trade Service:**
```python
import structlog
logger = structlog.get_logger(__name__)
logger.info("Mensagem", key=value)  # structlog requer formato diferente
```

**⚠️ Problema Potencial:**
- Se `structlog` não estiver configurado corretamente, pode causar erros silenciosos
- `structlog` requer configuração adicional para funcionar

### 2. Configuração do Keycloak

**Gateway (`config.py`):**
```python
KEYCLOAK_AUTH_SERVER_URL: str = os.getenv("KEYCLOAK_AUTH_SERVER_URL", "https://auth.rendacontinua.com/auth")
KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "auth_sso")

@property
def KEYCLOAK_ISSUER(self) -> str:
    """Retorna o issuer do Keycloak baseado na URL e realm"""
    issuer = os.getenv("KEYCLOAK_ISSUER")
    if issuer:
        return issuer
    return f"{self.KEYCLOAK_AUTH_SERVER_URL}/realms/{self.KEYCLOAK_REALM}"
```

**Trade Service (`config.py`):**
```python
KEYCLOAK_AUTH_SERVER_URL: str = "https://auth.rendacontinua.com/auth"
KEYCLOAK_REALM: str = "auth_sso"
KEYCLOAK_ISSUER: Optional[str] = None

@property
def keycloak_issuer(self) -> str:
    """Retorna o issuer do Keycloak baseado na URL e realm"""
    if self.KEYCLOAK_ISSUER:
        return self.KEYCLOAK_ISSUER
    return f"{self.KEYCLOAK_AUTH_SERVER_URL}/realms/{self.KEYCLOAK_REALM}"
```

**⚠️ Problema Potencial:**
- Trade Service tem `KEYCLOAK_ISSUER` opcional, mas não usa no `keycloak_service.py`
- O `keycloak_service.py` do Trade Service tem ISSUER hardcoded, ignorando a configuração

### 3. Uso da Configuração

**Gateway:**
- ❌ Não usa `settings.KEYCLOAK_ISSUER` no `jwt_validator.py`
- ✅ ISSUER hardcoded diretamente no arquivo

**Trade Service:**
- ❌ Não usa `settings.keycloak_issuer` no `keycloak_service.py`
- ✅ ISSUER hardcoded diretamente no arquivo (igual ao Gateway)

**✅ Ambos estão iguais neste aspecto**

---

## 🐛 Possíveis Problemas no Trade Service

### 1. Structlog Não Configurado

Se `structlog` não estiver configurado, pode causar erros:

```python
# Trade Service precisa de:
import structlog

# Configuração necessária (pode estar faltando):
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### 2. Dependências Faltando

Verificar se `structlog` está instalado:

```bash
pip install structlog
```

### 3. Erros Silenciosos

Se `structlog` não estiver configurado, os erros podem ser silenciosos e difíceis de debugar.

---

## ✅ Solução Recomendada

### Opção 1: Usar Mesmo Sistema do Gateway (Recomendado)

Copiar o `jwt_validator.py` do Gateway para o Trade Service e substituir `keycloak_service.py`:

**Vantagens:**
- ✅ Já está funcionando no Gateway
- ✅ Usa `logging` padrão (mais simples)
- ✅ Menos dependências
- ✅ Mais fácil de debugar

**Passos:**
1. Copiar `auth/jwt_validator.py` do Gateway
2. Renomear para `services/keycloak_service.py` no Trade Service
3. Ajustar imports se necessário
4. Testar

### Opção 2: Corrigir Structlog no Trade Service

Se quiser manter `structlog`, garantir que está configurado:

1. Adicionar configuração do `structlog` no início do `keycloak_service.py` ou em `app.py`
2. Verificar se `structlog` está instalado
3. Testar logs

---

## 📊 Comparação de Código

### Função `_get_openid_config()`

**Gateway:**
```python
@lru_cache(maxsize=1)
def _get_openid_config() -> Dict[str, Any]:
    """Obtém configuração OpenID do .well-known"""
    url = f"{ISSUER}/.well-known/openid-configuration"
    try:
        with httpx.Client(timeout=10, verify=False) as c:
            r = c.get(url)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"Erro ao obter configuração OpenID: {e}", url=url)
        raise HTTPException(...)
```

**Trade Service:**
```python
@lru_cache(maxsize=1)
def _get_openid_config() -> Dict[str, Any]:
    """Obtém configuração OpenID do .well-known"""
    url = f"{ISSUER}/.well-known/openid-configuration"
    try:
        with httpx.Client(timeout=10, verify=False) as c:
            r = c.get(url)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error("Erro ao obter configuração OpenID", error=str(e), url=url)
        raise HTTPException(...)
```

**Diferença:** Apenas no formato do log (logging vs structlog)

### Função `verify_bearer_token_or_401()`

**Gateway:**
```python
def verify_bearer_token_or_401(request: Request) -> Dict[str, Any]:
    """Valida token Bearer e retorna claims ou levanta 401"""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        logger.warning("Token Bearer ausente ou inválido")
        raise HTTPException(...)
    
    token = auth.split(" ", 1)[1].strip()
    logger.debug(f"Token extraído, tamanho: {len(token)}")
    
    try:
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        if not kid:
            logger.warning("Token sem 'kid' no header")
            raise HTTPException(...)
        
        jwk = _get_signing_key(kid)
        if not jwk:
            logger.warning(f"Chave pública não encontrada: {kid}")
            raise HTTPException(...)
        
        claims = jwt.decode(
            token,
            jwk,
            algorithms=[unverified.get("alg", "RS256")],
            issuer=ISSUER,
            options={"verify_aud": False},
        )
        
        logger.info(f"Token validado com sucesso - keycloak_id: {claims.get('sub')}, username: {claims.get('preferred_username')}, email: {claims.get('email')}")
        
        return claims
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao validar token: {e}, tipo: {type(e).__name__}")
        raise HTTPException(...)
```

**Trade Service:**
```python
def verify_bearer_token_or_401(request: Request) -> Dict[str, Any]:
    """Valida token Bearer e retorna claims ou levanta 401"""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        logger.warning("Token Bearer ausente ou inválido")
        raise HTTPException(...)
    
    token = auth.split(" ", 1)[1].strip()
    logger.debug("Token extraído", token_length=len(token))
    
    try:
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        if not kid:
            logger.warning("Token sem 'kid' no header")
            raise HTTPException(...)
        
        jwk = _get_signing_key(kid)
        if not jwk:
            logger.warning("Chave pública não encontrada", kid=kid)
            raise HTTPException(...)
        
        claims = jwt.decode(
            token,
            jwk,
            algorithms=[unverified.get("alg", "RS256")],
            issuer=ISSUER,
            options={"verify_aud": False},
        )
        
        # Log removido conforme solicitado
        
        return claims
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao validar token", error=str(e), error_type=type(e).__name__)
        raise HTTPException(...)
```

**Diferenças:**
1. Formato de log (f-string vs structlog)
2. Gateway tem log de sucesso, Trade Service removeu (comentário diz "Log removido conforme solicitado")

---

## 🎯 Conclusão

### O que o Gateway usa:

1. **Arquivo:** `auth/jwt_validator.py`
2. **Logging:** `logging` padrão do Python
3. **ISSUER:** Hardcoded `"https://auth.rendacontinua.com/auth/realms/auth_sso"`
4. **Dependências:** `jose`, `httpx`
5. **Cache:** JWKS cacheado por 10 minutos
6. **Refresh:** Força refresh se chave não encontrada

### Possíveis problemas no Trade Service:

1. **Structlog não configurado** - pode causar erros silenciosos
2. **Dependências faltando** - `structlog` pode não estar instalado
3. **Logs removidos** - dificulta debugging

### Recomendação:

**Copiar o `jwt_validator.py` do Gateway para o Trade Service** e substituir o `keycloak_service.py`, mantendo apenas a diferença de nome do arquivo. Isso garante que ambos usem a mesma implementação que já está funcionando.

