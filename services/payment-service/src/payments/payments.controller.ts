import {
  Controller,
  Get,
  Post,
  Body,
  Param,
  ParseIntPipe,
  HttpCode,
  HttpStatus,
} from '@nestjs/common'
import { PaymentsService } from './payments.service'
import { CreatePaymentDto } from '@sitio/shared'

@Controller('payments')
export class PaymentsController {
  constructor(private readonly paymentsService: PaymentsService) {}

  @Post('pix')
  @HttpCode(HttpStatus.CREATED)
  async createPix(@Body() dto: CreatePaymentDto) {
    return this.paymentsService.createPixPayment(Number(dto.orderId))
  }

  @Post('boleto')
  @HttpCode(HttpStatus.CREATED)
  async createBoleto(@Body() dto: CreatePaymentDto) {
    return this.paymentsService.createBoletoPayment(Number(dto.orderId))
  }

  @Get(':id')
  async findOne(@Param('id', ParseIntPipe) id: number) {
    return this.paymentsService.findOne(id)
  }

  @Get('order/:orderId')
  async findByOrder(@Param('orderId', ParseIntPipe) orderId: number) {
    return this.paymentsService.findByOrder(orderId)
  }
}

