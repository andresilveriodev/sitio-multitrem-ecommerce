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
   */
  async chat(
    userId: string,
    message: string,
    conversationHistory?: any[],
  ): Promise<string> {
    try {
      // ✅ Chamar o agente único completo
      const requestUrl = `${this.agnoUrl}/agents/assistente_sitio_multitrem/runs`
      
      console.log(`🤖 [Agno] Chamando agente: assistente_sitio_multitrem`)
      console.log(`📝 [Agno] User ID: ${userId}`)
      console.log(`📝 [Agno] Mensagem: ${message.substring(0, 50)}...`)

      const FormData = FormDataLib.default || FormDataLib
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
      
      if (error.code === 'ECONNREFUSED' || error.response?.status === 0) {
        throw new Error('Agno AgentOS não está rodando. Verifique se o servidor está ativo em http://localhost:7777')
      }
      
      if (error.code === 'ETIMEDOUT' || error.message.includes('timeout')) {
        console.error('❌ [Agno] Timeout ao chamar AgentOS')
        throw new Error('Timeout ao processar mensagem. Tente novamente.')
      }

      if (error.response?.status === 404) {
        throw new Error(`Agente 'assistente_sitio_multitrem' não encontrado. Verifique a configuração do AgentOS.`)
      }

      throw error
    }
  }
}
