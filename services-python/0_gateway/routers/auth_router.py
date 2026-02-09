"""
Router de autenticação
Recebe requisição do frontend e retorna usuário logado
"""

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from config import settings
from auth.jwt_validator import verify_bearer_token_or_401

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


@router.get("/user")
async def get_current_user(request: Request):
    """
    Recebe token do frontend e retorna dados do usuário logado
    O token deve ser enviado no header: Authorization: Bearer <token>
    """
    try:
        logger.info("Validando token e obtendo dados do usuário")
        
        # Validar token e obter claims (usa ISSUER hardcoded igual ao user_service)
        claims = verify_bearer_token_or_401(request)
        
        logger.info(f"Token válido, retornando dados do usuário - keycloak_id: {claims.get('sub')}, username: {claims.get('preferred_username')}")
        
        # Retornar dados do usuário do token
        return {
            "id": claims.get('sub'),  # Keycloak ID
            "keycloak_id": claims.get('sub'),
            "username": claims.get('preferred_username'),
            "email": claims.get('email'),
            "first_name": claims.get('given_name'),
            "last_name": claims.get('family_name'),
            "roles": claims.get('realm_access', {}).get('roles', []),
            "exp": claims.get('exp'),
            "iat": claims.get('iat')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter usuário: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get("/user-data")
async def get_user_data(request: Request):
    """
    Endpoint alternativo que retorna dados do usuário do token
    (mesma funcionalidade do /user, mantido para compatibilidade)
    """
    return await get_current_user(request)
