import { Injectable, Inject } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import axios from 'axios'
import Redis from 'ioredis'
import { WhatsAppService } from '../whatsapp/whatsapp.service'
import { MessageFormatter } from '../utils/message-formatter'
import { RateLimiter } from '../utils/rate-limiter'

@Injectable()
export class WebhooksService {
  private readonly aiServiceUrl: string
  private readonly rateLimiter: RateLimiter

  constructor(
    @Inject('REDIS_CLIENT')
    private readonly redis: Redis,
    private readonly whatsappService: WhatsAppService,
    private readonly configService: ConfigService,
  ) {
    this.aiServiceUrl = configService.get<string>(
      'AI_SERVICE_URL',
      'http://localhost:3007',
    )
    this.rateLimiter = new RateLimiter(redis, {
      maxRequests: 20,
      windowMs: 60000, // 1 minuto
    })
  }

  async handleIncomingMessage(payload: any) {
    // Verificar tipo de mensagem
    const message = payload.messages?.[0]
    if (!message) {
      return { processed: false, reason: 'No message in payload' }
    }

    // Verificar se é mensagem de texto
    const messageText = message.message?.conversation || 
                       message.message?.extendedTextMessage?.text || 
                       ''
    
    // Tratar mídia (imagem, áudio, etc)
    if (message.message?.image || message.message?.audio || message.message?.video) {
      const phoneNumber = message.key.remoteJid.replace('@s.whatsapp.net', '')
      await this.whatsappService.sendText(
        phoneNumber,
        'Desculpe, só consigo ler mensagens de texto 😊 Envie sua mensagem por escrito, por favor!',
      )
      return { processed: true, reason: 'Media message not supported' }
    }

    // Tratar localização
    if (message.message?.locationMessage) {
      // Salvar localização para entrega futura
      const phoneNumber = message.key.remoteJid.replace('@s.whatsapp.net', '')
      const location = message.message.locationMessage
      // TODO: Salvar localização no banco/Redis para uso futuro
      await this.whatsappService.sendText(
        phoneNumber,
        'Obrigado pela localização! Vou usar para agendar sua entrega. 🌍',
      )
      return { processed: true, reason: 'Location saved' }
    }

    // Se não for texto, ignorar
    if (!messageText) {
      return { processed: false, reason: 'No text message' }
    }

    const result = await this.whatsappService.handleIncomingMessage(payload)

    if (!result.processed) {
      return result
    }

    // Rate limiting
    const rateLimit = await this.rateLimiter.checkLimit(result.phoneNumber)
    if (!rateLimit.allowed) {
      await this.whatsappService.sendText(
        result.phoneNumber,
        'Aguarde um momento antes de enviar outra mensagem... ⏳',
      )
      return {
        ...result,
        rateLimited: true,
      }
    }

    try {
      // Encaminhar para ai-service
      const aiResponse = await axios.post(
        `${this.aiServiceUrl}/ai/chat`,
        {
          visitorId: result.visitorId,
          message: messageText,
          conversationHistory: result.conversationHistory,
          source: 'whatsapp',
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        },
      )

      const responseData = aiResponse.data
      const responseText = responseData.response || ''

      // Formatar resposta para WhatsApp
      const formattedText = MessageFormatter.formatForWhatsApp(responseText)

      // Processar ações especiais
      if (responseData.paymentLink) {
        // Se tem link de pagamento Pix
        const pixCode = MessageFormatter.extractPixCode(responseText)
        if (pixCode) {
          await this.whatsappService.sendText(
            result.phoneNumber,
            `💰 *Código Pix:*\n\n\`${pixCode}\`\n\nCopie o código acima para pagar.`,
          )
        } else {
          await this.whatsappService.sendText(
            result.phoneNumber,
            `${formattedText}\n\n💳 Link de pagamento: ${responseData.paymentLink}`,
          )
        }
      } else if (MessageFormatter.isProductList(formattedText)) {
        // Se lista produtos, usar sendList
        const products = this.extractProductsFromText(formattedText)
        if (products.length > 0) {
          await this.whatsappService.sendList({
            to: result.phoneNumber,
            title: 'Nossos Produtos',
            description: 'Escolha uma categoria:',
            buttonText: 'Ver Produtos',
            sections: [
              {
                title: 'Categorias',
                rows: products.map((p, i) => ({
                  id: `product_${i}`,
                  title: p.name,
                  description: p.price ? `R$ ${p.price}` : undefined,
                })),
              },
            ],
          })
        } else {
          await this.whatsappService.sendText(result.phoneNumber, formattedText)
        }
      } else if (MessageFormatter.isConfirmationRequest(formattedText)) {
        // Se pede confirmação, usar botões
        await this.whatsappService.sendButtons({
          to: result.phoneNumber,
          message: formattedText,
          buttons: ['✅ Confirmar', '❌ Cancelar'],
        })
      } else {
        // Mensagem normal
        await this.whatsappService.sendText(result.phoneNumber, formattedText)
      }

      // Se tem carrinho, mencionar total
      if (responseData.cart && responseData.cart.total > 0) {
        await this.whatsappService.sendText(
          result.phoneNumber,
          `🛒 *Carrinho atual:* R$ ${responseData.cart.total.toFixed(2)}`,
        )
      }

      return {
        ...result,
        aiResponse: responseText,
        actions: responseData.actions || [],
      }
    } catch (error: any) {
      console.error('Error forwarding to AI service:', error)
      // Enviar mensagem padrão em caso de erro
      await this.whatsappService.sendText(
        result.phoneNumber,
        'Desculpe, não consegui processar sua mensagem no momento. Por favor, tente novamente. 😊',
      )

      return {
        ...result,
        error: 'Failed to get AI response',
      }
    }
  }

  private extractProductsFromText(text: string): Array<{ name: string; price?: string }> {
    const products: Array<{ name: string; price?: string }> = []
    const lines = text.split('\n')

    for (const line of lines) {
      // Procurar por padrões como "• Produto - R$ X"
      const match = line.match(/[•\-*]\s*(.+?)(?:\s*-\s*R\$\s*([0-9,]+))?/i)
      if (match) {
        products.push({
          name: match[1].trim(),
          price: match[2] ? `R$ ${match[2]}` : undefined,
        })
      }
    }

    return products.slice(0, 10) // Máximo 10 produtos
  }
}

