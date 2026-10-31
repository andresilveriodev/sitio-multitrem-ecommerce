"""
WhatsApp Gateway — integração Evolution API (somente canal).
"""

import logging

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from routers import messages, webhook
from services.chatbot_client import ChatbotClient
from services.dedupe_cache import DedupeCache, RecentEventsBuffer
from services.evolution_client import EvolutionClient

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = structlog.get_logger(__name__)

chatbot_client = ChatbotClient()
evolution_client = EvolutionClient()
dedupe_cache = DedupeCache(ttl_seconds=settings.DEDUPE_TTL_SECONDS)
recent_events = RecentEventsBuffer(limit=settings.RECENT_EVENTS_LIMIT)

# Documentação OpenAPI só via Host local (não via túnel / internet)
_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "[::1]"})


def _is_local_host(request: Request) -> bool:
    """True apenas se o Host for localhost e sem headers de Cloudflare Tunnel."""
    if request.headers.get("cf-ray") or request.headers.get("cf-connecting-ip"):
        return False
    host = (request.headers.get("host") or "").split("%")[0]
    host = host.split(":")[0].strip().lower()
    return host in _LOCAL_HOSTS


class LocalDocsOnlyMiddleware(BaseHTTPMiddleware):
    """Bloqueia /docs, /redoc e /openapi.json fora de localhost."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        is_docs = (
            path.rstrip("/") in _DOCS_PATHS
            or path.startswith("/docs/")
            or path.startswith("/redoc/")
        )
        if is_docs and not _is_local_host(request):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return await call_next(request)


app = FastAPI(
    title="WhatsApp Gateway",
    description="Gateway Evolution API → Chatbot (sem lógica de negócio)",
    version="1.0.0",
)

app.add_middleware(LocalDocsOnlyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(messages.router)

webhook.chatbot_client = chatbot_client
webhook.dedupe_cache = dedupe_cache
webhook.recent_events = recent_events
messages.evolution_client = evolution_client


@app.get("/")
async def root():
    return {
        "service": "whatsapp_gateway",
        "status": "running",
        "version": "1.0.0",
        "role": "evolution_channel_gateway",
        "port": settings.PORT,
    }


@app.get("/health")
async def health():
    secret_ok = bool((settings.EVOLUTION_WEBHOOK_SECRET or "").strip())
    send_ok = evolution_client.configured
    return {
        "status": "healthy" if secret_ok else "degraded",
        "service": "whatsapp_gateway",
        "webhook_secret_configured": secret_ok,
        "evolution_send_configured": send_ok,
        "chatbot_url": settings.CHATBOT_SERVICE_URL,
        "instance_filter": settings.EVOLUTION_INSTANCE_NAME or None,
        "recent_events": len(recent_events.list()) if recent_events else 0,
    }


@app.on_event("startup")
async def startup_event():
    logger.info(
        "WhatsApp Gateway iniciando",
        port=settings.PORT,
        chatbot=settings.CHATBOT_SERVICE_URL,
        instance=settings.EVOLUTION_INSTANCE_NAME,
        secret_configured=bool((settings.EVOLUTION_WEBHOOK_SECRET or "").strip()),
    )


@app.on_event("shutdown")
async def shutdown_event():
    await chatbot_client.close()
    await evolution_client.close()
    logger.info("WhatsApp Gateway encerrado")
