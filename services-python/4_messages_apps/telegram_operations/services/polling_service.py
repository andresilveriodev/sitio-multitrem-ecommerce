"""
Serviço de Polling para buscar atualizações do Telegram
Usa getUpdates ao invés de webhook
"""

import asyncio
import structlog
from typing import Optional, Dict, Any
from config import settings
from services.telegram_service import TelegramService

logger = structlog.get_logger(__name__)


class PollingService:
    """Serviço para buscar atualizações do Telegram via polling"""
    
    def __init__(self, telegram_service: TelegramService):
        self.telegram_service = telegram_service
        self.running = False
        self.last_update_id = 0
        self.polling_task: Optional[asyncio.Task] = None
        self.polling_interval = 1  # Segundos entre cada poll (mínimo recomendado: 1)
        self.timeout = 10  # Timeout para long polling (segundos)
    
    async def start(self):
        """Inicia o serviço de polling"""
        if self.running:
            logger.warning("Polling já está rodando")
            return
        
        logger.info("Iniciando serviço de polling do Telegram...")
        
        # Remover webhook se existir (polling e webhook não podem coexistir)
        await self._ensure_webhook_removed()
        
        self.running = True
        
        # Iniciar task de polling
        self.polling_task = asyncio.create_task(self._polling_loop())
        logger.info("Serviço de polling iniciado com sucesso")
    
    async def _ensure_webhook_removed(self):
        """Garante que o webhook foi removido antes de iniciar polling"""
        logger.info("Verificando e removendo webhook (se existir)...")
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                # Verificar se há webhook configurado
                logger.debug(f"Verificando webhook (tentativa {attempt + 1}/{max_attempts})...")
                webhook_info = await self.telegram_service.get_webhook_info()
                
                webhook_url = None
                if webhook_info and webhook_info.get("ok") and webhook_info.get("result"):
                    webhook_url = webhook_info.get("result", {}).get("url", "")
                    if webhook_url:
                        webhook_url = webhook_url.strip()
                
                if webhook_url:
                    logger.info(f"Webhook encontrado: {webhook_url} - Removendo... (tentativa {attempt + 1}/{max_attempts})")
                    try:
                        delete_result = await self.telegram_service.delete_webhook(drop_pending_updates=True)
                        logger.info(f"Comando delete_webhook executado. Resultado: {delete_result}")
                        await asyncio.sleep(3)  # Aguardar propagação (aumentado para 3 segundos)
                        
                        # Verificar se foi removido
                        webhook_info_after = await self.telegram_service.get_webhook_info()
                        webhook_url_after = None
                        if webhook_info_after and webhook_info_after.get("ok") and webhook_info_after.get("result"):
                            webhook_url_after = webhook_info_after.get("result", {}).get("url", "")
                            if webhook_url_after:
                                webhook_url_after = webhook_url_after.strip()
                        
                        if webhook_url_after:
                            logger.warning(f"Webhook ainda configurado após remoção (URL: {webhook_url_after}). Tentando novamente...")
                            if attempt < max_attempts - 1:
                                await asyncio.sleep(3)
                                continue
                            else:
                                logger.error(f"Webhook ainda configurado após {max_attempts} tentativas! URL: {webhook_url_after}")
                                logger.error("Polling pode não funcionar corretamente enquanto o webhook estiver ativo.")
                        else:
                            logger.info("✅ Webhook removido com sucesso!")
                            await asyncio.sleep(2)  # Aguardar propagação final
                            return
                    except Exception as delete_error:
                        logger.error(f"Erro ao executar delete_webhook: {delete_error}", exc_info=True)
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(2)
                            continue
                else:
                    logger.info("✅ Nenhum webhook configurado - pronto para polling")
                    return
                    
            except Exception as e:
                logger.error(f"Erro ao verificar/remover webhook (tentativa {attempt + 1}): {e}", exc_info=True)
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                else:
                    logger.error("Não foi possível remover webhook após todas as tentativas. Polling pode não funcionar.")
        
        logger.warning("Finalizando verificação de webhook. Polling será iniciado mesmo se webhook ainda estiver ativo.")
    
    async def stop(self):
        """Para o serviço de polling"""
        logger.info("Parando serviço de polling...")
        self.running = False
        
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Serviço de polling parado")
    
    async def _polling_loop(self):
        """Loop principal de polling"""
        logger.info(f"Iniciando loop de polling (intervalo: {self.polling_interval}s, timeout: {self.timeout}s)")
        
        while self.running:
            try:
                # Buscar atualizações
                # Se last_update_id é 0, não passar offset (buscar todas pendentes)
                # Se last_update_id > 0, passar offset = last_update_id + 1
                offset = None if self.last_update_id == 0 else self.last_update_id + 1
                
                updates = await self.telegram_service.get_updates(
                    offset=offset,
                    timeout=self.timeout
                )
                
                if updates:
                    logger.info(f"Recebidas {len(updates)} atualização(ões)")
                    
                    for update in updates:
                        update_id = update.get("update_id")
                        
                        # Atualizar último ID processado
                        if update_id and update_id > self.last_update_id:
                            self.last_update_id = update_id
                        
                        # Processar atualização
                        try:
                            await self.telegram_service.process_update(update)
                        except Exception as e:
                            logger.error(f"Erro ao processar atualização {update_id}: {e}", exc_info=True)
                            # Continuar processando outras atualizações mesmo se uma falhar
                
                # Aguardar antes da próxima busca (long polling já faz timeout)
                # Se recebeu atualizações, processar imediatamente
                # Se não recebeu, o timeout já passou, então buscar novamente
                
            except asyncio.CancelledError:
                logger.info("Polling cancelado")
                break
            except Exception as e:
                logger.error(f"Erro no loop de polling: {e}", exc_info=True)
                # Aguardar antes de tentar novamente em caso de erro
                await asyncio.sleep(self.polling_interval)
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do polling"""
        return {
            "running": self.running,
            "last_update_id": self.last_update_id,
            "polling_interval": self.polling_interval,
            "timeout": self.timeout
        }
