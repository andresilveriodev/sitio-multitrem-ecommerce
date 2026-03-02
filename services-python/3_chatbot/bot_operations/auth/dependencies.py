"""
Dependências de autenticação e autorização
"""
from fastapi import Depends, HTTPException, status, Request
from typing import Dict, Any
import structlog

from .jwt_validator import verify_bearer_token_or_401

logger = structlog.get_logger()


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency para obter usuário atual autenticado.
    Valida o token JWT e retorna os claims do usuário.
    
    O FastAPI injeta automaticamente o Request quando usado como Depends.
    """
    logger.info(
        "🔐 get_current_user chamado",
        path=request.url.path,
        method=request.method,
        has_authorization="authorization" in [k.lower() for k in request.headers.keys()]
    )
    
    try:
        user = verify_bearer_token_or_401(request)
        logger.info(
            "✅ Usuário autenticado com sucesso",
            path=request.url.path,
            user_id=user.get('sub'),
            username=user.get('preferred_username')
        )
        return user
    except Exception as e:
        logger.error(
            "❌ Erro ao autenticar usuário",
            path=request.url.path,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


def require_colaborador_role(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency que verifica se o usuário tem o role 'colaborador'.
    Deve ser usado em endpoints que requerem permissão de colaborador.
    
    Args:
        current_user: Claims do token JWT (obtido via get_current_user)
    
    Returns:
        Dict com os claims do usuário autenticado e com role colaborador
    
    Raises:
        HTTPException 403: Se o usuário não tiver o role 'colaborador'
    """
    # Verifica roles do realm
    realm_roles = current_user.get('realm_access', {}).get('roles', [])
    
    # Verifica roles do resource (client)
    resource_access = current_user.get('resource_access', {})
    client_roles = []
    for resource, access in resource_access.items():
        if isinstance(access, dict) and 'roles' in access:
            client_roles.extend(access.get('roles', []))
    
    # Verifica se tem o role 'colaborador' em qualquer lugar
    all_roles = realm_roles + client_roles
    
    if 'colaborador' not in all_roles:
        username = current_user.get('preferred_username', 'unknown')
        logger.warning(
            "Acesso negado: usuário sem role 'colaborador'",
            username=username,
            user_id=current_user.get('sub'),
            realm_roles=realm_roles,
            client_roles=client_roles
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: role 'colaborador' é necessário"
        )
    
    logger.info(
        "Acesso autorizado: usuário com role 'colaborador'",
        username=current_user.get('preferred_username'),
        user_id=current_user.get('sub')
    )
    
    return current_user


def check_colaborador_role(current_user: Dict[str, Any]) -> bool:
    """
    Verifica se o usuário tem role 'colaborador' sem levantar exceção.
    Útil para verificações condicionais.
    
    Args:
        current_user: Claims do token JWT
        
    Returns:
        bool: True se tem role 'colaborador', False caso contrário
    """
    realm_roles = current_user.get('realm_access', {}).get('roles', [])
    resource_access = current_user.get('resource_access', {})
    client_roles = []
    for resource, access in resource_access.items():
        if isinstance(access, dict) and 'roles' in access:
            client_roles.extend(access.get('roles', []))
    
    all_roles = realm_roles + client_roles
    return 'colaborador' in all_roles