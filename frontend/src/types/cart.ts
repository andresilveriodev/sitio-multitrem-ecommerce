export interface CartItem {
  productId: number
  visitorId: string
  productName: string
  quantity: number
  unitPrice: number
  selectedItems?: string[]
  subtotal: number
  imageUrl?: string
}

export interface Cart {
  id: string
  visitorId: string
  items: CartItem[]
  total: number
  itemCount: number
  createdAt: string
  updatedAt: string
}

