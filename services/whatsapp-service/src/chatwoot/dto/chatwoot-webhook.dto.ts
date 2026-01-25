export interface ChatwootContact {
  id: number
  identifier: string
  phone_number: string
  name: string
  custom_attributes?: Record<string, any>
}

export interface ChatwootConversation {
  id: number
  inbox_id: number
  contact_id: number
  status: string
  assignee?: {
    id: number
    name: string
  }
}

export interface CreateContactDto {
  identifier: string
  phone_number: string
  name: string
  custom_attributes?: Record<string, any>
}

export interface CreateConversationDto {
  source_id: string
  inbox_id: number
  contact_id: number
}

export interface SendMessageDto {
  content: string
  message_type: 'incoming' | 'outgoing'
  private: boolean
}

export interface ChatwootWebhookPayload {
  event: string
  conversation?: {
    id: number
    inbox_id: number
    contact_inbox?: {
      source_id: string
    }
  }
  message?: {
    id: number
    content: string
    message_type: number // 0 = outgoing, 1 = incoming
    private: boolean
    sender?: {
      type: string
    }
  }
}
