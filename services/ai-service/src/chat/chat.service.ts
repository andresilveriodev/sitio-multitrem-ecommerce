import { Injectable, Inject } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import OpenAI from 'openai'
import Redis from 'ioredis'
import axios from 'axios'
import { buildSystemPrompt } from '../prompts/sales-assistant.prompt'
import { FUNCTION_DEFINITIONS } from '../functions/functions.registry'
import { ExecutorService } from '../functions/executor.service'
import { ChatMessageDto } from './dto'

@Injectable()
export class ChatService {
  private readonly openai: OpenAI
  private readonly model: string
  private readonly temperature: number
  private readonly maxTokens: number
  private readonly productServiceUrl: string

  constructor(
    @Inject('OPENAI_CLIENT')
    private readonly openaiClient: OpenAI,
    @Inject('REDIS_CLIENT')
    private readonly redis: Redis,
    private readonly configService: ConfigService,
    private readonly executorService: ExecutorService,
  ) {
    this.openai = openaiClient
    this.model = configService.get<string>('OPENAI_MODEL', 'gpt-4o-mini')
    // Converter string para number (variáveis de ambiente são sempre strings)
    this.temperature = Number(configService.get<string>('OPENAI_TEMPERATURE', '0.7')) || 0.7
    this.maxTokens = Number(configService.get<string>('OPENAI_MAX_TOKENS', '500')) || 500
    this.productServiceUrl =
      configService.get<string>('PRODUCT_SERVICE_URL') ||
      'http://localhost:3001'
  }

  async processMessage(dto: ChatMessageDto) {
    const { visitorId, message, conversationHistory, source } = dto

    // Buscar histórico do Redis se não fornecido
    let history = conversationHistory || (await this.getConversationHistory(visitorId))

    // Buscar produtos atuais (com tratamento de erro se Product Service não estiver disponível)
    let products: any[] = []
    try {
      const productsResponse = await axios.get(`${this.productServiceUrl}/products`, {
        timeout: 5000, // Timeout de 5 segundos
      })
      products = productsResponse.data || []
    } catch (error: any) {
      console.warn(
        `Product Service não disponível (${this.productServiceUrl}): ${error.message}. Continuando sem lista de produtos.`,
      )
      // Continua com lista vazia de produtos
      products = []
    }

    // Montar system prompt com produtos
    const systemPrompt = buildSystemPrompt(products)

    // Montar mensagens para OpenAI
    // Mapear histórico: pode vir do Redis (com role) ou do WhatsApp (com from/text/type)
    const mappedHistory = history.slice(-10).map((msg: any) => {
      // Se já tem role (formato do Redis), usar diretamente
      if (msg.role && msg.content) {
        return {
          role: msg.role,
          content: msg.content,
        }
      }
      // Se vem do WhatsApp (formato from/text/type), mapear
      if (msg.text) {
        return {
          role: msg.type === 'incoming' ? 'user' : 'assistant',
          content: msg.text,
        }
      }
      // Fallback: tentar usar como está
      return {
        role: msg.role || 'user',
        content: msg.content || msg.text || '',
      }
    })

    const messages: any[] = [
      { role: 'system', content: systemPrompt },
      ...mappedHistory,
      { role: 'user', content: message },
    ]

    // Chamar OpenAI com function calling
    let response = await this.openai.chat.completions.create({
      model: this.model,
      messages: messages as any,
      tools: FUNCTION_DEFINITIONS,
      tool_choice: 'auto',
      temperature: this.temperature,
      max_tokens: this.maxTokens,
    })

    const assistantMessage = response.choices[0].message
    const actions: any[] = []

    // Se a IA chamou funções, executar
    if (assistantMessage.tool_calls && assistantMessage.tool_calls.length > 0) {
      // Adicionar mensagem do assistant com tool_calls APENAS UMA VEZ
      messages.push({
        role: 'assistant',
        content: assistantMessage.content,
        tool_calls: assistantMessage.tool_calls,
      })

      // Executar cada função e adicionar resposta
      for (const toolCall of assistantMessage.tool_calls) {
        const functionName = toolCall.function.name as any
        const params = JSON.parse(toolCall.function.arguments)

        // Executar função
        const result = await this.executorService.executeFunction(
          functionName,
          params,
          { visitorId },
        )

        actions.push({
          function: functionName,
          params,
          result,
        })

        // Adicionar mensagem de resposta (tool) para cada tool_call
        messages.push({
          role: 'tool',
          tool_call_id: toolCall.id,
          content: JSON.stringify(result),
        })
      }

      // Chamar OpenAI novamente com resultados
      response = await this.openai.chat.completions.create({
        model: this.model,
        messages: messages as any,
        tools: FUNCTION_DEFINITIONS,
        tool_choice: 'auto',
        temperature: this.temperature,
        max_tokens: this.maxTokens,
      })
    }

    const finalResponse = response.choices[0].message.content || 'Desculpe, não consegui processar sua mensagem.'

    // Salvar no histórico
    await this.saveMessage(visitorId, 'user', message, source)
    await this.saveMessage(visitorId, 'assistant', finalResponse, source)

    // Buscar carrinho atualizado se houver ações
    let cart = null
    if (actions.some((a) => a.function === 'add_to_cart' || a.function === 'remove_from_cart' || a.function === 'view_cart')) {
      try {
        const cartResponse = await axios.get(
          `${this.configService.get<string>('CART_SERVICE_URL') || 'http://localhost:3002'}/cart/${visitorId}`,
        )
        cart = cartResponse.data
      } catch (error) {
        // Ignorar erro
      }
    }

    // Extrair link de pagamento se houver
    let paymentLink = null
    const paymentAction = actions.find((a) => a.function === 'generate_payment_link')
    if (paymentAction && paymentAction.result.success) {
      paymentLink = paymentAction.result.payment?.qrCode || paymentAction.result.payment?.boletoUrl
    }

    return {
      response: finalResponse,
      actions,
      cart,
      paymentLink,
    }
  }

  async getConversationHistory(visitorId: string) {
    try {
      const key = `ai:conversation:${visitorId}`
      const history = await this.redis.lrange(key, 0, 19)
      return history.map((msg) => JSON.parse(msg))
    } catch (error) {
      return []
    }
  }

  private async saveMessage(
    visitorId: string,
    role: 'user' | 'assistant' | 'system',
    content: string,
    source?: string,
  ) {
    try {
      const key = `ai:conversation:${visitorId}`
      const message = {
        role,
        content,
        timestamp: new Date().toISOString(),
        source,
      }
      await this.redis.lpush(key, JSON.stringify(message))
      await this.redis.ltrim(key, 0, 19)
      await this.redis.expire(key, 86400) // 24 horas
    } catch (error) {
      console.error('Error saving message:', error)
    }
  }
}

