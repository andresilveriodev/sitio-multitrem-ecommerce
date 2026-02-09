"""
Validador JWT independente usando .well-known + JWKS
"""
import os
import time
import httpx
from jose import jwt
from fastapi import HTTPException, status, Request
from functools import lru_cache
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()

# Configuração do Keycloak
ISSUER = "https://auth.rendacontinua.com/auth/realms/auth_sso"  # Deve bater com o 'iss' do token

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter configuração OpenID: {str(e)}"
        )

_jwks_cache = {"keys": None, "exp": 0}

def _get_jwks() -> Dict[str, Any]:
    """Obtém JWKS com cache de 10 minutos"""
    global _jwks_cache
    now = int(time.time())
    
    if _jwks_cache["keys"] and _jwks_cache["exp"] > now:
        logger.debug("Retornando JWKS do cache")
        return _jwks_cache["keys"]
    
    try:
        jwks_uri = _get_openid_config()["jwks_uri"]
        logger.info("Obtendo JWKS", jwks_uri=jwks_uri)
        
        with httpx.Client(timeout=10, verify=False) as c:
            r = c.get(jwks_uri)
            r.raise_for_status()
            data = r.json()
        
        _jwks_cache = {"keys": data, "exp": now + 600}  # Cache por 10 minutos
        logger.info("JWKS obtido com sucesso", keys_count=len(data.get("keys", [])))
        return data
        
    except Exception as e:
        logger.error("Erro ao obter JWKS", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter chaves públicas: {str(e)}"
        )

def _get_signing_key(kid: str) -> Optional[Dict[str, Any]]:
    """Obtém chave de assinatura pelo kid"""
    jwks = _get_jwks()
    
    # Primeira tentativa
    for k in jwks["keys"]:
        if k.get("kid") == kid:
            logger.debug("Chave encontrada", kid=kid)
            return k
    
    # Força refresh e tenta novamente (rotação de chaves)
    logger.warning("Chave não encontrada, forçando refresh do cache", kid=kid)
    _jwks_cache["exp"] = 0
    jwks = _get_jwks()
    
    for k in jwks["keys"]:
        if k.get("kid") == kid:
            logger.info("Chave encontrada após refresh", kid=kid)
            return k
    
    logger.error("Chave não encontrada após refresh", kid=kid)
    return None

def verify_bearer_token_or_401(request: Request) -> Dict[str, Any]:
    """Valida token Bearer e retorna claims ou levanta 401"""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        logger.warning("Token Bearer ausente ou inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token de autenticação necessário",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth.split(" ", 1)[1].strip()
    logger.debug("Token extraído", token_length=len(token))

    try:
        # Obter header não verificado para pegar o kid
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        if not kid:
            logger.warning("Token sem 'kid' no header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token inválido: sem 'kid'"
            )

        # Obter chave de assinatura
        jwk = _get_signing_key(kid)
        if not jwk:
            logger.warning("Chave pública não encontrada", kid=kid)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Chave pública não encontrada"
            )

        # Decodificar e validar token
        claims = jwt.decode(
            token,
            jwk,  # jose aceita JWK dict
            algorithms=[unverified.get("alg", "RS256")],
            issuer=ISSUER,
            options={"verify_aud": False},  # Não verificar audience por enquanto
        )
        
        logger.info("Token validado com sucesso", 
                   keycloak_id=claims.get('sub'),
                   username=claims.get('preferred_username'),
                   email=claims.get('email'))
        
        return claims
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao validar token", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Token inválido: {str(e)}"
        )






