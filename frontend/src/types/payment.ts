export type PaymentMethod = 'pix' | 'boleto' | 'cartao'

export interface PixPayment {
  qrCode: string
  qrCodeBase64: string
  expiresAt: string
}

export interface BoletoPayment {
  barcode: string
  boletoUrl: string
  expiresAt: string
}

export interface CardPayment {
  last4Digits?: string
  brand?: string
}

export interface Payment {
  id: string
  orderId: string
  method: PaymentMethod
  status: string
  amount: number
  mercadoPagoId?: string
  pixData?: PixPayment
  boletoData?: BoletoPayment
  cardData?: CardPayment
  createdAt: string
}

