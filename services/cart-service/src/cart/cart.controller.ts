import {
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Body,
  Param,
  HttpCode,
  HttpStatus,
  ParseIntPipe,
} from '@nestjs/common'
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiParam,
  ApiBody,
} from '@nestjs/swagger'
import { CartService } from './cart.service'
import { AddToCartDto, UpdateCartItemDto, Cart } from '@sitio/shared'

@ApiTags('cart')
@Controller('cart')
export class CartController {
  constructor(private readonly cartService: CartService) {}

  @Get(':visitorId')
  @ApiOperation({ summary: 'Obter carrinho do visitante' })
  @ApiParam({ name: 'visitorId', description: 'ID do visitante', type: String })
  @ApiResponse({ status: 200, description: 'Carrinho encontrado', type: Cart })
  async getCart(@Param('visitorId') visitorId: string): Promise<Cart> {
    return this.cartService.getCart(visitorId)
  }

  @Post(':visitorId/items')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Adicionar item ao carrinho' })
  @ApiParam({ name: 'visitorId', description: 'ID do visitante', type: String })
  @ApiBody({ type: AddToCartDto })
  @ApiResponse({ status: 200, description: 'Item adicionado ao carrinho', type: Cart })
  async addItem(
    @Param('visitorId') visitorId: string,
    @Body() dto: AddToCartDto,
  ): Promise<Cart> {
    return this.cartService.addItem(visitorId, dto)
  }

  @Put(':visitorId/items/:productId')
  @ApiOperation({ summary: 'Atualizar quantidade de item no carrinho' })
  @ApiParam({ name: 'visitorId', description: 'ID do visitante', type: String })
  @ApiParam({ name: 'productId', description: 'ID do produto', type: Number })
  @ApiBody({ type: UpdateCartItemDto })
  @ApiResponse({ status: 200, description: 'Item atualizado', type: Cart })
  async updateItem(
    @Param('visitorId') visitorId: string,
    @Param('productId', ParseIntPipe) productId: number,
    @Body() dto: UpdateCartItemDto,
  ): Promise<Cart> {
    return this.cartService.updateItem(visitorId, productId, dto.quantity)
  }

  @Delete(':visitorId/items/:productId')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Remover item do carrinho' })
  @ApiParam({ name: 'visitorId', description: 'ID do visitante', type: String })
  @ApiParam({ name: 'productId', description: 'ID do produto', type: Number })
  @ApiResponse({ status: 200, description: 'Item removido', type: Cart })
  async removeItem(
    @Param('visitorId') visitorId: string,
    @Param('productId', ParseIntPipe) productId: number,
  ): Promise<Cart> {
    return this.cartService.removeItem(visitorId, productId)
  }

  @Delete(':visitorId')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Limpar carrinho' })
  @ApiParam({ name: 'visitorId', description: 'ID do visitante', type: String })
  @ApiResponse({ status: 204, description: 'Carrinho limpo com sucesso' })
  async clearCart(@Param('visitorId') visitorId: string): Promise<void> {
    return this.cartService.clearCart(visitorId)
  }
}



