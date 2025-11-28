import { Controller, Post, Body, HttpCode, HttpStatus } from '@nestjs/common'
import { WebhooksService } from './webhooks.service'

@Controller('webhooks')
export class WebhooksController {
  constructor(private readonly webhooksService: WebhooksService) {}

  @Post('whatsapp')
  @HttpCode(HttpStatus.OK)
  async handleWhatsAppWebhook(@Body() payload: any) {
    return this.webhooksService.handleIncomingMessage(payload)
  }
}

