import { ProductCategory, OrderStatus, PaymentStatus, PaymentMethod, DeliveryDay, DeliveryPeriod } from '../types'

export const PRODUCT_CATEGORIES: ProductCategory[] = [
  'hortalica',
  'ovos',
  'kit',
  'combo',
]

export const ORDER_STATUS: OrderStatus[] = [
  'pending',
  'confirmed',
  'preparing',
  'delivering',
  'delivered',
  'cancelled',
]

export const PAYMENT_STATUS: PaymentStatus[] = [
  'pending',
  'processing',
  'paid',
  'failed',
  'refunded',
]

export const PAYMENT_METHODS: PaymentMethod[] = [
  'pix',
  'boleto',
  'cartao',
]

export const DELIVERY_DAYS: DeliveryDay[] = [
  'quarta',
  'quinta',
  'sexta',
  'sabado',
]

export const DELIVERY_PERIODS: DeliveryPeriod[] = [
  'manha',
]

export const DELIVERY_DAY_MAP: Record<DeliveryDay, number> = {
  quarta: 3,
  quinta: 4,
  sexta: 5,
  sabado: 6,
}

export const MAX_CART_ITEM_QUANTITY = 10
export const CART_TTL_HOURS = 24

