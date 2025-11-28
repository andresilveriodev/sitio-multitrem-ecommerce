import { Injectable, Inject, BadRequestException } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import axios, { AxiosInstance } from 'axios'
import Redis from 'ioredis'
import { SendMessageDto, SendButtonsDto, SendListDto } from './dto'

@Injectable()
export class WhatsAppService {
  private readonly axiosInstance: AxiosInstance
  private readonly baseUrl: string
  private readonly apiKey: string
  private readonly instanceName: string

  constructor(
    @Inject('REDIS_CLIENT')
    private readonly redis: Redis,
    private readonly configService: ConfigService,
  ) {
    const config = this.configService.get('EVOLUTION_CONFIG')
    this.baseUrl = config.baseUrl
    this.apiKey = config.apiKey
    this.instanceName = config.instanceName

    this.axiosInstance = axios.create({
      baseURL: `${this.baseUrl}/instance/${this.instanceName}`,
      headers: {
        'Content-Type': 'application/json',
        apikey: this.apiKey,
      },
    })
  }

  async sendText(to: string, message: string) {
    try {
      const response = await this.axiosInstance.post('/send-text', {
        number: to,
        text: message,
      })

      return {
        success: true,
        messageId: response.data.key?.id,
        timestamp: response.data.timestamp,
      }
    } catch (error: any) {
      throw new BadRequestException(
        `Failed to send message: ${error.response?.data?.message || error.message}`,
      )
    }
  }

  async sendButtons(dto: SendButtonsDto) {
    try {
      const buttons = dto.buttons.map((text, index) => ({
        buttonId: `btn_${index}`,
        buttonText: { displayText: text },
        type: 1,
      }))

      const response = await this.axiosInstance.post('/send-buttons', {
        number: dto.to,
        buttons: {
          title: dto.message,
          footer: 'Sítio Multitrem',
          buttons: buttons,
        },
      })

      return {
        success: true,
        messageId: response.data.key?.id,
        timestamp: response.data.timestamp,
      }
    } catch (error: any) {
      throw new BadRequestException(
        `Failed to send buttons: ${error.response?.data?.message || error.message}`,
      )
    }
  }

  async sendList(dto: SendListDto) {
    try {
      const response = await this.axiosInstance.post('/send-list', {
        number: dto.to,
        list: {
          title: dto.title,
          description: dto.description,
          buttonText: dto.buttonText,
          sections: dto.sections,
        },
      })

      return {
        success: true,
        messageId: response.data.key?.id,
        timestamp: response.data.timestamp,
      }
    } catch (error: any) {
      throw new BadRequestException(
        `Failed to send list: ${error.response?.data?.message || error.message}`,
      )
    }
  }

  async getStatus() {
    try {
      const response = await this.axiosInstance.get('/connection-state')

      return {
        status: response.data.state,
        qrCode: response.data.qr?.base64,
        isConnected: response.data.state === 'open',
      }
    } catch (error: any) {
      throw new BadRequestException(
        `Failed to get status: ${error.response?.data?.message || error.message}`,
      )
    }
  }

  async handleIncomingMessage(payload: any) {
    try {
      const message = payload.messages?.[0]
      if (!message) {
        return { processed: false, reason: 'No message in payload' }
      }

      const phoneNumber = message.key.remoteJid.replace('@s.whatsapp.net', '')
      const messageText = message.message?.conversation || message.message?.extendedTextMessage?.text || ''
      const timestamp = message.messageTimestamp

      // Gerar visitorId a partir do número (hash simples)
      const visitorId = `whatsapp_${phoneNumber}`

      // Armazenar mensagem no histórico do Redis
      const conversationKey = `whatsapp:conversation:${phoneNumber}`
      const messageData = {
        from: phoneNumber,
        text: messageText,
        timestamp: timestamp,
        type: 'incoming',
      }

      // Adicionar à lista (máximo 20 mensagens)
      await this.redis.lpush(conversationKey, JSON.stringify(messageData))
      await this.redis.ltrim(conversationKey, 0, 19)
      await this.redis.expire(conversationKey, 86400) // 24 horas

      // Buscar histórico completo
      const history = await this.redis.lrange(conversationKey, 0, 19)
      const conversationHistory = history.map((msg) => JSON.parse(msg))

      return {
        processed: true,
        visitorId,
        phoneNumber,
        message: messageText,
        timestamp,
        conversationHistory,
      }
    } catch (error: any) {
      console.error('Error handling incoming message:', error)
      return { processed: false, error: error.message }
    }
  }

  async getConversationHistory(phoneNumber: string) {
    try {
      const conversationKey = `whatsapp:conversation:${phoneNumber}`
      const history = await this.redis.lrange(conversationKey, 0, 19)
      return history.map((msg) => JSON.parse(msg))
    } catch (error: any) {
      return []
    }
  }
}

