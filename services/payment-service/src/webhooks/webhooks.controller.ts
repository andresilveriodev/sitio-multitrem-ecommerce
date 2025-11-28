import { Controller, Post, Body, Headers, HttpCode, HttpStatus } from '@nestjs/common'
import { WebhooksService } from './webhooks.service'

@Controller('webhooks')
export class WebhooksController {
  constructor(private readonly webhooksService: WebhooksService) {}

  @Post('mercadopago')
  @HttpCode(HttpStatus.OK)
  async handleMercadoPago(
    @Body() data: any,
    @Headers('x-signature') signature?: string,
  ) {
    // TODO: Validar assinatura do webhook
    // Por enquanto, processar diretamente
    await this.webhooksService.handlePaymentNotification(data)
    return { received: true }
  }
}


