import { ConfigService } from '@nestjs/config'
import { MercadoPagoConfig, Payment } from 'mercadopago'

export const createMercadoPagoClient = (
  configService: ConfigService,
): Payment => {
  const accessToken = configService.get<string>('MERCADO_PAGO_ACCESS_TOKEN')
  
  if (!accessToken) {
    throw new Error('MERCADO_PAGO_ACCESS_TOKEN is required')
  }

  const client = new MercadoPagoConfig({
    accessToken,
    options: {
      timeout: 5000,
      idempotencyKey: 'abc',
    },
  })

  return new Payment(client)
}


