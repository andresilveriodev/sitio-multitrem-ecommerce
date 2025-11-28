import { ConfigService } from '@nestjs/config'

export interface ServiceConfig {
  url: string
  timeout: number
}

export const getServicesConfig = (
  configService: ConfigService,
): Record<string, ServiceConfig> => ({
  product: {
    url:
      configService.get<string>('PRODUCT_SERVICE_URL') ||
      'http://localhost:3001',
    timeout: 30000,
  },
  cart: {
    url:
      configService.get<string>('CART_SERVICE_URL') || 'http://localhost:3002',
    timeout: 30000,
  },
  order: {
    url:
      configService.get<string>('ORDER_SERVICE_URL') ||
      'http://localhost:3003',
    timeout: 30000,
  },
  payment: {
    url:
      configService.get<string>('PAYMENT_SERVICE_URL') ||
      'http://localhost:3004',
    timeout: 30000,
  },
  auth: {
    url:
      configService.get<string>('AUTH_SERVICE_URL') || 'http://localhost:3005',
    timeout: 30000,
  },
  whatsapp: {
    url:
      configService.get<string>('WHATSAPP_SERVICE_URL') ||
      'http://localhost:3006',
    timeout: 30000,
  },
  ai: {
    url: configService.get<string>('AI_SERVICE_URL') || 'http://localhost:3007',
    timeout: 30000,
  },
})

