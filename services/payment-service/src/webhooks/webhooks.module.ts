import { Module } from '@nestjs/common'
import { TypeOrmModule } from '@nestjs/typeorm'
import { ConfigModule, ConfigService } from '@nestjs/config'
import { WebhooksController } from './webhooks.controller'
import { WebhooksService } from './webhooks.service'
import { PaymentEntity } from '../payments/entities/payment.entity'
import { createMercadoPagoClient } from '../config/mercadopago.config'

@Module({
  imports: [TypeOrmModule.forFeature([PaymentEntity])],
  controllers: [WebhooksController],
  providers: [
    WebhooksService,
    {
      provide: 'MERCADO_PAGO_CLIENT',
      useFactory: (configService: ConfigService) => {
        return createMercadoPagoClient(configService)
      },
      inject: [ConfigService],
    },
  ],
})
export class WebhooksModule {}


