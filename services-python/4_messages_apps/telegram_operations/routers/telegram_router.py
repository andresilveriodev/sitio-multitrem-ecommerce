"""
Router para processamento de mensagens do Telegram
"""

import structlog
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse

from config import settings
from services.keycloak_auth_service import keycloak_auth_service

logger = structlog.get_logger(__name__)

router = APIRouter()

# Instâncias dos serviços serão injetadas pelo app
telegram_service = None
polling_service = None


@router.get("/polling-status")
async def get_polling_status():
    """
    Obtém status do serviço de polling
    """
    if not polling_service:
        return {
            "success": False,
            "error": "Polling service não está disponível"
        }
    
    status = polling_service.get_status()
    return {
        "success": True,
        "polling_status": status,
        "message": "Serviço usando polling (getUpdates) ao invés de webhook"
    }


@router.post("/send-message")
async def send_message(request: Request):
    """
    Endpoint para enviar mensagem via Telegram (uso administrativo/teste)
    """
    try:
        if not telegram_service:
            raise HTTPException(status_code=503, detail="Telegram service não está disponível")
        
        body = await request.json()
        chat_id = body.get("chat_id")
        text = body.get("text")
        
        if not chat_id or not text:
            raise HTTPException(status_code=400, detail="chat_id e text são obrigatórios")
        
        result = await telegram_service.send_message(chat_id=chat_id, text=text)
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao enviar mensagem: {str(e)}")


@router.get("/auth/callback")
async def auth_callback(
    state: Optional[str] = Query(None),
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """
    Endpoint de callback do Keycloak (adaptado de AuthEndpoint.auth)
    Redireciona para o bot do Telegram após autenticação bem-sucedida
    """
    try:
        if error:
            logger.error("Erro na autenticação Keycloak", error=error)
            return HTMLResponse(
                content=f"""
                <html>
                    <body>
                        <h1>Erro na Autenticação</h1>
                        <p>Ocorreu um erro durante a autenticação: {error}</p>
                        <p>Por favor, tente novamente.</p>
                    </body>
                </html>
                """,
                status_code=400
            )
        
        if not state or not code:
            return HTMLResponse(
                content="""
                <html>
                    <body>
                        <h1>Parâmetros Inválidos</h1>
                        <p>State ou code não fornecidos.</p>
                    </body>
                </html>
                """,
                status_code=400
            )
        
        # Completar autenticação
        logger.info(
            "Iniciando troca de code por tokens",
            has_code=bool(code),
            has_state=bool(state),
            code_preview=code[:10] + "..." if code else "None",
            state_preview=state[:10] + "..." if state else "None"
        )
        
        result = await keycloak_auth_service.exchange_code_for_tokens(code=code, state=state)
        
        if not result:
            logger.error("Falha ao completar autenticação", state=state[:8] + "..." if state else "None")
            return HTMLResponse(
                content="""
                <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>Falha na Autenticação</title>
                        <style>
                            body {
                                font-family: Arial, sans-serif;
                                text-align: center;
                                padding: 50px;
                                background-color: #f5f5f5;
                            }
                            .error-box {
                                background-color: white;
                                border-radius: 8px;
                                padding: 30px;
                                max-width: 500px;
                                margin: 0 auto;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            }
                            h1 {
                                color: #d32f2f;
                                margin-bottom: 20px;
                            }
                            p {
                                color: #666;
                                line-height: 1.6;
                            }
                            .retry-button {
                                display: inline-block;
                                margin-top: 20px;
                                padding: 10px 20px;
                                background-color: #0088cc;
                                color: white;
                                text-decoration: none;
                                border-radius: 4px;
                            }
                            .retry-button:hover {
                                background-color: #006ba3;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="error-box">
                            <h1>❌ Falha na Autenticação</h1>
                            <p><strong>Não foi possível completar a autenticação.</strong></p>
                            <p>O servidor de autenticação pode estar temporariamente indisponível (erro 502 Bad Gateway).</p>
                            <p>Por favor, aguarde alguns instantes e tente novamente.</p>
                            <a href="https://web.telegram.org/k/#@BaculejoBot" class="retry-button">Voltar para o Telegram</a>
                        </div>
                    </body>
                </html>
                """,
                status_code=500
            )
        
        telegram_user_id = result.get("telegram_user_id")
        telegram_chat_id = result.get("telegram_chat_id")
        userinfo = result.get("userinfo", {})
        
        logger.info(
            "Autenticação completada com sucesso",
            telegram_user_id=telegram_user_id,
            preferred_username=userinfo.get("preferred_username")
        )
        
        # Enviar mensagem de confirmação no Telegram
        # IMPORTANTE: Enviar como nova mensagem para aparecer no topo e não perder a lógica da conversa
        if telegram_chat_id and telegram_service:
            try:
                username = userinfo.get("preferred_username", "Usuário")
                success_message = (
                    f"✅ Login realizado com sucesso!\n\n"
                    f"Olá, {username}! Você está autenticado e pode continuar editando seu pedido."
                )
                await telegram_service.send_message(
                    chat_id=int(telegram_chat_id),
                    text=success_message
                )
                logger.info("Mensagem de confirmação enviada no Telegram", telegram_user_id=telegram_user_id, chat_id=telegram_chat_id)
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem de confirmação no Telegram: {e}", exc_info=True)
                # Continuar mesmo se falhar o envio da mensagem
        
        # Redirecionar para o bot do Telegram Web
        telegram_redirect_url = "https://web.telegram.org/k/#@BaculejoBot"
        
        logger.info(
            "Redirecionando para Telegram após autenticação",
            telegram_user_id=telegram_user_id,
            redirect_url=telegram_redirect_url
        )
        
        # Usar redirect HTTP 302 ao invés de meta refresh para garantir que funcione
        return RedirectResponse(url=telegram_redirect_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Erro no callback de autenticação: {e}", exc_info=True)
        return HTMLResponse(
            content=f"""
            <html>
                <body>
                    <h1>Erro Interno</h1>
                    <p>Ocorreu um erro ao processar a autenticação.</p>
                </body>
            </html>
            """,
            status_code=500
        )
