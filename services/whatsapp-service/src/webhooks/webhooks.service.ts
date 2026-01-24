import { Injectable, Inject } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import axios from 'axios'
import Redis from 'ioredis'
import { WhatsAppService } from '../whatsapp/whatsapp.service'
import { MessageFormatter } from '../utils/message-formatter'
import { RateLimiter } from '../utils/rate-limiter'
import { AgnoService } from '../agno/agno.service'

@Injectable()
export class WebhooksService {
  private readonly aiServiceUrl: string
  private readonly rateLimiter: RateLimiter
  private readonly useAgno: boolean
  private readonly allowedPhoneNumbers: Set<string>

  constructor(
    @Inject('REDIS_CLIENT')
    private readonly redis: Redis,
    private readonly whatsappService: WhatsAppService,
    private readonly configService: ConfigService,
    private readonly agnoService: AgnoService,
  ) {
    this.aiServiceUrl = configService.get<string>(
      'AI_SERVICE_URL',
      'http://localhost:7777',
    )
    // Usar Agno se a URL for porta 7777 (padrão do AgentOS)
    this.useAgno = this.aiServiceUrl.includes(':7777')
    this.rateLimiter = new RateLimiter(redis, {
      maxRequests: 20,
      windowMs: 60000, // 1 minuto
    })

    // Configurar números permitidos para teste da IA
    // Pode ser configurado via variável de ambiente ou usar os padrões
    const allowedNumbersEnv = configService.get<string>(
      'AI_ALLOWED_PHONE_NUMBERS',
      '+5562981062311,+55 62 8141-2139,+556281062311',
    )

    const allowedNumbers = allowedNumbersEnv
      .split(',')
      .map((num) => num.trim())
      .filter((num) => num.length > 0)

    this.allowedPhoneNumbers = new Set(
      allowedNumbers.map((num) => this.normalizePhoneNumber(num)),
    )

    console.log(`🤖 [Webhooks] AI Service: ${this.aiServiceUrl}`)
    console.log(`🤖 [Webhooks] Usando Agno: ${this.useAgno ? 'SIM' : 'NÃO'}`)
    console.log(
      `📱 [Webhooks] Números permitidos para IA: ${Array.from(this.allowedPhoneNumbers).join(', ')}`,
    )
  }

  /**
   * Normaliza número de telefone removendo espaços, hífens e o sinal +
   * Exemplo: "+55 62 8141-2139" -> "556281412139"
   */
  private normalizePhoneNumber(phoneNumber: string): string {
    return phoneNumber.replace(/[\s\-+]/g, '')
  }

  /**
   * Verifica se o número está na lista de permitidos para usar IA
   */
  private isPhoneNumberAllowed(phoneNumber: string): boolean {
    const normalized = this.normalizePhoneNumber(phoneNumber)
    return this.allowedPhoneNumbers.has(normalized)
  }

  async handleIncomingMessage(payload: any) {
    // Verificar tipo de mensagem
    // Evolution API pode enviar em vários formatos:
    // 1. payload.data.messages[0] (formato de teste)
    // 2. payload.messages[0] (alternativo)
    // 3. payload.data (formato real da Evolution API - sem array)
    let message = payload.data?.messages?.[0] || payload.messages?.[0]
    
    // Se não encontrou em arrays, verificar se payload.data é a própria mensagem
    if (!message && payload.data?.key && payload.data?.message) {
      message = payload.data
    }
    
    if (!message) {
      console.log('❌ [Webhooks] Nenhuma mensagem encontrada no payload')
      console.log('📦 Payload recebido:', JSON.stringify(payload, null, 2))
      return { processed: false, reason: 'No message in payload' }
    }
    
    console.log('✅ [Webhooks] Mensagem extraída com sucesso')
    console.log('🔑 Message key:', message.key)
    console.log('💬 Message content:', message.message)

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

    // Verificar se o número está permitido para usar IA
    const normalizedPhone = this.normalizePhoneNumber(result.phoneNumber)
    const isAllowed = this.isPhoneNumberAllowed(result.phoneNumber)

    if (!isAllowed) {
      console.log(
        `🚫 [Webhooks] Número ${result.phoneNumber} (normalizado: ${normalizedPhone}) não está na lista de permitidos para IA`,
      )

      // Enviar mensagem padrão sem usar IA
      await this.whatsappService.sendText(
        result.phoneNumber,
        'Olá! Obrigado por entrar em contato. Nossa equipe entrará em contato em breve. 😊',
      )

      return {
        ...result,
        aiResponse: null,
        aiBlocked: true,
        reason: 'Phone number not in allowed list for AI testing',
      }
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
      let responseText = ''

      // ✅ Apenas números permitidos chegam aqui
      console.log(
        `✅ [Webhooks] Número ${result.phoneNumber} autorizado para usar IA`,
      )

      // Usar Agno AgentOS ou AI Service legado
      if (this.useAgno) {
        console.log('🤖 [Webhooks] Usando Agno AgentOS')
        responseText = await this.agnoService.chat(
          result.visitorId,
          messageText,
          result.conversationHistory,
        )
      } else {
        console.log('🤖 [Webhooks] Usando AI Service legado')
        // Encaminhar para ai-service legado
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
        responseText = responseData.response || ''
      }

      // Formatar resposta para WhatsApp
      const formattedText = MessageFormatter.formatForWhatsApp(responseText)

      // Enviar resposta
      await this.whatsappService.sendText(result.phoneNumber, formattedText)

      console.log(`✅ [Webhooks] Resposta enviada para ${result.phoneNumber}`)

      return {
        ...result,
        aiResponse: responseText,
        actions: [],
      }
    } catch (error: any) {
      console.error('❌ [Webhooks] Error forwarding to AI service:', error)
      
      // Mensagem de erro mais específica
      let errorMessage = 'Desculpe, não consegui processar sua mensagem no momento. Por favor, tente novamente. 😊'
      
      if (error.message && error.message.includes('Agno AgentOS não está rodando')) {
        errorMessage = 'O sistema de IA está temporariamente indisponível. Por favor, tente novamente em alguns instantes. 🤖'
      }
      
      await this.whatsappService.sendText(
        result.phoneNumber,
        errorMessage,
      )

      return {
        ...result,
        error: 'Failed to get AI response',
        errorDetails: error.message,
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

