import { Injectable, NotFoundException } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { Product } from './entities/product.entity'
import { CreateProductDto, UpdateProductDto } from './dto'

@Injectable()
export class ProductsService {
  constructor(
    @InjectRepository(Product)
    private readonly productRepository: Repository<Product>,
  ) {}

  async findAll(category?: string, active?: boolean): Promise<Product[]> {
    const queryBuilder = this.productRepository.createQueryBuilder('product')

    if (category) {
      queryBuilder.where('product.category = :category', { category })
    }

    if (active !== undefined) {
      queryBuilder.andWhere('product.active = :active', { active })
    } else {
      // Por padrão, retorna apenas ativos
      queryBuilder.andWhere('product.active = :active', { active: true })
    }

    return queryBuilder.getMany()
  }

  async findById(id: number): Promise<Product> {
    const product = await this.productRepository.findOne({ where: { id } })
    if (!product) {
      throw new NotFoundException(`Product with ID ${id} not found`)
    }
    return product
  }

  async findBySlug(slug: string): Promise<Product> {
    const product = await this.productRepository.findOne({ where: { slug } })
    if (!product) {
      throw new NotFoundException(`Product with slug "${slug}" not found`)
    }
    return product
  }

  async create(dto: CreateProductDto): Promise<Product> {
    // Verificar se slug já existe
    const existingProduct = await this.productRepository.findOne({
      where: { slug: dto.slug },
    })
    if (existingProduct) {
      throw new Error(`Product with slug "${dto.slug}" already exists`)
    }

    const product = this.productRepository.create({
      ...dto,
      active: dto.active ?? true,
    })
    return this.productRepository.save(product)
  }

  async update(id: number, dto: UpdateProductDto): Promise<Product> {
    const product = await this.findById(id)

    // Se está atualizando o slug, verificar se não existe outro produto com o mesmo slug
    if (dto.slug && dto.slug !== product.slug) {
      const existingProduct = await this.productRepository.findOne({
        where: { slug: dto.slug },
      })
      if (existingProduct) {
        throw new Error(`Product with slug "${dto.slug}" already exists`)
      }
    }

    await this.productRepository.update(id, dto)
    return this.findById(id)
  }

  async remove(id: number): Promise<void> {
    await this.findById(id) // Verifica se existe
    await this.productRepository.update(id, { active: false })
  }

  async seed(): Promise<void> {
    const count = await this.productRepository.count()
    if (count > 0) {
      console.log('Database already has products, skipping seed')
      return
    }

    // Helper function para gerar URL da imagem baseada no slug
    const getImageUrl = (slug: string): string | undefined => {
      // Tenta encontrar a imagem com diferentes extensões
      const extensions = ['.jpg', '.jpeg', '.png', '.webp']
      // Retorna a URL relativa - o Next.js servirá da pasta public
      return `/images/products/${slug}.jpg` // Padrão: JPG, pode ser ajustado
    }

    const products: Partial<Product>[] = [
      // HORTALIÇAS (R$ 5,00 cada)
      {
        name: 'Alface Americana',
        slug: 'alface-americana',
        description: 'Alface fresca e crocante',
        price: 5.0,
        category: 'hortalica',
        imageUrl: getImageUrl('alface-americana'),
        active: true,
      },
      {
        name: 'Alface Crespa',
        slug: 'alface-crespa',
        description: 'Alface crespa e saborosa',
        price: 5.0,
        category: 'hortalica',
        imageUrl: getImageUrl('alface-crespa'),
        active: true,
      },
      {
        name: 'Coentro',
        slug: 'coentro',
        description: 'Coentro fresco',
        price: 5.0,
        category: 'hortalica',
        imageUrl: getImageUrl('coentro'),
        active: true,
      },
      {
        name: 'Cebolinha',
        slug: 'cebolinha',
        description: 'Cebolinha verde',
        price: 5.0,
        category: 'hortalica',
        imageUrl: getImageUrl('cebolinha'),
        active: true,
      },
      {
        name: 'Salsa',
        slug: 'salsa',
        description: 'Salsa fresca',
        price: 5.0,
        category: 'hortalica',
        imageUrl: getImageUrl('salsa'),
        active: true,
      },
      {
        name: 'Rúcula',
        slug: 'rucula',
        description: 'Rúcula fresca',
        price: 5.0,
        category: 'hortalica',
        imageUrl: getImageUrl('rucula'),
        active: true,
      },
      // OVOS CAIPIRAS
      {
        name: '12 Ovos Caipiras',
        slug: '12-ovos-caipiras',
        description: 'Dúzia de ovos caipiras frescos',
        price: 15.0,
        category: 'ovos',
        imageUrl: getImageUrl('12-ovos-caipiras'),
        active: true,
      },
      {
        name: '20 Ovos Caipiras',
        slug: '20-ovos-caipiras',
        description: 'Vinte ovos caipiras frescos',
        price: 24.0,
        category: 'ovos',
        imageUrl: getImageUrl('20-ovos-caipiras'),
        active: true,
      },
      {
        name: '30 Ovos Caipiras',
        slug: '30-ovos-caipiras',
        description: 'Trinta ovos caipiras frescos',
        price: 35.0,
        category: 'ovos',
        imageUrl: getImageUrl('30-ovos-caipiras'),
        active: true,
      },
      // KITS
      {
        name: 'Kit 1 Pessoa',
        slug: 'kit-1-pessoa',
        description: 'Kit com 3 hortaliças à escolha',
        price: 12.0,
        category: 'kit',
        kitSize: 3,
        imageUrl: getImageUrl('kit-1-pessoa'),
        active: true,
      },
      {
        name: 'Kit 2 Pessoas',
        slug: 'kit-2-pessoas',
        description: 'Kit com 5 hortaliças à escolha',
        price: 20.0,
        category: 'kit',
        kitSize: 5,
        imageUrl: getImageUrl('kit-2-pessoas'),
        active: true,
      },
      {
        name: 'Kit 3 Pessoas',
        slug: 'kit-3-pessoas',
        description: 'Kit com 7 hortaliças à escolha',
        price: 28.0,
        category: 'kit',
        kitSize: 7,
        imageUrl: getImageUrl('kit-3-pessoas'),
        active: true,
      },
      {
        name: 'Kit 4 Pessoas',
        slug: 'kit-4-pessoas',
        description: 'Kit com 9 hortaliças à escolha',
        price: 35.0,
        category: 'kit',
        kitSize: 9,
        imageUrl: getImageUrl('kit-4-pessoas'),
        active: true,
      },
      {
        name: 'Kit 5 Pessoas',
        slug: 'kit-5-pessoas',
        description: 'Kit com 12 hortaliças à escolha',
        price: 45.0,
        category: 'kit',
        kitSize: 12,
        imageUrl: getImageUrl('kit-5-pessoas'),
        active: true,
      },
      // COMBOS
      {
        name: 'Combo Família 2',
        slug: 'combo-familia-2',
        description: '5 hortaliças + 20 ovos caipiras',
        price: 49.5,
        category: 'combo',
        imageUrl: getImageUrl('combo-familia-2'),
        active: true,
      },
    ]

    await this.productRepository.save(products)
    console.log(`✅ Seeded ${products.length} products`)
  }
}

