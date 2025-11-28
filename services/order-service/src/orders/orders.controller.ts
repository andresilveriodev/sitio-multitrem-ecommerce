import {
  Controller,
  Get,
  Post,
  Put,
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
import { OrdersService } from './orders.service'
import { CreateOrderDto, UpdateOrderStatusDto, OrderStatus, PaymentStatus } from '@sitio/shared'

@ApiTags('orders')
@Controller('orders')
export class OrdersController {
  constructor(private readonly ordersService: OrdersService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Criar novo pedido' })
  @ApiBody({ type: CreateOrderDto })
  @ApiResponse({ status: 201, description: 'Pedido criado com sucesso' })
  @ApiResponse({ status: 400, description: 'Dados inválidos ou carrinho vazio' })
  async create(@Body() dto: CreateOrderDto) {
    return this.ordersService.create(dto)
  }

  @Get(':id')
  @ApiOperation({ summary: 'Buscar pedido por ID' })
  @ApiParam({ name: 'id', description: 'ID do pedido', type: Number })
  @ApiResponse({ status: 200, description: 'Pedido encontrado' })
  @ApiResponse({ status: 404, description: 'Pedido não encontrado' })
  async findOne(@Param('id', ParseIntPipe) id: number) {
    return this.ordersService.findOne(id)
  }

  @Get('visitor/:visitorId')
  @ApiOperation({ summary: 'Buscar pedidos por visitante' })
  @ApiParam({ name: 'visitorId', description: 'ID do visitante', type: String })
  @ApiResponse({ status: 200, description: 'Lista de pedidos do visitante' })
  async findByVisitor(@Param('visitorId') visitorId: string) {
    return this.ordersService.findByVisitor(visitorId)
  }

  @Put(':id/status')
  @ApiOperation({ summary: 'Atualizar status do pedido' })
  @ApiParam({ name: 'id', description: 'ID do pedido', type: Number })
  @ApiBody({ type: UpdateOrderStatusDto })
  @ApiResponse({ status: 200, description: 'Status atualizado' })
  async updateStatus(
    @Param('id', ParseIntPipe) id: number,
    @Body() dto: UpdateOrderStatusDto,
  ) {
    return this.ordersService.updateStatus(id, dto.status as OrderStatus)
  }

  @Put(':id/payment-status')
  @ApiOperation({ summary: 'Atualizar status de pagamento' })
  @ApiParam({ name: 'id', description: 'ID do pedido', type: Number })
  @ApiBody({ schema: { type: 'object', properties: { paymentStatus: { type: 'string', enum: ['pending', 'paid', 'failed', 'refunded'] } } } })
  @ApiResponse({ status: 200, description: 'Status de pagamento atualizado' })
  async updatePaymentStatus(
    @Param('id', ParseIntPipe) id: number,
    @Body('paymentStatus') paymentStatus: PaymentStatus,
  ) {
    return this.ordersService.updatePaymentStatus(id, paymentStatus)
  }
}

