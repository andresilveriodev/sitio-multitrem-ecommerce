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
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiParam,
  ApiBody,
} from '@nestjs/swagger'
import { PaymentsService } from './payments.service'
import { CreatePaymentDto } from '@sitio/shared'

@ApiTags('payments')
@Controller('payments')
export class PaymentsController {
  constructor(private readonly paymentsService: PaymentsService) {}

  @Post('pix')
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Criar pagamento Pix' })
  @ApiBody({ type: CreatePaymentDto })
  @ApiResponse({ status: 201, description: 'Pagamento Pix criado com sucesso' })
  async createPix(@Body() dto: CreatePaymentDto) {
    return this.paymentsService.createPixPayment(Number(dto.orderId))
  }

  @Post('boleto')
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Criar pagamento Boleto' })
  @ApiBody({ type: CreatePaymentDto })
  @ApiResponse({ status: 201, description: 'Pagamento Boleto criado com sucesso' })
  async createBoleto(@Body() dto: CreatePaymentDto) {
    return this.paymentsService.createBoletoPayment(Number(dto.orderId))
  }

  @Get(':id')
  @ApiOperation({ summary: 'Buscar pagamento por ID' })
  @ApiParam({ name: 'id', description: 'ID do pagamento', type: Number })
  @ApiResponse({ status: 200, description: 'Pagamento encontrado' })
  async findOne(@Param('id', ParseIntPipe) id: number) {
    return this.paymentsService.findOne(id)
  }

  @Get('order/:orderId')
  @ApiOperation({ summary: 'Buscar pagamento por pedido' })
  @ApiParam({ name: 'orderId', description: 'ID do pedido', type: Number })
  @ApiResponse({ status: 200, description: 'Pagamento encontrado' })
  async findByOrder(@Param('orderId', ParseIntPipe) orderId: number) {
    return this.paymentsService.findByOrder(orderId)
  }
}

