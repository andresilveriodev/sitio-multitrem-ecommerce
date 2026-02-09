import { Controller, Get, Param } from '@nestjs/common'
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiParam,
} from '@nestjs/swagger'
import { DeliveryService } from './delivery.service'

@ApiTags('delivery')
@Controller('delivery')
export class DeliveryController {
  constructor(private readonly deliveryService: DeliveryService) {}

  @Get('slots')
  @ApiOperation({ summary: 'Listar horários de entrega disponíveis' })
  @ApiResponse({ status: 200, description: 'Lista de horários disponíveis' })
  async getAvailableSlots() {
    return this.deliveryService.getAvailableSlots()
  }

  @Get('slots/:date')
  @ApiOperation({ summary: 'Verificar disponibilidade para uma data específica' })
  @ApiParam({ name: 'date', description: 'Data no formato YYYY-MM-DD', type: String })
  @ApiResponse({ status: 200, description: 'Disponibilidade para a data' })
  async checkAvailability(@Param('date') date: string) {
    return this.deliveryService.checkAvailability(date)
  }
}


