import { Module } from '@nestjs/common'
import { TypeOrmModule } from '@nestjs/typeorm'
import { DeliveryController } from './delivery.controller'
import { DeliveryService } from './delivery.service'
import { DeliverySlot } from './entities/delivery-slot.entity'

@Module({
  imports: [TypeOrmModule.forFeature([DeliverySlot])],
  controllers: [DeliveryController],
  providers: [DeliveryService],
  exports: [DeliveryService],
})
export class DeliveryModule {}


