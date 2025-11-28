import { Test, TestingModule } from '@nestjs/testing'
import { ConfigService } from '@nestjs/config'
import Redis from 'ioredis'
import axios from 'axios'
import { CartService } from './cart.service'
import { AddToCartDto } from './dto'

jest.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('CartService', () => {
  let service: CartService
  let redis: jest.Mocked<Redis>

  const mockProduct = {
    id: 1,
    name: 'Alface Americana',
    price: 5.0,
    category: 'hortalicas',
  }

  const mockCart: any = {
    id: 'cart-123',
    visitorId: 'visitor123',
    items: [],
    total: 0,
    itemCount: 0,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }

  const mockRedis = {
    get: jest.fn(),
    setex: jest.fn(),
    del: jest.fn(),
  } as any

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        CartService,
        {
          provide: 'REDIS_CLIENT',
          useValue: mockRedis,
        },
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string, defaultValue?: any) => {
              if (key === 'PRODUCT_SERVICE_URL') {
                return 'http://localhost:3001'
              }
              return defaultValue
            }),
          },
        },
      ],
    }).compile()

    service = module.get<CartService>(CartService)
    redis = module.get('REDIS_CLIENT')
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('getCart', () => {
    it('deve criar carrinho vazio se não existir', async () => {
      mockRedis.get.mockResolvedValue(null)
      mockRedis.setex.mockResolvedValue('OK')

      const result = await service.getCart('visitor123')

      expect(result.visitorId).toBe('visitor123')
      expect(result.items).toEqual([])
      expect(result.total).toBe(0)
      expect(mockRedis.setex).toHaveBeenCalled()
    })

    it('deve retornar carrinho existente', async () => {
      mockRedis.get.mockResolvedValue(JSON.stringify(mockCart))

      const result = await service.getCart('visitor123')

      expect(result).toEqual(mockCart)
    })
  })

  describe('addItem', () => {
    it('deve adicionar item ao carrinho', async () => {
      mockRedis.get.mockResolvedValue(JSON.stringify(mockCart))
      mockRedis.setex.mockResolvedValue('OK')
      mockedAxios.get.mockResolvedValue({ data: mockProduct })

      const dto: AddToCartDto = {
        productId: 1,
        quantity: 2,
      }

      const result = await service.addItem('visitor123', dto)

      expect(result.items).toHaveLength(1)
      expect(result.items[0].productId).toBe(1)
      expect(result.items[0].quantity).toBe(2)
      expect(result.total).toBe(10.0) // 2 * 5.0
      expect(mockRedis.setex).toHaveBeenCalled()
    })

    it('deve calcular total corretamente', async () => {
      const cartWithItems = {
        ...mockCart,
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

      mockRedis.get.mockResolvedValue(JSON.stringify(cartWithItems))
      mockRedis.setex.mockResolvedValue('OK')
      mockedAxios.get.mockResolvedValue({ data: mockProduct })

      const dto: AddToCartDto = {
        productId: 1,
        quantity: 1,
      }

      const result = await service.addItem('visitor123', dto)

      expect(result.total).toBe(15.0) // 10.0 + 5.0
    })
  })

  describe('removeItem', () => {
    it('deve remover item do carrinho', async () => {
      const cartWithItems = {
        ...mockCart,
        items: [
          {
            productId: 1,
            quantity: 2,
            unitPrice: 5.0,
            subtotal: 10.0,
          },
        ],
        total: 10.0,
        itemCount: 2,
      }

      mockRedis.get.mockResolvedValue(JSON.stringify(cartWithItems))
      mockRedis.setex.mockResolvedValue('OK')

      const result = await service.removeItem('visitor123', 1)

      expect(result.items).toHaveLength(0)
      expect(result.total).toBe(0)
      expect(result.itemCount).toBe(0)
    })
  })
})

