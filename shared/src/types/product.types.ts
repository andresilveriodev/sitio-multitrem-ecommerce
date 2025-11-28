export type ProductCategory = 'hortalica' | 'ovos' | 'kit' | 'combo'

export interface Product {
  id: number
  name: string
  slug: string
  description?: string
  price: number
  category: ProductCategory
  imageUrl?: string
  active: boolean
  maxQuantity?: number
  kitSize?: number
}

export interface KitProduct extends Product {
  kitSize: number
  availableItems: string[]
}

