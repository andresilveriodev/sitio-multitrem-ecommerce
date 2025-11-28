import { Injectable, Inject } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import Redis from 'ioredis'
import axios from 'axios'
import { Cart, CartItem, AddToCartDto, MAX_CART_ITEM_QUANTITY, CART_TTL_HOURS } from '@sitio/shared'

@Injectable()
export class CartService {
  private readonly redis: Redis
  private readonly productServiceUrl: string

  constructor(
    @Inject('REDIS_CLIENT') private readonly redisClient: Redis,
    private readonly configService: ConfigService,
  ) {
    this.redis = redisClient
    this.productServiceUrl = configService.get<string>(
      'PRODUCT_SERVICE_URL',
      'http://localhost:3001',
    )
  }

  private getCartKey(visitorId: string): string {
    return `cart:${visitorId}`
  }

  private async fetchProduct(productId: number) {
    try {
      const response = await axios.get(
        `${this.productServiceUrl}/products/${productId}`,
      )
      return response.data
    } catch (error) {
      throw new Error(`Product ${productId} not found`)
    }
  }

  private calculateTotal(items: CartItem[]): number {
    return items.reduce((total, item) => total + item.subtotal, 0)
  }

  private calculateItemSubtotal(quantity: number, unitPrice: number): number {
    return quantity * unitPrice
  }

  async getCart(visitorId: string): Promise<Cart> {
    const key = this.getCartKey(visitorId)
    const cartData = await this.redis.get(key)

    if (!cartData) {
      // Criar carrinho vazio
      const emptyCart: Cart = {
        id: `cart-${visitorId}-${Date.now()}`,
        visitorId,
        items: [],
        total: 0,
        itemCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }
      await this.redis.setex(
        key,
        CART_TTL_HOURS * 3600,
        JSON.stringify(emptyCart),
      )
      return emptyCart
    }

    return JSON.parse(cartData) as Cart
  }

  async addItem(visitorId: string, dto: AddToCartDto): Promise<Cart> {
    const cart = await this.getCart(visitorId)

    // Buscar produto no product-service
    const product = await this.fetchProduct(dto.productId)

    // Validar quantidade máxima
    if (dto.quantity > MAX_CART_ITEM_QUANTITY) {
      throw new Error(
        `Maximum quantity per item is ${MAX_CART_ITEM_QUANTITY}`,
      )
    }

    // Para kits, validar selectedItems
    if (product.category === 'kit' && product.kitSize) {
      if (!dto.selectedItems || dto.selectedItems.length !== product.kitSize) {
        throw new Error(
          `Kit requires exactly ${product.kitSize} selected items`,
        )
      }
    }

    // Verificar se item já existe no carrinho
    const existingItemIndex = cart.items.findIndex((item) => {
      if (item.productId === dto.productId) {
        if (product.category === 'kit') {
          // Para kits, comparar selectedItems
          const itemSelected = item.selectedItems?.sort().join(',')
          const dtoSelected = dto.selectedItems?.sort().join(',')
          return itemSelected === dtoSelected
        }
        return true
      }
      return false
    })

    if (existingItemIndex >= 0) {
      // Item existe, somar quantidade
      const existingItem = cart.items[existingItemIndex]
      const newQuantity = existingItem.quantity + dto.quantity

      if (newQuantity > MAX_CART_ITEM_QUANTITY) {
        throw new Error(
          `Maximum quantity per item is ${MAX_CART_ITEM_QUANTITY}`,
        )
      }

      cart.items[existingItemIndex] = {
        ...existingItem,
        quantity: newQuantity,
        subtotal: this.calculateItemSubtotal(newQuantity, existingItem.unitPrice),
      }
    } else {
      // Novo item
      const newItem: CartItem = {
        productId: dto.productId,
        visitorId,
        productName: product.name,
        quantity: dto.quantity,
        unitPrice: product.price,
        selectedItems: dto.selectedItems,
        subtotal: this.calculateItemSubtotal(dto.quantity, product.price),
      }
      cart.items.push(newItem)
    }

    // Recalcular total
    cart.total = this.calculateTotal(cart.items)
    cart.itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0)
    cart.updatedAt = new Date().toISOString()

    // Salvar no Redis
    const key = this.getCartKey(visitorId)
    await this.redis.setex(
      key,
      CART_TTL_HOURS * 3600,
      JSON.stringify(cart),
    )

    return cart
  }

  async updateItem(
    visitorId: string,
    productId: number,
    quantity: number,
  ): Promise<Cart> {
    const cart = await this.getCart(visitorId)

    if (quantity < 1) {
      throw new Error('Quantity must be at least 1')
    }

    if (quantity > MAX_CART_ITEM_QUANTITY) {
      throw new Error(`Maximum quantity per item is ${MAX_CART_ITEM_QUANTITY}`)
    }

    const itemIndex = cart.items.findIndex(
      (item) => item.productId === productId,
    )

    if (itemIndex === -1) {
      throw new Error('Item not found in cart')
    }

    cart.items[itemIndex].quantity = quantity
    cart.items[itemIndex].subtotal = this.calculateItemSubtotal(
      quantity,
      cart.items[itemIndex].unitPrice,
    )

    // Recalcular total
    cart.total = this.calculateTotal(cart.items)
    cart.itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0)
    cart.updatedAt = new Date().toISOString()

    // Salvar no Redis
    const key = this.getCartKey(visitorId)
    await this.redis.setex(
      key,
      CART_TTL_HOURS * 3600,
      JSON.stringify(cart),
    )

    return cart
  }

  async removeItem(visitorId: string, productId: number): Promise<Cart> {
    const cart = await this.getCart(visitorId)

    cart.items = cart.items.filter((item) => item.productId !== productId)

    // Recalcular total
    cart.total = this.calculateTotal(cart.items)
    cart.itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0)
    cart.updatedAt = new Date().toISOString()

    // Salvar no Redis
    const key = this.getCartKey(visitorId)
    await this.redis.setex(
      key,
      CART_TTL_HOURS * 3600,
      JSON.stringify(cart),
    )

    return cart
  }

  async clearCart(visitorId: string): Promise<void> {
    const key = this.getCartKey(visitorId)
    await this.redis.del(key)
  }
}



