export type DeliveryPeriod = 'manha'

export type DeliveryDay = 'quarta' | 'quinta' | 'sexta' | 'sabado'

export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'preparing'
  | 'delivering'
  | 'delivered'
  | 'cancelled'

export type PaymentStatus =
  | 'pending'
  | 'processing'
  | 'paid'
  | 'failed'
  | 'refunded'

export interface DeliverySlot {
  id: string
  date: string
  dayOfWeek: number
  period: DeliveryPeriod
  availableSlots: number
  maxSlots: number
}

export interface OrderItem {
  productId: number
  productName: string
  quantity: number
  unitPrice: number
  selectedItems?: string[]
  subtotal: number
}

export interface Order {
  id: string
  visitorId: string
  customerId?: number
  items: OrderItem[]
  total: number
  status: OrderStatus
  deliveryDate: string
  deliveryPeriod: DeliveryPeriod
  paymentMethod: string
  paymentStatus: PaymentStatus
  customerName: string
  customerPhone: string
  customerAddress: string
  createdAt: string
}

