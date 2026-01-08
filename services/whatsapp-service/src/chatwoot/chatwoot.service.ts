import { Injectable, Inject } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import axios, { AxiosInstance } from 'axios'
import {
  ChatwootWebhookPayload,
  ChatwootContact,
  ChatwootConversation,
  CreateContactDto,
  CreateConversationDto,
  SendMessageDto,
} from './dto'

@Injectable()
export class ChatwootService {
  private readonly axiosInstance: AxiosInstance
  private readonly baseUrl: string
  private readonly accountId: number
  private readonly accessToken: string
  private readonly inboxId: number
  private readonly aiEnabled: boolean
  private readonly autoAssign: boolean

  constructor(private readonly configService: ConfigService) {
    this.baseUrl = configService.get<string>('CHATWOOT_URL', 'http://localhost:3000')
    this.accountId = Number(configService.get<string>('CHATWOOT_ACCOUNT_ID', '1'))
    this.accessToken = configService.get<string>('CHATWOOT_ACCESS_TOKEN', '')
    this.inboxId = Number(configService.get<string>('CHATWOOT_INBOX_ID', '1'))
    this.aiEnabled = configService.get<string>('CHATWOOT_AI_ENABLED', 'true') === 'true'
    this.autoAssign = configService.get<string>('CHATWOOT_AUTO_ASSIGN', 'false') === 'true'

    this.axiosInstance = axios.create({
      baseURL: `${this.baseUrl}/public/api/v1/accounts/${this.accountId}`,
      headers: {
        'Content-Type': 'application/json',
        api_access_token: this.accessToken,
      },
    })
  }

  /**
   * Verifica se Chatwoot está configurado
   */
  isConfigured(): boolean {
    return !!this.accessToken && !!this.baseUrl && this.accountId > 0 && this.inboxId > 0
  }

  /**
   * Verifica se IA está habilitada
   */
  isAiEnabled(): boolean {
    return this.aiEnabled
  }

  /**
   * Busca ou cria contato no Chatwoot
   */
  async findOrCreateContact(phoneNumber: string, name?: string): Promise<ChatwootContact | null> {
    if (!this.isConfigured()) {
      return null
    }

    try {
      // Buscar contato existente
      try {
        const searchResponse = await this.axiosInstance.get('/contacts/search', {
          params: {
            q: phoneNumber,
          },
        })

        if (searchResponse.data?.payload?.length > 0) {
          return searchResponse.data.payload[0]
        }
      } catch (error) {
        // Se busca falhar, continuar para criar novo contato
        console.warn('Contact search failed, creating new contact:', error)
      }

      // Criar novo contato
      const createDto: CreateContactDto = {
        identifier: phoneNumber,
        phone_number: phoneNumber,
        name: name || `WhatsApp ${phoneNumber}`,
        custom_attributes: {
          source: 'whatsapp',
        },
      }

      const createResponse = await this.axiosInstance.post('/contacts', createDto)
      return createResponse.data?.payload
    } catch (error: any) {
      console.error('Error finding/creating contact in Chatwoot:', error.message)
      return null
    }
  }

  /**
   * Busca ou cria conversa no Chatwoot
   */
  async findOrCreateConversation(
    phoneNumber: string,
    contactId: number,
  ): Promise<ChatwootConversation | null> {
    if (!this.isConfigured()) {
      return null
    }

    try {
      // Buscar conversas do contato
      const conversationsResponse = await this.axiosInstance.get(`/contacts/${contactId}/conversations`)

      if (conversationsResponse.data?.payload?.length > 0) {
        // Encontrar conversa na inbox correta
        const conversation = conversationsResponse.data.payload.find(
          (conv: any) => conv.inbox_id === this.inboxId,
        )

        if (conversation) {
          return conversation
        }
      }

      // Criar nova conversa
      const createDto: CreateConversationDto = {
        source_id: phoneNumber,
        inbox_id: this.inboxId,
        contact_id: contactId,
      }

      const createResponse = await this.axiosInstance.post('/conversations', createDto)
      const conversation = createResponse.data

      // Atribuir automaticamente se configurado
      if (this.autoAssign && conversation?.id) {
        try {
          // Buscar primeiro agente disponível (ou usar ID 1 como padrão)
          await this.axiosInstance.post(`/conversations/${conversation.id}/assignments`, {
            assignee_id: 1, // TODO: Buscar agente disponível dinamicamente
          })
        } catch (error) {
          // Ignorar erro de atribuição
          console.warn('Failed to auto-assign conversation:', error)
        }
      }

      return conversation
    } catch (error: any) {
      console.error('Error finding/creating conversation in Chatwoot:', error.message)
      return null
    }
  }

  /**
   * Verifica se conversa está atribuída a um agente
   */
  async isConversationAssigned(conversationId: number): Promise<boolean> {
    if (!this.isConfigured()) {
      return false
    }

    try {
      const response = await this.axiosInstance.get(`/conversations/${conversationId}`)
      const conversation = response.data

      return !!conversation?.assignee?.id
    } catch (error: any) {
      console.error('Error checking conversation assignment:', error.message)
      return false
    }
  }

  /**
   * Sincroniza mensagem recebida do WhatsApp com Chatwoot
   */
  async syncIncomingMessage(
    phoneNumber: string,
    message: string,
    timestamp?: number,
  ): Promise<{ conversationId: number | null; isAssigned: boolean }> {
    if (!this.isConfigured()) {
      return { conversationId: null, isAssigned: false }
    }

    try {
      // Buscar ou criar contato
      const contact = await this.findOrCreateContact(phoneNumber)
      if (!contact) {
        return { conversationId: null, isAssigned: false }
      }

      // Buscar ou criar conversa
      const conversation = await this.findOrCreateConversation(phoneNumber, contact.id)
      if (!conversation) {
        return { conversationId: null, isAssigned: false }
      }

      // Verificar se está atribuída
      const isAssigned = await this.isConversationAssigned(conversation.id)

      // Enviar mensagem para Chatwoot
      const messageDto: SendMessageDto = {
        content: message,
        message_type: 'incoming',
        private: false,
      }

      await this.axiosInstance.post(`/conversations/${conversation.id}/messages`, messageDto)

      return {
        conversationId: conversation.id,
        isAssigned,
      }
    } catch (error: any) {
      console.error('Error syncing incoming message to Chatwoot:', error.message)
      return { conversationId: null, isAssigned: false }
    }
  }

  /**
   * Sincroniza mensagem enviada pela IA com Chatwoot
   */
  async syncOutgoingMessage(conversationId: number, message: string): Promise<boolean> {
    if (!this.isConfigured() || !conversationId) {
      return false
    }

    try {
      const messageDto: SendMessageDto = {
        content: message,
        message_type: 'outgoing',
        private: false,
      }

      await this.axiosInstance.post(`/conversations/${conversationId}/messages`, messageDto)
      return true
    } catch (error: any) {
      console.error('Error syncing outgoing message to Chatwoot:', error.message)
      return false
    }
  }

  /**
   * Processa webhook do Chatwoot (mensagem enviada por agente ou recebida de aluno)
   */
  async processWebhook(payload: ChatwootWebhookPayload): Promise<{
    processed: boolean
    phoneNumber?: string
    message?: string
    conversationId?: number
    messageType?: 'incoming' | 'outgoing'
  }> {
    if (!this.isConfigured()) {
      return { processed: false }
    }

    try {
      // Processar apenas eventos de mensagem criada
      if (payload.event !== 'message_created') {
        return { processed: false }
      }

      // Verificar se é da inbox correta
      if (payload.conversation?.inbox_id !== this.inboxId) {
        return { processed: false }
      }

      // Extrair número do telefone do source_id
      const phoneNumber = payload.conversation.contact_inbox?.source_id
      if (!phoneNumber || !payload.message || payload.message.private) {
        return { processed: false }
      }

      // Verificar tipo de mensagem
      // message_type: 0 = outgoing (agente), 1 = incoming (aluno)
      const isIncoming = payload.message.message_type === 1
      const isOutgoing = payload.message.message_type === 0

      // Processar mensagem recebida (incoming) de aluno
      if (isIncoming && payload.message.content) {
        return {
          processed: true,
          phoneNumber,
          message: payload.message.content,
          conversationId: payload.conversation.id,
          messageType: 'incoming',
        }
      }

      // Processar mensagem enviada (outgoing) por agente (não bot)
      if (
        isOutgoing &&
        payload.message.sender?.type !== 'agent_bot' &&
        payload.message.content
      ) {
      return {
        processed: true,
        phoneNumber,
        message: payload.message.content,
        conversationId: payload.conversation.id,
          messageType: 'outgoing',
        }
      }

      return { processed: false }
    } catch (error: any) {
      console.error('Error processing Chatwoot webhook:', error.message)
      return { processed: false }
    }
  }
}

