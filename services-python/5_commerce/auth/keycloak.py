"""
Validação de tokens Keycloak
"""

import httpx
from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import structlog
# Validação via introspection endpoint do Keycloak
# Não precisa importar jwt diretamente pois usamos introspection

from config import settings

logger = structlog.get_logger()
security = HTTPBearer()


class KeycloakTokenValidator:
    """Validador de tokens Keycloak"""
    
    def __init__(self):
        self.public_key_cache: Optional[str] = None
        self.jwks_cache: Optional[Dict[str, Any]] = None
    
    async def get_public_key(self) -> str:
        """Obtém a chave pública do Keycloak"""
        if self.public_key_cache:
            return self.public_key_cache
        
        try:
            jwks_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(jwks_url, timeout=5.0)
                response.raise_for_status()
                jwks = response.json()
                self.jwks_cache = jwks
                
                # Extrair a chave pública (simplificado - em produção use biblioteca jwks)
                # Por enquanto, vamos usar a validação via introspection
                logger.info("JWKS obtido do Keycloak")
                return ""
        except Exception as e:
            logger.error("Erro ao obter chave pública do Keycloak", error=str(e))
            raise HTTPException(
                status_code=503,
                detail="Serviço de autenticação indisponível"
            )
    
    async def introspect_token(self, token: str) -> Dict[str, Any]:
        """Valida token via introspection endpoint do Keycloak"""
        try:
            introspection_url = (
                f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}"
                f"/protocol/openid-connect/token/introspect"
            )
            
            data = {
                "token": token,
                "client_id": settings.KEYCLOAK_CLIENT_ID,
                "client_secret": settings.KEYCLOAK_CLIENT_SECRET,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    introspection_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=5.0
                )
                response.raise_for_status()
                result = response.json()
                
                if not result.get("active"):
                    raise HTTPException(
                        status_code=401,
                        detail="Token inválido ou expirado"
                    )
                
                logger.info("Token validado via introspection", 
                           username=result.get("username"),
                           client_id=result.get("client_id"))
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error("Erro na validação do token", status_code=e.response.status_code)
            raise HTTPException(
                status_code=401,
                detail="Falha na validação do token"
            )
        except Exception as e:
            logger.error("Erro ao validar token", error=str(e))
            raise HTTPException(
                status_code=401,
                detail="Erro na autenticação"
            )
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Valida token usando introspection"""
        return await self.introspect_token(token)


# Instância global do validador
token_validator = KeycloakTokenValidator()


async def verify_keycloak_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """
    Dependency para validar token Keycloak
    
    Usa o endpoint de introspection do Keycloak para validar o token.
    Retorna os dados do token validado.
    """
    token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token_data = await token_validator.validate_token(token)
        return token_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro inesperado na validação", error=str(e))
        raise HTTPException(
            status_code=401,
            detail="Erro na autenticação"
        )


async def get_current_user(
    token_data: Dict[str, Any] = Depends(verify_keycloak_token)
) -> Dict[str, Any]:
    """
    Dependency que retorna os dados do usuário autenticado
    
    Extrai informações do token validado como:
    - username
    - client_id
    - roles
    - etc.
    """
    return {
        "username": token_data.get("username"),
        "client_id": token_data.get("client_id"),
        "preferred_username": token_data.get("preferred_username"),
        "roles": token_data.get("realm_access", {}).get("roles", []),
        "token_data": token_data
    }
