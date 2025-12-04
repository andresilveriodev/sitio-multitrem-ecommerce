const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export interface ChatMessage {
  visitorId: string
  message: string
  conversationHistory?: Array<{
    role: 'user' | 'assistant' | 'system'
    content: string
    timestamp?: string
  }>
  source?: string
}

export interface ChatResponse {
  response: string
  actions: Array<{
    function: string
    params: any
    result: any
  }>
  cart?: {
    items: Array<{
      productId: number
      quantity: number
      product: any
    }>
    total: number
  }
  paymentLink?: string
}

export const aiService = {
  async sendMessage(data: ChatMessage): Promise<ChatResponse> {
    const response = await fetch(`${API_URL}/ai/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error('Erro ao enviar mensagem')
    }

    return response.json()
  },

  async getConversation(visitorId: string) {
    const response = await fetch(`${API_URL}/ai/conversation/${visitorId}`)

    if (!response.ok) {
      throw new Error('Erro ao buscar conversa')
    }

    return response.json()
  },
}

