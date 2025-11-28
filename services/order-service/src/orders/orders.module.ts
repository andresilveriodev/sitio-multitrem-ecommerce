import { Module } from '@nestjs/common'
import { TypeOrmModule } from '@nestjs/typeorm'
import { OrdersController } from './orders.controller'
import { OrdersService } from './orders.service'
import { Order } from './entities/order.entity'
import { OrderItem } from './entities/order-item.entity'
import { DeliverySlot } from '../delivery/entities/delivery-slot.entity'

@Module({
  imports: [TypeOrmModule.forFeature([Order, OrderItem, DeliverySlot])],
  controllers: [OrdersController],
  providers: [OrdersService],
  exports: [OrdersService],
})
export class OrdersModule {}


