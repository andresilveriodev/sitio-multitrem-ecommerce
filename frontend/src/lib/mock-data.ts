import type { Product, KitProduct, ProductCategory } from '@/types'

const PLACEHOLDER_IMAGE = 'https://placehold.co/400x400/22c55e/white?text=Produto'

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
    imageUrl: PLACEHOLDER_IMAGE,
    active: true,
  },
  {
    id: 2,
    name: 'Alface Crespa',
    slug: 'alface-crespa',
    price: 5.0,
    category: 'hortalica',
    imageUrl: PLACEHOLDER_IMAGE,
    active: true,
  },
  {
    id: 3,
    name: 'Coentro',
    slug: 'coentro',
    price: 5.0,
    category: 'hortalica',
    imageUrl: PLACEHOLDER_IMAGE,
    active: true,
  },
  {
    id: 4,
    name: 'Cebolinha',
    slug: 'cebolinha',
    price: 5.0,
    category: 'hortalica',
    imageUrl: PLACEHOLDER_IMAGE,
    active: true,
  },
  {
    id: 5,
    name: 'Salsa',
    slug: 'salsa',
    price: 5.0,
    category: 'hortalica',
    imageUrl: PLACEHOLDER_IMAGE,
    active: true,
  },
  {
    id: 6,
    name: 'Rúcula',
    slug: 'rucula',
    price: 5.0,
    category: 'hortalica',
    imageUrl: PLACEHOLDER_IMAGE,
    active: true,
  },
  // OVOS
  {
    id: 7,
    name: 'Ovos Caipiras - 12 unidades',
    slug: 'ovos-caipiras-12',
    price: 15.0,
    category: 'ovos',
    imageUrl: PLACEHOLDER_IMAGE,
    active: true,
  },
  {
    id: 8,
    name: 'Ovos Caipiras - 20 unidades',
    slug: 'ovos-caipiras-20',
    price: 24.0,
    category: 'ovos',
    imageUrl: PLACEHOLDER_IMAGE,
    active: true,
  },
  {
    id: 9,
    name: 'Ovos Caipiras - 30 unidades',
    slug: 'ovos-caipiras-30',
    price: 35.0,
    category: 'ovos',
    imageUrl: PLACEHOLDER_IMAGE,
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
    imageUrl: PLACEHOLDER_IMAGE,
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
    imageUrl: PLACEHOLDER_IMAGE,
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
    imageUrl: PLACEHOLDER_IMAGE,
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
    imageUrl: PLACEHOLDER_IMAGE,
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
    imageUrl: PLACEHOLDER_IMAGE,
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
    imageUrl: PLACEHOLDER_IMAGE,
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

