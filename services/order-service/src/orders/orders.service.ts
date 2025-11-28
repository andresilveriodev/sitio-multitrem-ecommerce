import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { ConfigService } from '@nestjs/config'
import axios from 'axios'
import { Order } from './entities/order.entity'
import { OrderItem } from './entities/order-item.entity'
import { DeliverySlot } from '../delivery/entities/delivery-slot.entity'
import {
  CreateOrderDto,
  OrderStatus,
  PaymentStatus,
  Cart,
} from '@sitio/shared'

@Injectable()
export class OrdersService {
  private readonly cartServiceUrl: string

  constructor(
    @InjectRepository(Order)
    private readonly orderRepository: Repository<Order>,
    @InjectRepository(OrderItem)
    private readonly orderItemRepository: Repository<OrderItem>,
    @InjectRepository(DeliverySlot)
    private readonly deliverySlotRepository: Repository<DeliverySlot>,
    private readonly configService: ConfigService,
  ) {
    this.cartServiceUrl = configService.get<string>(
      'CART_SERVICE_URL',
      'http://localhost:3002',
    )
  }

  private async fetchCart(visitorId: string): Promise<Cart> {
    try {
      const response = await axios.get(
        `${this.cartServiceUrl}/cart/${visitorId}`,
      )
      return response.data
    } catch (error) {
      throw new BadRequestException('Cart not found')
    }
  }

  private async clearCart(visitorId: string): Promise<void> {
    try {
      await axios.delete(`${this.cartServiceUrl}/cart/${visitorId}`)
    } catch (error) {
      // Log error but don't fail order creation
      console.error('Failed to clear cart:', error)
    }
  }

  async create(dto: CreateOrderDto): Promise<Order> {
    // 1. Buscar carrinho
    const cart = await this.fetchCart(dto.visitorId)

    if (!cart.items || cart.items.length === 0) {
      throw new BadRequestException('Cart is empty')
    }

    // 2. Verificar disponibilidade do slot
    const slot = await this.deliverySlotRepository.findOne({
      where: {
        date: dto.deliveryDate,
        period: dto.deliveryPeriod,
        active: true,
      },
    })

    if (!slot) {
      throw new BadRequestException('Delivery slot not available')
    }

    if (slot.currentOrders >= slot.maxOrders) {
      throw new BadRequestException('Delivery slot is full')
    }

    // 3. Criar order
    const addressStr = `${dto.address.street}, ${dto.address.number}${dto.address.complement ? ` - ${dto.address.complement}` : ''}, ${dto.address.neighborhood}`
    
    const order = this.orderRepository.create({
      visitorId: dto.visitorId,
      customerId: dto.customerId || null,
      status: 'pending' as OrderStatus,
      total: cart.total,
      deliveryDate: dto.deliveryDate,
      deliveryPeriod: dto.deliveryPeriod,
      paymentMethod: dto.paymentMethod,
      paymentStatus: 'pending' as PaymentStatus,
      customerName: dto.customerName,
      customerPhone: dto.customerPhone,
      customerAddress: addressStr,
      customerCep: dto.address.zipCode || null,
      customerCity: dto.address.city || null,
      customerState: dto.address.state || null,
    })

    const savedOrder = await this.orderRepository.save(order)

    // 4. Criar order items
    const orderItems = cart.items.map((item) =>
      this.orderItemRepository.create({
        orderId: savedOrder.id,
        productId: item.productId,
        productName: item.productName,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
        selectedItems: item.selectedItems || null,
        subtotal: item.subtotal,
      }),
    )

    await this.orderItemRepository.save(orderItems)

    // 5. Incrementar currentOrders do slot
    slot.currentOrders += 1
    await this.deliverySlotRepository.save(slot)

    // 6. Limpar carrinho
    await this.clearCart(dto.visitorId)

    // 7. Retornar order com items
    return this.findOne(savedOrder.id)
  }

  async findOne(id: number): Promise<Order> {
    const order = await this.orderRepository.findOne({
      where: { id },
      relations: ['items'],
    })

    if (!order) {
      throw new NotFoundException(`Order ${id} not found`)
    }

    return order
  }

  async findByVisitor(visitorId: string): Promise<Order[]> {
    return this.orderRepository.find({
      where: { visitorId },
      relations: ['items'],
      order: { createdAt: 'DESC' },
    })
  }

  async updateStatus(
    id: number,
    status: OrderStatus,
  ): Promise<Order> {
    const order = await this.findOne(id)
    order.status = status
    return this.orderRepository.save(order)
  }

  async updatePaymentStatus(
    id: number,
    paymentStatus: PaymentStatus,
  ): Promise<Order> {
    const order = await this.findOne(id)
    order.paymentStatus = paymentStatus
    return this.orderRepository.save(order)
  }
}

