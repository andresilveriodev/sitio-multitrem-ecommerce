export type MessageRole = 'user' | 'assistant' | 'system'

export type AIIntent =
  | 'greeting'
  | 'list_products'
  | 'add_to_cart'
  | 'remove_from_cart'
  | 'view_cart'
  | 'checkout'
  | 'schedule_delivery'
  | 'payment'
  | 'other'

export interface AIMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: string
  intent?: AIIntent
  extractedProducts?: Array<{
    productId: number
    quantity: number
    selectedItems?: string[]
  }>
}

export interface AIConversation {
  id: string
  visitorId: string
  channel: 'web' | 'whatsapp'
  messages: AIMessage[]
  createdAt: string
}

