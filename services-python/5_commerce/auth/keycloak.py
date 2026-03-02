"""
Validação de tokens Keycloak
"""

import httpx
from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import structlog
import logging
import sys
# Validação via introspection endpoint do Keycloak
# Não precisa importar jwt diretamente pois usamos introspection

from config import settings

logger = structlog.get_logger()
# Logger padrão do Python para garantir que apareça no console do uvicorn
std_logger = logging.getLogger(__name__)
# Configurar nível de log para garantir que apareça
std_logger.setLevel(logging.INFO)
if not std_logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)
    std_logger.addHandler(handler)
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
        # Variáveis para logging (definidas no início para uso em exceções)
        introspection_url = (
            f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/token/introspect"
        )
        token_preview = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else "***"
        has_client_secret = bool(settings.KEYCLOAK_CLIENT_SECRET)
        
        try:
            
            logger.info(
                "Iniciando validação de token",
                keycloak_url=settings.KEYCLOAK_SERVER_URL,
                realm=settings.KEYCLOAK_REALM,
                client_id=settings.KEYCLOAK_CLIENT_ID,
                has_client_secret=has_client_secret,
                token_preview=token_preview
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
                
                # Log detalhado antes de verificar status
                try:
                    result = response.json()
                except Exception:
                    result = {"raw_response": response.text[:500]}
                
                # Verificar status HTTP antes de verificar active
                if response.status_code != 200:
                    error_msg = (
                        f"[AUTH ERROR] Keycloak retornou HTTP {response.status_code} na introspection. "
                        f"URL: {introspection_url}, Client ID: {settings.KEYCLOAK_CLIENT_ID}, "
                        f"Has Secret: {has_client_secret}, Response: {result}"
                    )
                    print(error_msg, file=sys.stderr, flush=True)
                    std_logger.error(error_msg)
                    logger.error(
                        "Keycloak retornou erro HTTP na introspection",
                        status_code=response.status_code,
                        response_body=result,
                        introspection_url=introspection_url,
                        client_id=settings.KEYCLOAK_CLIENT_ID,
                        has_client_secret=has_client_secret
                    )
                    response.raise_for_status()
                
                # Verificar se token está ativo
                if not result.get("active"):
                    error_msg = (
                        f"[AUTH ERROR] Token marcado como INATIVO pelo Keycloak. "
                        f"Token preview: {token_preview}, Response: {result}, "
                        f"Client ID: {result.get('client_id')}, Username: {result.get('username')}"
                    )
                    print(error_msg, file=sys.stderr, flush=True)
                    std_logger.error(error_msg)
                    logger.warning(
                        "Token marcado como inativo pelo Keycloak",
                        active=result.get("active"),
                        token_preview=token_preview,
                        keycloak_response=result,
                        client_id=result.get("client_id"),
                        username=result.get("username")
                    )
                    raise HTTPException(
                        status_code=401,
                        detail=f"Token inválido ou expirado. Keycloak response: {result}"
                    )
                
                logger.info("Token validado via introspection", 
                           username=result.get("username"),
                           client_id=result.get("client_id"),
                           exp=result.get("exp"),
                           token_preview=token_preview)
                return result
                
        except httpx.HTTPStatusError as e:
            # Capturar resposta de erro do Keycloak
            error_body = {}
            try:
                error_body = e.response.json()
            except Exception:
                error_body = {"raw_response": e.response.text[:500]}
            
            error_msg = (
                f"[AUTH ERROR] Erro HTTP {e.response.status_code} na validação do token com Keycloak. "
                f"URL: {introspection_url}, Client ID: {settings.KEYCLOAK_CLIENT_ID}, "
                f"Has Secret: {has_client_secret}, Token preview: {token_preview}, "
                f"Keycloak error: {error_body}"
            )
            print(error_msg, file=sys.stderr, flush=True)
            std_logger.error(error_msg)
            logger.error(
                "Erro HTTP na validação do token com Keycloak",
                status_code=e.response.status_code,
                keycloak_error=error_body,
                introspection_url=introspection_url,
                client_id=settings.KEYCLOAK_CLIENT_ID,
                has_client_secret=has_client_secret,
                token_preview=token_preview
            )
            raise HTTPException(
                status_code=401,
                detail=f"Falha na validação do token. Keycloak retornou {e.response.status_code}: {error_body}"
            )
        except httpx.RequestError as e:
            error_msg = (
                f"[AUTH ERROR] Erro de conexão com Keycloak. "
                f"URL: {settings.KEYCLOAK_SERVER_URL}, Realm: {settings.KEYCLOAK_REALM}, "
                f"Error: {str(e)}, Type: {type(e).__name__}"
            )
            std_logger.error(error_msg)
            logger.error(
                "Erro de conexão com Keycloak",
                error=str(e),
                error_type=type(e).__name__,
                keycloak_url=settings.KEYCLOAK_SERVER_URL,
                realm=settings.KEYCLOAK_REALM
            )
            raise HTTPException(
                status_code=503,
                detail=f"Serviço de autenticação indisponível: {str(e)}"
            )
        except HTTPException:
            # Re-raise HTTPExceptions (já logadas acima)
            raise
        except Exception as e:
            logger.error(
                "Erro inesperado ao validar token",
                error=str(e),
                error_type=type(e).__name__,
                token_preview=token_preview
            )
            raise HTTPException(
                status_code=401,
                detail=f"Erro na autenticação: {str(e)}"
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
    
    # Log inicial para rastreamento - usando print() para garantir que apareça
    if token:
        token_preview = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else "***"
        msg = f"[AUTH] Recebida requisição com token. Preview: {token_preview}"
        print(msg, file=sys.stderr, flush=True)
        std_logger.info(msg)
        logger.info("Recebida requisição com token", token_preview=token_preview)
    else:
        msg = "[AUTH] Recebida requisição sem token"
        print(msg, file=sys.stderr, flush=True)
        std_logger.warning(msg)
        logger.warning("Recebida requisição sem token")
    
    if not token:
        msg = "[AUTH ERROR] Tentativa de acesso sem token de autenticação"
        print(msg, file=sys.stderr, flush=True)
        std_logger.warning(msg)
        logger.warning("Tentativa de acesso sem token de autenticação")
        raise HTTPException(
            status_code=401,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token_data = await token_validator.validate_token(token)
        return token_data
    except HTTPException as e:
        # Log adicional para HTTPExceptions - usando print() para garantir
        error_msg = (
            f"[AUTH ERROR] Falha na autenticação. "
            f"Status: {e.status_code}, Detail: {e.detail}"
        )
        print(error_msg, file=sys.stderr, flush=True)
        std_logger.error(error_msg)
        logger.warning(
            "Falha na autenticação",
            status_code=e.status_code,
            detail=e.detail,
            headers=e.headers if hasattr(e, 'headers') else None
        )
        raise
    except Exception as e:
        logger.error(
            "Erro inesperado na validação do token",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=401,
            detail=f"Erro na autenticação: {str(e)}"
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
