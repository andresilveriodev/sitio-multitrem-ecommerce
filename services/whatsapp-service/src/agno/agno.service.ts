import { Injectable } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import axios, { AxiosInstance } from 'axios'
import * as FormDataLib from 'form-data'

@Injectable()
export class AgnoService {
  private readonly agnoUrl: string
  private readonly axiosInstance: AxiosInstance

  constructor(private readonly configService: ConfigService) {
    this.agnoUrl = this.configService.get<string>(
      'AI_SERVICE_URL',
      'http://localhost:7777',
    )

    this.axiosInstance = axios.create({
      baseURL: this.agnoUrl,
      timeout: 60000, // 60 segundos (aumentado para evitar timeout)
    })

    console.log(`🤖 [Agno] Conectado em: ${this.agnoUrl}`)
  }

  /**
   * Chama o Agno AgentOS via agente único completo
   * Implementa retry com exponential backoff para rate limits
   */
  async chat(
    userId: string,
    message: string,
    conversationHistory?: any[],
  ): Promise<string> {
    const maxRetries = 3
    let retryCount = 0

    while (retryCount < maxRetries) {
      try {
        // ✅ Chamar o agente único completo
        const requestUrl = `${this.agnoUrl}/agents/assistente_sitio_multitrem/runs`
        
        console.log(`🤖 [Agno] Chamando agente: assistente_sitio_multitrem`)
        console.log(`📝 [Agno] User ID: ${userId}`)
        console.log(`📝 [Agno] Mensagem: ${message.substring(0, 50)}...`)

        const FormData = FormDataLib
        const formData = new FormData()
        formData.append('message', message)
        formData.append('stream', 'false')
        formData.append('user_id', userId)
        formData.append('session_id', `whatsapp_${userId}`)

        const response = await this.axiosInstance.post(requestUrl, formData, {
          headers: {
            ...formData.getHeaders(),
          },
          timeout: 60000, // 60 segundos
        })

        const agnoResponse = response.data

        // Extrair resposta do agente
        let responseText = ''

        if (agnoResponse.content) {
          responseText = agnoResponse.content
        } else if (typeof agnoResponse === 'string') {
          responseText = agnoResponse
        }

        // Limpar resposta
        responseText = responseText.trim()

        if (!responseText) {
          responseText = 'Desculpe, não consegui gerar uma resposta adequada. Pode reformular sua pergunta?'
        }

        // Log de sucesso
        console.log(`✅ [Agno] Resposta recebida do assistente_sitio_multitrem`)

        return responseText
      } catch (error: any) {
        console.error('❌ [Agno] Erro ao chamar AgentOS:', error.message)
        
        // Verificar se é rate limit
        const errorMessage = error.message || ''
        const errorData = error.response?.data || {}
        const isRateLimit = 
          errorMessage.includes('rate limit') ||
          errorMessage.includes('Rate limit') ||
          errorMessage.includes('rate_limit') ||
          errorData.message?.includes('rate limit') ||
          errorData.error?.message?.includes('rate limit') ||
          error.response?.status === 429

        if (isRateLimit && retryCount < maxRetries - 1) {
          retryCount++
          
          // Extrair tempo de espera da mensagem de erro (ex: "try again in 34.802s")
          const waitTimeMatch = errorMessage.match(/try again in ([\d.]+)s/i)
          let waitTime = waitTimeMatch 
            ? Math.ceil(parseFloat(waitTimeMatch[1])) * 1000 
            : Math.pow(2, retryCount) * 1000 // Exponential backoff: 2s, 4s, 8s
          
          // Limitar tempo máximo de espera a 60 segundos
          waitTime = Math.min(waitTime, 60000)
          
          console.log(`⏳ [Agno] Rate limit atingido. Tentativa ${retryCount}/${maxRetries}. Aguardando ${waitTime/1000}s...`)
          await new Promise(resolve => setTimeout(resolve, waitTime))
          continue // Tentar novamente
        }
        
        if (error.code === 'ECONNREFUSED' || error.response?.status === 0) {
          throw new Error('Agno AgentOS não está rodando. Verifique se o servidor está ativo em http://localhost:7777')
        }
        
        if (error.code === 'ETIMEDOUT' || errorMessage.includes('timeout')) {
          console.error('❌ [Agno] Timeout ao chamar AgentOS')
          throw new Error('Timeout ao processar mensagem. Tente novamente.')
        }

        if (error.response?.status === 404) {
          throw new Error(`Agente 'assistente_sitio_multitrem' não encontrado. Verifique a configuração do AgentOS.`)
        }

        // Se não for rate limit ou já tentou todas as vezes, lançar erro
        throw error
      }
    }

    // Se chegou aqui, todas as tentativas falharam
    throw new Error('Falha ao processar mensagem após múltiplas tentativas.')
  }
}
