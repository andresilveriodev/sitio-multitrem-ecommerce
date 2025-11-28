import { Injectable, Inject } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import axios from 'axios'
import { WhatsAppService } from '../whatsapp/whatsapp.service'

@Injectable()
export class WebhooksService {
  private readonly aiServiceUrl: string

  constructor(
    private readonly whatsappService: WhatsAppService,
    private readonly configService: ConfigService,
  ) {
    this.aiServiceUrl = configService.get<string>(
      'AI_SERVICE_URL',
      'http://localhost:3007',
    )
  }

  async handleIncomingMessage(payload: any) {
    const result = await this.whatsappService.handleIncomingMessage(payload)

    if (!result.processed) {
      return result
    }

    try {
      // Encaminhar para ai-service
      const aiResponse = await axios.post(
        `${this.aiServiceUrl}/ai/chat`,
        {
          visitorId: result.visitorId,
          message: result.message,
          conversationHistory: result.conversationHistory,
          source: 'whatsapp',
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        },
      )

      // Enviar resposta da IA de volta via WhatsApp
      if (aiResponse.data.response) {
        await this.whatsappService.sendText(
          result.phoneNumber,
          aiResponse.data.response,
        )
      }

      return {
        ...result,
        aiResponse: aiResponse.data.response,
      }
    } catch (error: any) {
      console.error('Error forwarding to AI service:', error)
      // Enviar mensagem padrão em caso de erro
      await this.whatsappService.sendText(
        result.phoneNumber,
        'Desculpe, não consegui processar sua mensagem no momento. Por favor, tente novamente.',
      )

      return {
        ...result,
        error: 'Failed to get AI response',
      }
    }
  }
}

