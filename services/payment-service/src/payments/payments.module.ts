import { Module } from '@nestjs/common'
import { TypeOrmModule } from '@nestjs/typeorm'
import { ConfigModule, ConfigService } from '@nestjs/config'
import { PaymentsController } from './payments.controller'
import { PaymentsService } from './payments.service'
import { PaymentEntity } from './entities/payment.entity'
import { createMercadoPagoClient } from '../config/mercadopago.config'

@Module({
  imports: [TypeOrmModule.forFeature([PaymentEntity])],
  controllers: [PaymentsController],
  providers: [
    PaymentsService,
    {
      provide: 'MERCADO_PAGO_CLIENT',
      useFactory: (configService: ConfigService) => {
        return createMercadoPagoClient(configService)
      },
      inject: [ConfigService],
    },
  ],
  exports: [PaymentsService],
})
export class PaymentsModule {}


