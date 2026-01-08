import { Controller, Post, Body, HttpCode, HttpStatus, Logger } from '@nestjs/common'
import { WebhooksService } from './webhooks.service'

@Controller('webhooks')
export class WebhooksController {
  private readonly logger = new Logger('WebhooksController')

  constructor(private readonly webhooksService: WebhooksService) {}

  @Post('whatsapp')
  @HttpCode(HttpStatus.OK)
  async handleWhatsAppWebhook(@Body() payload: any) {
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
    
    return this.webhooksService.handleIncomingMessage(payload)
  }
}

