import { Test, TestingModule } from '@nestjs/testing'
import { getRepositoryToken } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { ProductsService } from './products.service'
import { Product } from './entities/product.entity'
import { NotFoundException } from '@nestjs/common'

describe('ProductsService', () => {
  let service: ProductsService
  let repository: Repository<Product>

  const mockProduct: Product = {
    id: 1,
    name: 'Alface Americana',
    slug: 'alface-americana',
    description: 'Alface fresca',
    price: 5.0,
    category: 'hortalica',
    active: true,
    createdAt: new Date(),
    updatedAt: new Date(),
  } as Product

  const mockRepository = {
    createQueryBuilder: jest.fn(() => ({
      where: jest.fn().mockReturnThis(),
      andWhere: jest.fn().mockReturnThis(),
      getMany: jest.fn().mockResolvedValue([mockProduct]),
    })),
    findOne: jest.fn(),
    create: jest.fn(),
    save: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
  }

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        ProductsService,
        {
          provide: getRepositoryToken(Product),
          useValue: mockRepository,
        },
      ],
    }).compile()

    service = module.get<ProductsService>(ProductsService)
    repository = module.get<Repository<Product>>(getRepositoryToken(Product))
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('findAll', () => {
    it('deve listar todos os produtos', async () => {
      const result = await service.findAll()

      expect(result).toEqual([mockProduct])
      expect(mockRepository.createQueryBuilder).toHaveBeenCalled()
    })

    it('deve filtrar produtos por categoria', async () => {
      const queryBuilder = {
        where: jest.fn().mockReturnThis(),
        andWhere: jest.fn().mockReturnThis(),
        getMany: jest.fn().mockResolvedValue([mockProduct]),
      }

      mockRepository.createQueryBuilder.mockReturnValue(queryBuilder)

      const result = await service.findAll('hortalicas')

      expect(result).toEqual([mockProduct])
      expect(queryBuilder.where).toHaveBeenCalledWith(
        'product.category = :category',
        { category: 'hortalicas' },
      )
    })

    it('deve retornar apenas produtos ativos por padrão', async () => {
      const queryBuilder = {
        where: jest.fn().mockReturnThis(),
        andWhere: jest.fn().mockReturnThis(),
        getMany: jest.fn().mockResolvedValue([mockProduct]),
      }

      mockRepository.createQueryBuilder.mockReturnValue(queryBuilder)

      await service.findAll()

      expect(queryBuilder.andWhere).toHaveBeenCalledWith(
        'product.active = :active',
        { active: true },
      )
    })
  })

  describe('findById', () => {
    it('deve buscar produto por ID', async () => {
      mockRepository.findOne.mockResolvedValue(mockProduct)

      const result = await service.findById(1)

      expect(result).toEqual(mockProduct)
      expect(mockRepository.findOne).toHaveBeenCalledWith({
        where: { id: 1 },
      })
    })

    it('deve lançar NotFoundException se produto não existir', async () => {
      mockRepository.findOne.mockResolvedValue(null)

      await expect(service.findById(999)).rejects.toThrow(NotFoundException)
    })
  })

  describe('findBySlug', () => {
    it('deve buscar produto por slug', async () => {
      mockRepository.findOne.mockResolvedValue(mockProduct)

      const result = await service.findBySlug('alface-americana')

      expect(result).toEqual(mockProduct)
      expect(mockRepository.findOne).toHaveBeenCalledWith({
        where: { slug: 'alface-americana' },
      })
    })

    it('deve lançar NotFoundException se produto não existir', async () => {
      mockRepository.findOne.mockResolvedValue(null)

      await expect(service.findBySlug('produto-inexistente')).rejects.toThrow(
        NotFoundException,
      )
    })
  })
})




