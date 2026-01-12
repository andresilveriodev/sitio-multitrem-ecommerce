import type { Product, KitProduct, ProductCategory } from '@/types'

// Helper function para gerar URL da imagem baseada no slug
const getImageUrl = (slug: string): string => {
  return `/images/products/${slug}.jpg`
}

export const AVAILABLE_VEGETABLES = [
  'Alface Americana',
  'Alface Crespa',
  'Coentro',
  'Cebolinha',
  'Salsa',
  'Rúcula',
]

export const PRODUCTS: (Product | KitProduct)[] = [
  // HORTALIÇAS
  {
    id: 1,
    name: 'Alface Americana',
    slug: 'alface-americana',
    price: 5.0,
    category: 'hortalica',
    imageUrl: getImageUrl('alface-americana'),
    active: true,
  },
  {
    id: 2,
    name: 'Alface Crespa',
    slug: 'alface-crespa',
    price: 5.0,
    category: 'hortalica',
    imageUrl: getImageUrl('alface-crespa'),
    active: true,
  },
  {
    id: 3,
    name: 'Coentro',
    slug: 'coentro',
    price: 5.0,
    category: 'hortalica',
    imageUrl: getImageUrl('coentro'),
    active: true,
  },
  {
    id: 4,
    name: 'Cebolinha',
    slug: 'cebolinha',
    price: 5.0,
    category: 'hortalica',
    imageUrl: getImageUrl('cebolinha'),
    active: true,
  },
  {
    id: 5,
    name: 'Salsa',
    slug: 'salsa',
    price: 5.0,
    category: 'hortalica',
    imageUrl: getImageUrl('salsa'),
    active: true,
  },
  {
    id: 6,
    name: 'Rúcula',
    slug: 'rucula',
    price: 5.0,
    category: 'hortalica',
    imageUrl: getImageUrl('rucula'),
    active: true,
  },
  // OVOS
  {
    id: 7,
    name: '12 Ovos Caipiras',
    slug: '12-ovos-caipiras',
    price: 15.0,
    category: 'ovos',
    imageUrl: getImageUrl('12-ovos-caipiras'),
    active: true,
  },
  {
    id: 8,
    name: '20 Ovos Caipiras',
    slug: '20-ovos-caipiras',
    price: 24.0,
    category: 'ovos',
    imageUrl: getImageUrl('20-ovos-caipiras'),
    active: true,
  },
  {
    id: 9,
    name: '30 Ovos Caipiras',
    slug: '30-ovos-caipiras',
    price: 35.0,
    category: 'ovos',
    imageUrl: getImageUrl('30-ovos-caipiras'),
    active: true,
  },
  // KITS
  {
    id: 10,
    name: 'Kit 1 Pessoa',
    slug: 'kit-1-pessoa',
    description: '3 hortaliças à escolha',
    price: 12.0,
    category: 'kit',
    kitSize: 3,
    availableItems: AVAILABLE_VEGETABLES,
    imageUrl: getImageUrl('kit-1-pessoa'),
    active: true,
  } as KitProduct,
  {
    id: 11,
    name: 'Kit 2 Pessoas',
    slug: 'kit-2-pessoas',
    description: '5 hortaliças à escolha',
    price: 20.0,
    category: 'kit',
    kitSize: 5,
    availableItems: AVAILABLE_VEGETABLES,
    imageUrl: getImageUrl('kit-2-pessoas'),
    active: true,
  } as KitProduct,
  {
    id: 12,
    name: 'Kit 3 Pessoas',
    slug: 'kit-3-pessoas',
    description: '7 hortaliças à escolha',
    price: 28.0,
    category: 'kit',
    kitSize: 7,
    availableItems: AVAILABLE_VEGETABLES,
    imageUrl: getImageUrl('kit-3-pessoas'),
    active: true,
  } as KitProduct,
  {
    id: 13,
    name: 'Kit 4 Pessoas',
    slug: 'kit-4-pessoas',
    description: '9 hortaliças à escolha',
    price: 35.0,
    category: 'kit',
    kitSize: 9,
    availableItems: AVAILABLE_VEGETABLES,
    imageUrl: getImageUrl('kit-4-pessoas'),
    active: true,
  } as KitProduct,
  {
    id: 14,
    name: 'Kit 5 Pessoas',
    slug: 'kit-5-pessoas',
    description: '12 hortaliças à escolha',
    price: 45.0,
    category: 'kit',
    kitSize: 12,
    availableItems: AVAILABLE_VEGETABLES,
    imageUrl: getImageUrl('kit-5-pessoas'),
    active: true,
  } as KitProduct,
  // COMBOS
  {
    id: 15,
    name: 'Combo Família 2',
    slug: 'combo-familia-2',
    description: '5 hortaliças + 20 ovos caipiras',
    price: 49.5,
    category: 'combo',
    imageUrl: getImageUrl('combo-familia-2'),
    active: true,
  },
]

// Funções auxiliares
export function getProductsByCategory(
  category?: ProductCategory
): (Product | KitProduct)[] {
  if (!category) return PRODUCTS.filter((p) => p.active)
  return PRODUCTS.filter((p) => p.category === category && p.active)
}

export function getProductById(id: number): Product | KitProduct | undefined {
  return PRODUCTS.find((p) => p.id === id && p.active)
}

export function getKitProducts(): KitProduct[] {
  return PRODUCTS.filter(
    (p) => p.category === 'kit' && p.active
  ) as KitProduct[]
}

export function getAvailableDeliveryDays(): Date[] {
  const days: Date[] = []
  const today = new Date()
  let count = 0
  let currentDate = new Date(today)

  while (count < 14) {
    currentDate.setDate(currentDate.getDate() + 1)
    const dayOfWeek = currentDate.getDay()

    // 3 = quarta, 4 = quinta, 5 = sexta, 6 = sábado
    if (dayOfWeek >= 3 && dayOfWeek <= 6) {
      days.push(new Date(currentDate))
      count++
    }
  }

  return days
}

