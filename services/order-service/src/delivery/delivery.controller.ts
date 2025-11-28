import { Controller, Get, Param } from '@nestjs/common'
import { DeliveryService } from './delivery.service'

@Controller('delivery')
export class DeliveryController {
  constructor(private readonly deliveryService: DeliveryService) {}

  @Get('slots')
  async getAvailableSlots() {
    return this.deliveryService.getAvailableSlots()
  }

  @Get('slots/:date')
  async checkAvailability(@Param('date') date: string) {
    return this.deliveryService.checkAvailability(date)
  }
}


