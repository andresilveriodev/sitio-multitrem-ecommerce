"""
Rotas de autenticação
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
import structlog

from models.auth import Token, UserCreate, UserResponse, RegisterRequest, RegisterResponse, UserDataResponse
from models.acl import User as ACLUser
from services.auth_service import auth_service
from services.keycloak_service import keycloak_service
from db_session import get_db_session

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session),
    request: Request = None
):
    """Autentica usuário via Keycloak"""
    try:
        logger.info("Tentativa de login", username=form_data.username)
        
        # Autenticar usuário
        auth_result = await auth_service.authenticate_user(
            db, form_data.username, form_data.password
        )
        
        if not auth_result:
            logger.warning("Login falhou", username=form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = auth_result['user']
        keycloak_token = auth_result['keycloak_token']
        
        logger.info("Login realizado com sucesso", 
                   user_id=user.id, username=user.username)
        
        return {
            "access_token": keycloak_token['access_token'],
            "refresh_token": keycloak_token.get('refresh_token'),
            "token_type": "bearer",
            "expires_in": keycloak_token.get('expires_in'),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profiles": [profile.name for profile in user.profiles],
                "permissions": auth_result['permissions']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro no login", username=form_data.username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db_session)
):
    """Renova token de acesso"""
    try:
        logger.debug("Tentativa de renovação de token")
        
        refresh_result = await auth_service.refresh_token(db, refresh_token)
        
        if not refresh_result:
            logger.warning("Falha na renovação de token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de renovação inválido ou expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info("Token renovado com sucesso")
        
        return {
            "access_token": refresh_result['access_token'],
            "refresh_token": refresh_result.get('refresh_token'),
            "token_type": "bearer",
            "expires_in": refresh_result.get('expires_in')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro na renovação de token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session)
):
    """Faz logout do usuário"""
    try:
        logger.info("Tentativa de logout")
        
        success = await auth_service.logout_user(db, token)
        
        if not success:
            logger.warning("Falha no logout")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido ou sessão não encontrada"
            )
        
        logger.info("Logout realizado com sucesso")
        
        return {
            "message": "Logout realizado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro no logout", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/user", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session)
):
    """Obtém informações do usuário atual"""
    try:
        user = await auth_service.get_current_user(db, token)
        
        if not user:
            logger.warning("Usuário não encontrado")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Obter permissões do usuário
        permissions = await auth_service.acl_service.get_user_permissions_summary(db, user.id)
        
        logger.debug("Informações do usuário consultadas", user_id=user.id)
        
        return UserResponse(
            id=user.id,
            keycloak_id=user.keycloak_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at,
            profiles=[profile.name for profile in user.profiles]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter usuário atual", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/user-data", response_model=UserDataResponse)
async def get_user_data(
    request: Request
):
    """Decodifica token JWT e retorna dados do token (sem consultar banco)"""
    try:
        # Usar o novo validador JWT independente
        from auth.jwt_validator import verify_bearer_token_or_401
        
        logger.info("=== VALIDAÇÃO JWT INDEPENDENTE ===")
        
        # Validar token e obter claims
        claims = verify_bearer_token_or_401(request)
        
        logger.info("=== TOKEN VÁLIDO - DADOS EXTRAÍDOS ===")
        logger.info("Token decodificado com sucesso", 
                   keycloak_id=claims.get('sub'),
                   username=claims.get('preferred_username'),
                   email=claims.get('email'),
                   roles=claims.get('realm_access', {}).get('roles', []),
                   exp=claims.get('exp'),
                   iat=claims.get('iat'))
        
        # Retornar apenas os dados do token
        return UserDataResponse(
            # Dados do Keycloak (do token)
            keycloak_id=claims.get('sub'),
            username=claims.get('preferred_username'),
            email=claims.get('email'),
            first_name=claims.get('given_name'),
            last_name=claims.get('family_name'),
            roles=claims.get('realm_access', {}).get('roles', []),
            exp=claims.get('exp'),
            iat=claims.get('iat'),
            
            # Dados locais como None (não consultados)
            id=None,
            is_active=None,
            is_verified=None,
            last_login=None,
            created_at=None,
            updated_at=None,
            profiles=[],
            permissions=[],
            session_info=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao decodificar token", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/register", response_model=RegisterResponse)
async def register_user(
    user_data: RegisterRequest,
    db: Session = Depends(get_db_session)
):
    """Registra novo usuário via Keycloak Admin API"""
    try:
        logger.info("Tentativa de registro de usuário", 
                   cpf=user_data.cpf, email=user_data.email, phone=user_data.phone)
        
        # 1. Criar usuário no Keycloak via Admin API
        try:
            keycloak_id = await keycloak_service.create_user_in_keycloak({
                "cpf": user_data.cpf,
                "email": user_data.email,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "phone": user_data.phone
            })
            
            if not keycloak_id:
                logger.error("Falha ao criar usuário no Keycloak", email=user_data.email)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao criar usuário no sistema de autenticação"
                )
                
        except ValueError as e:
            # Usuário já existe
            logger.warning("Tentativa de cadastro de usuário já existente", 
                          cpf=user_data.cpf, email=user_data.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        
        # 2. Definir senha temporária se fornecida
        if user_data.password:
            password_set = await keycloak_service.set_user_password(
                keycloak_id, user_data.password, temporary=True
            )
            if not password_set:
                logger.warning("Falha ao definir senha temporária", keycloak_id=keycloak_id)
        
        # 3. Enviar e-mail de verificação
        email_sent = await keycloak_service.send_verification_email(keycloak_id)
        if not email_sent:
            logger.warning("Falha ao enviar e-mail de verificação", keycloak_id=keycloak_id)
        
        # 4. Obter dados completos do usuário criado
        user_info = await keycloak_service.get_user_by_id(keycloak_id)
        
        logger.info("Usuário registrado com sucesso", 
                   keycloak_id=keycloak_id, email=user_data.email)
        
        return RegisterResponse(
            success=True,
            keycloak_id=keycloak_id,
            message="Usuário criado com sucesso. Verifique seu e-mail para ativar a conta.",
            user_data=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro no registro", 
                    cpf=user_data.cpf, email=user_data.email, phone=user_data.phone, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.post("/sync-user/{keycloak_id}")
async def sync_user_to_user_service(
    keycloak_id: str,
    db: Session = Depends(get_db_session)
):
    """Sincroniza dados do usuário com o user_service"""
    try:
        logger.info("Sincronizando usuário com user_service", keycloak_id=keycloak_id)
        
        # 1. Obter dados completos do usuário no Keycloak
        user_info = await keycloak_service.get_user_by_id(keycloak_id)
        
        if not user_info:
            logger.error("Usuário não encontrado no Keycloak", keycloak_id=keycloak_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado no sistema de autenticação"
            )
        
        # 2. Preparar dados para o user_service
        user_data = {
            "keycloak_id": keycloak_id,
            "username": user_info.get("username"),
            "email": user_info.get("email"),
            "first_name": user_info.get("firstName"),
            "last_name": user_info.get("lastName"),
            "is_active": user_info.get("enabled", True),
            "email_verified": user_info.get("emailVerified", False),
            "attributes": user_info.get("attributes", {})
        }
        
        # 3. Aqui você faria a chamada para o user_service
        # Por enquanto, retornamos os dados preparados
        logger.info("Dados do usuário preparados para sincronização", 
                   keycloak_id=keycloak_id)
        
        return {
            "success": True,
            "message": "Dados do usuário preparados para sincronização",
            "user_data": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro na sincronização", keycloak_id=keycloak_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get("/check-user")
async def check_user_exists(
    cpf: str = None,
    email: str = None,
    db: Session = Depends(get_db_session)
):
    """Verifica se usuário já existe no sistema"""
    try:
        if not cpf and not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF ou email deve ser fornecido"
            )
        
        existing_user = await keycloak_service.check_user_exists(cpf=cpf, email=email)
        
        if existing_user:
            return {
                "exists": True,
                "message": "Usuário já existe no sistema",
                "user_info": {
                    "id": existing_user.get("id"),
                    "username": existing_user.get("username"),
                    "email": existing_user.get("email"),
                    "enabled": existing_user.get("enabled", False),
                    "emailVerified": existing_user.get("emailVerified", False)
                }
            }
        else:
            return {
                "exists": False,
                "message": "Usuário não encontrado"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao verificar usuário", cpf=cpf, email=email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )

@router.get("/health")
async def health_check():
    """Verificação de saúde do serviço"""
    return {
        "status": "healthy",
        "service": "auth_service",
        "version": "1.0.0"
    }
