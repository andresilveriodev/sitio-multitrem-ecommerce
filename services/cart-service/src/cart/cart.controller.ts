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
import { CartService } from './cart.service'
import { AddToCartDto, UpdateCartItemDto, Cart } from '@sitio/shared'

@Controller('cart')
export class CartController {
  constructor(private readonly cartService: CartService) {}

  @Get(':visitorId')
  async getCart(@Param('visitorId') visitorId: string): Promise<Cart> {
    return this.cartService.getCart(visitorId)
  }

  @Post(':visitorId/items')
  @HttpCode(HttpStatus.OK)
  async addItem(
    @Param('visitorId') visitorId: string,
    @Body() dto: AddToCartDto,
  ): Promise<Cart> {
    return this.cartService.addItem(visitorId, dto)
  }

  @Put(':visitorId/items/:productId')
  async updateItem(
    @Param('visitorId') visitorId: string,
    @Param('productId', ParseIntPipe) productId: number,
    @Body() dto: UpdateCartItemDto,
  ): Promise<Cart> {
    return this.cartService.updateItem(visitorId, productId, dto.quantity)
  }

  @Delete(':visitorId/items/:productId')
  @HttpCode(HttpStatus.OK)
  async removeItem(
    @Param('visitorId') visitorId: string,
    @Param('productId', ParseIntPipe) productId: number,
  ): Promise<Cart> {
    return this.cartService.removeItem(visitorId, productId)
  }

  @Delete(':visitorId')
  @HttpCode(HttpStatus.NO_CONTENT)
  async clearCart(@Param('visitorId') visitorId: string): Promise<void> {
    return this.cartService.clearCart(visitorId)
  }
}



