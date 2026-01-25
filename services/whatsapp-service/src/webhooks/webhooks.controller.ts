import { Controller, Post, Body, HttpCode, HttpStatus, Logger } from '@nestjs/common'
import { WebhooksService } from './webhooks.service'

@Controller('webhooks')
export class WebhooksController {
  private readonly logger = new Logger('WebhooksController')

  constructor(private readonly webhooksService: WebhooksService) {}

  @Post('whatsapp')
  @HttpCode(HttpStatus.OK)
  async handleWhatsAppWebhook(@Body() payload: any) {
    try {
      // Log TODAS as requisições recebidas
      this.logger.log('🔔 WEBHOOK RECEBIDO!')
      this.logger.log(`📋 Event: ${payload.event}`)
      this.logger.log(`📱 Instance: ${payload.instance}`)
      
      if (payload.data) {
        const msg = payload.data
        if (msg.key) {
          this.logger.log(`📞 De: ${msg.key.remoteJid}`)
          this.logger.log(`👤 Nome: ${msg.pushName || 'N/A'}`)
        }
        if (msg.message) {
          this.logger.log(`💬 Mensagem: ${JSON.stringify(msg.message)}`)
        }
      }
      
      this.logger.log(`📦 Payload completo: ${JSON.stringify(payload).substring(0, 500)}...`)
      
      const result = await this.webhooksService.handleIncomingMessage(payload)
      
      // Retornar resposta simples para Evolution API
      return { success: true, processed: result.processed || false }
    } catch (error: any) {
      this.logger.error(`❌ [WebhooksController] Erro ao processar webhook: ${error.message}`)
      this.logger.error(error.stack)
      // Retornar sucesso mesmo em caso de erro para evitar retentativas infinitas
      return { success: false, error: error.message }
    }
  }
}

