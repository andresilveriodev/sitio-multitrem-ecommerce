import { Test, TestingModule } from '@nestjs/testing'
import { getRepositoryToken } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { ConfigService } from '@nestjs/config'
import axios from 'axios'
import { OrdersService } from './orders.service'
import { Order } from './entities/order.entity'
import { OrderItem } from './entities/order-item.entity'
import { DeliverySlot } from '../delivery/entities/delivery-slot.entity'
import { CreateOrderDto } from './dto'
import { BadRequestException } from '@nestjs/common'

jest.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('OrdersService', () => {
  let service: OrdersService
  let orderRepository: Repository<Order>
  let orderItemRepository: Repository<OrderItem>

  const mockCart = {
    id: 'cart-123',
    visitorId: 'visitor123',
    items: [
      {
        productId: 1,
        quantity: 2,
        unitPrice: 5.0,
        subtotal: 10.0,
      },
    ],
    total: 10.0,
  }

  const mockOrder: Order = {
    id: 1,
    visitorId: 'visitor123',
    status: 'pending',
    total: 10.0,
    deliveryDate: new Date('2024-12-04'),
    items: [],
    createdAt: new Date(),
    updatedAt: new Date(),
  } as Order

  const mockOrderRepository = {
    create: jest.fn(),
    save: jest.fn(),
    findOne: jest.fn(),
    find: jest.fn(),
    update: jest.fn(),
  }

  const mockOrderItemRepository = {
    create: jest.fn(),
    save: jest.fn(),
  }

  const mockDeliverySlotRepository = {
    findOne: jest.fn(),
    save: jest.fn(),
  }

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        OrdersService,
        {
          provide: getRepositoryToken(Order),
          useValue: mockOrderRepository,
        },
        {
          provide: getRepositoryToken(OrderItem),
          useValue: mockOrderItemRepository,
        },
        {
          provide: getRepositoryToken(DeliverySlot),
          useValue: mockDeliverySlotRepository,
        },
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string, defaultValue?: any) => {
              if (key === 'CART_SERVICE_URL') {
                return 'http://localhost:3002'
              }
              return defaultValue
            }),
          },
        },
      ],
    }).compile()

    service = module.get<OrdersService>(OrdersService)
    orderRepository = module.get<Repository<Order>>(getRepositoryToken(Order))
    orderItemRepository = module.get<Repository<OrderItem>>(
      getRepositoryToken(OrderItem),
    )
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('create', () => {
    it('deve criar pedido a partir do carrinho', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockCart })
      mockDeliverySlotRepository.findOne.mockResolvedValue({
        id: 1,
        date: '2024-12-04',
        period: 'morning',
        maxOrders: 10,
        currentOrders: 5,
        active: true,
      })
      mockOrderRepository.create.mockReturnValue(mockOrder)
      mockOrderRepository.save.mockResolvedValue(mockOrder)
      mockOrderItemRepository.create.mockReturnValue({} as OrderItem)
      mockOrderItemRepository.save.mockResolvedValue({} as OrderItem)
      mockDeliverySlotRepository.save.mockResolvedValue({})

      const dto: CreateOrderDto = {
        visitorId: 'visitor123',
        items: mockCart.items,
        deliveryDate: '2024-12-04',
        deliveryPeriod: 'morning',
        paymentMethod: 'pix',
        customerName: 'João Silva',
        customerPhone: '62999999999',
        address: {
          street: 'Rua Teste',
          number: '123',
          complement: '',
          neighborhood: 'Centro',
          city: 'Terezópolis de Goiás',
          state: 'GO',
          zipCode: '75175000',
        },
      }

      const result = await service.create(dto)

      expect(result).toBeDefined()
      expect(mockOrderRepository.create).toHaveBeenCalled()
      expect(mockOrderRepository.save).toHaveBeenCalled()
    })

    it('deve validar data de entrega (apenas quarta a sábado)', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockCart })

      const dto: CreateOrderDto = {
        visitorId: 'visitor123',
        items: mockCart.items,
        deliveryDate: '2024-12-01', // Domingo
        deliveryPeriod: 'morning',
        paymentMethod: 'pix',
        customerName: 'João Silva',
        customerPhone: '62999999999',
        address: {
          street: 'Rua Teste',
          number: '123',
          complement: '',
          neighborhood: 'Centro',
          city: 'Terezópolis de Goiás',
          state: 'GO',
          zipCode: '75175000',
        },
      }

      await expect(service.create(dto)).rejects.toThrow(BadRequestException)
    })

    it('deve aceitar quarta-feira como data válida', async () => {
      mockedAxios.get.mockResolvedValue({ data: mockCart })
      mockDeliverySlotRepository.findOne.mockResolvedValue({
        id: 1,
        date: '2024-12-04',
        period: 'morning',
        maxOrders: 10,
        currentOrders: 5,
        active: true,
      })
      mockOrderRepository.create.mockReturnValue(mockOrder)
      mockOrderRepository.save.mockResolvedValue(mockOrder)
      mockOrderItemRepository.create.mockReturnValue({} as OrderItem)
      mockOrderItemRepository.save.mockResolvedValue({} as OrderItem)
      mockDeliverySlotRepository.save.mockResolvedValue({})

      const dto: CreateOrderDto = {
        visitorId: 'visitor123',
        items: mockCart.items,
        deliveryDate: '2024-12-04', // Quarta-feira
        deliveryPeriod: 'morning',
        paymentMethod: 'pix',
        customerName: 'João Silva',
        customerPhone: '62999999999',
        address: {
          street: 'Rua Teste',
          number: '123',
          complement: '',
          neighborhood: 'Centro',
          city: 'Terezópolis de Goiás',
          state: 'GO',
          zipCode: '75175000',
        },
      }

      const result = await service.create(dto)

      expect(result).toBeDefined()
    })
  })
})

