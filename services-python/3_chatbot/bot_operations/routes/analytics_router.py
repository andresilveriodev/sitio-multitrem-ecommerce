"""
Router para analytics e métricas do chatbot
"""

from fastapi import APIRouter, HTTPException
import structlog

from services.cache_service import cache_service
from services.context_service import context_service
from services.ai_integration import ai_integration
from auth.dependencies import require_colaborador_role
from fastapi import Depends

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chatbot", tags=["analytics"])


@router.get("/analytics/{user_id}")
async def get_user_analytics(
    user_id: str,
    current_user: dict = Depends(require_colaborador_role)
):
    """Busca analytics do usuário"""
    try:
        # Busca contexto do usuário
        context = await context_service.get_conversation_context(user_id)
        
        # Busca métricas de uso do AI Service
        usage_metrics = await ai_integration.get_usage_metrics(user_id)
        
        # Estatísticas do cache
        cache_stats = cache_service.get_cache_stats()
        
        # Calcula métricas do contexto
        total_messages = len(context.message_history)
        ai_messages = sum(1 for msg in context.message_history if msg.requires_ai)
        auto_responses = total_messages - ai_messages
        
        analytics = {
            "user_id": user_id,
            "conversation_stats": {
                "total_messages": total_messages,
                "ai_messages": ai_messages,
                "auto_responses": auto_responses,
                "ai_usage_percentage": (ai_messages / total_messages * 100) if total_messages > 0 else 0,
                "current_topic": context.current_topic,
                "last_interaction": context.last_interaction.isoformat() if context.last_interaction else None
            },
            "cache_stats": {
                "cache_hits": cache_stats["cache_hits"],
                "cache_misses": cache_stats["cache_misses"],
                "hit_rate": cache_stats["hit_rate"],
                "memory_cache_size": cache_stats["memory_cache_size"]
            },
            "ai_service_metrics": usage_metrics or {},
            "context_summary": context.context_summary
        }
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar analytics do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/cost-tracking/{user_id}")
async def get_cost_tracking(
    user_id: str,
    current_user: dict = Depends(require_colaborador_role)
):
    """Busca informações de custos do usuário"""
    try:
        # Busca métricas de uso do AI Service
        usage_metrics = await ai_integration.get_usage_metrics(user_id, "daily")
        
        # Busca assinatura do usuário
        subscription = await ai_integration.get_user_subscription(user_id)
        
        # Busca contexto para calcular economia com cache
        context = await context_service.get_conversation_context(user_id)
        cache_stats = cache_service.get_cache_stats()
        
        # Calcula economia estimada com cache
        estimated_savings = 0
        if cache_stats["cache_hits"] > 0:
            # Estimativa: cada cache hit economiza ~$0.01
            estimated_savings = cache_stats["cache_hits"] * 0.01
        
        cost_data = {
            "user_id": user_id,
            "subscription": subscription or {},
            "usage_metrics": usage_metrics or {},
            "cache_savings": {
                "cache_hits": cache_stats["cache_hits"],
                "estimated_savings_usd": estimated_savings,
                "hit_rate": cache_stats["hit_rate"]
            },
            "cost_optimization": {
                "auto_responses_count": sum(1 for msg in context.message_history if not msg.requires_ai),
                "ai_calls_saved": cache_stats["cache_hits"] + sum(1 for msg in context.message_history if not msg.requires_ai)
            }
        }
        
        return {
            "success": True,
            "cost_tracking": cost_data
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar custos do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/cache-stats")
async def get_cache_stats(
    current_user: dict = Depends(require_colaborador_role)
):
    """Busca estatísticas do cache"""
    try:
        stats = cache_service.get_cache_stats()
        
        return {
            "success": True,
            "cache_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas do cache: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/clear-cache")
async def clear_cache(
    current_user: dict = Depends(require_colaborador_role)
):
    """Limpa todo o cache"""
    try:
        success = await cache_service.clear_cache()
        
        return {
            "success": success,
            "message": "Cache limpo com sucesso" if success else "Erro ao limpar cache"
        }
        
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/invalidate-user-cache/{user_id}")
async def invalidate_user_cache(
    user_id: str,
    current_user: dict = Depends(require_colaborador_role)
):
    """Invalida cache de um usuário específico"""
    try:
        success = await cache_service.invalidate_user_cache(user_id)
        
        return {
            "success": success,
            "message": f"Cache do usuário {user_id} invalidado com sucesso" if success else "Erro ao invalidar cache"
        }
        
    except Exception as e:
        logger.error(f"Erro ao invalidar cache do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/system-health")
async def get_system_health(
    current_user: dict = Depends(require_colaborador_role)
):
    """Verifica saúde geral do sistema"""
    try:
        # Verifica conexão com AI Service
        ai_service_healthy = await ai_integration.validate_ai_connection()
        
        # Verifica cache
        cache_stats = cache_service.get_cache_stats()
        cache_healthy = cache_stats["redis_connected"]
        
        # Verifica contexto service
        context_healthy = context_service.redis is not None
        
        health_status = {
            "ai_service": {
                "status": "healthy" if ai_service_healthy else "unhealthy",
                "url": ai_integration.base_url
            },
            "cache_service": {
                "status": "healthy" if cache_healthy else "unhealthy",
                "redis_connected": cache_healthy,
                "memory_cache_size": cache_stats["memory_cache_size"]
            },
            "context_service": {
                "status": "healthy" if context_healthy else "unhealthy",
                "redis_connected": context_healthy,
                "active_sessions": len(context_service.active_sessions)
            },
            "overall_status": "healthy" if all([ai_service_healthy, cache_healthy, context_healthy]) else "degraded"
        }
        
        return {
            "success": True,
            "health": health_status
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar saúde do sistema: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/performance-metrics")
async def get_performance_metrics(
    current_user: dict = Depends(require_colaborador_role)
):
    """Busca métricas de performance do sistema"""
    try:
        # Estatísticas do cache
        cache_stats = cache_service.get_cache_stats()
        
        # Sessões ativas
        active_sessions = len(context_service.active_sessions)
        
        # Limpeza de sessões expiradas
        expired_sessions = await context_service.cleanup_expired_sessions()
        
        performance_metrics = {
            "cache_performance": {
                "hit_rate": cache_stats["hit_rate"],
                "total_requests": cache_stats["cache_hits"] + cache_stats["cache_misses"],
                "memory_usage": cache_stats["memory_cache_size"]
            },
            "session_management": {
                "active_sessions": active_sessions,
                "expired_sessions_cleaned": expired_sessions
            },
            "system_resources": {
                "redis_connected": cache_stats["redis_connected"],
                "context_service_connected": context_service.redis is not None
            }
        }
        
        return {
            "success": True,
            "performance_metrics": performance_metrics
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar métricas de performance: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
