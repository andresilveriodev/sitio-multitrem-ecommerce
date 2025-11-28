import { DataSource } from 'typeorm'
import { Product } from '../../products/entities/product.entity'

export async function seedProducts(dataSource: DataSource): Promise<void> {
  const productRepository = dataSource.getRepository(Product)

  const count = await productRepository.count()
  if (count > 0) {
    console.log('Database already has products, skipping seed')
    return
  }

  const products: Partial<Product>[] = [
    // HORTALIÇAS (R$ 5,00 cada)
    {
      name: 'Alface Americana',
      slug: 'alface-americana',
      description: 'Alface fresca e crocante',
      price: 5.0,
      category: 'hortalica',
      active: true,
    },
    {
      name: 'Alface Crespa',
      slug: 'alface-crespa',
      description: 'Alface crespa e saborosa',
      price: 5.0,
      category: 'hortalica',
      active: true,
    },
    {
      name: 'Coentro',
      slug: 'coentro',
      description: 'Coentro fresco',
      price: 5.0,
      category: 'hortalica',
      active: true,
    },
    {
      name: 'Cebolinha',
      slug: 'cebolinha',
      description: 'Cebolinha verde',
      price: 5.0,
      category: 'hortalica',
      active: true,
    },
    {
      name: 'Salsa',
      slug: 'salsa',
      description: 'Salsa fresca',
      price: 5.0,
      category: 'hortalica',
      active: true,
    },
    {
      name: 'Rúcula',
      slug: 'rucula',
      description: 'Rúcula fresca',
      price: 5.0,
      category: 'hortalica',
      active: true,
    },
    // OVOS CAIPIRAS
    {
      name: '12 Ovos Caipiras',
      slug: '12-ovos-caipiras',
      description: 'Dúzia de ovos caipiras frescos',
      price: 15.0,
      category: 'ovos',
      active: true,
    },
    {
      name: '20 Ovos Caipiras',
      slug: '20-ovos-caipiras',
      description: 'Vinte ovos caipiras frescos',
      price: 24.0,
      category: 'ovos',
      active: true,
    },
    {
      name: '30 Ovos Caipiras',
      slug: '30-ovos-caipiras',
      description: 'Trinta ovos caipiras frescos',
      price: 35.0,
      category: 'ovos',
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
      active: true,
    },
    {
      name: 'Kit 2 Pessoas',
      slug: 'kit-2-pessoas',
      description: 'Kit com 5 hortaliças à escolha',
      price: 20.0,
      category: 'kit',
      kitSize: 5,
      active: true,
    },
    {
      name: 'Kit 3 Pessoas',
      slug: 'kit-3-pessoas',
      description: 'Kit com 7 hortaliças à escolha',
      price: 28.0,
      category: 'kit',
      kitSize: 7,
      active: true,
    },
    {
      name: 'Kit 4 Pessoas',
      slug: 'kit-4-pessoas',
      description: 'Kit com 9 hortaliças à escolha',
      price: 35.0,
      category: 'kit',
      kitSize: 9,
      active: true,
    },
    {
      name: 'Kit 5 Pessoas',
      slug: 'kit-5-pessoas',
      description: 'Kit com 12 hortaliças à escolha',
      price: 45.0,
      category: 'kit',
      kitSize: 12,
      active: true,
    },
    // COMBOS
    {
      name: 'Combo Família 2',
      slug: 'combo-familia-2',
      description: '5 hortaliças + 20 ovos caipiras',
      price: 49.5,
      category: 'combo',
      active: true,
    },
  ]

  await productRepository.save(products)
  console.log(`✅ Seeded ${products.length} products`)
}



