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
        self.running = True
        
        # Remover webhook se existir (polling e webhook não podem coexistir)
        await self._remove_webhook_if_exists()
        
        # Iniciar task de polling
        self.polling_task = asyncio.create_task(self._polling_loop())
        logger.info("Serviço de polling iniciado com sucesso")
    
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
    
    async def _remove_webhook_if_exists(self):
        """Remove webhook se existir (polling e webhook não podem coexistir)"""
        try:
            webhook_info = await self.telegram_service.get_webhook_info()
            if webhook_info and webhook_info.get("result", {}).get("url"):
                logger.info("Removendo webhook existente (polling e webhook não podem coexistir)")
                await self.telegram_service.delete_webhook(drop_pending_updates=True)
                logger.info("Webhook removido com sucesso")
        except Exception as e:
            logger.debug(f"Erro ao verificar/remover webhook (pode não existir): {e}")
    
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
