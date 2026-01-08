import { Injectable } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import axios from 'axios'
import * as FormData from 'form-data'

@Injectable()
export class AgnoService {
  private readonly agnoUrl: string

  constructor(private readonly configService: ConfigService) {
    this.agnoUrl = configService.get<string>('AI_SERVICE_URL', 'http://localhost:7777')
  }

  /**
   * Roteia a mensagem para o agente correto baseado no contexto
   */
  private routeToAgent(message: string, conversationHistory?: any[]): string {
    const lowerMessage = message.toLowerCase()

    // Palavras-chave para roteamento
    if (
      lowerMessage.includes('pagar') ||
      lowerMessage.includes('pix') ||
      lowerMessage.includes('boleto') ||
      lowerMessage.includes('pagamento')
    ) {
      return 'Pagamento'
    }

    if (
      lowerMessage.includes('entregar') ||
      lowerMessage.includes('entrega') ||
      lowerMessage.includes('agendar') ||
      lowerMessage.includes('horário') ||
      lowerMessage.includes('quando')
    ) {
      return 'Agendamento'
    }

    if (
      lowerMessage.includes('problema') ||
      lowerMessage.includes('cancelar') ||
      lowerMessage.includes('ajuda') ||
      lowerMessage.includes('reclamação') ||
      lowerMessage.includes('rastrear')
    ) {
      return 'Suporte'
    }

    // Padrão: Vendedor (para vendas e informações de produtos)
    return 'Vendedor'
  }

  /**
   * Envia mensagem para o Agno AgentOS
   */
  async chat(
    userId: string,
    message: string,
    conversationHistory?: any[],
  ): Promise<string> {
    try {
      // Rotear para o agente correto
      const agentName = this.routeToAgent(message, conversationHistory)
      // Agno usa IDs em minúsculas
      const agentId = agentName.toLowerCase()

      console.log(`🤖 [Agno] Roteando para agente: ${agentName} (ID: ${agentId})`)
      console.log(`📝 [Agno] Mensagem: ${message.substring(0, 50)}...`)

      // Preparar requisição com FormData (Agno API expects multipart/form-data)
      const requestUrl = `${this.agnoUrl}/agents/${agentId}/runs`
      const formData = new FormData()
      formData.append('message', message)
      formData.append('stream', 'false')
      formData.append('user_id', userId)

      // Chamar API do Agno AgentOS
      const response = await axios.post(
        requestUrl,
        formData,
        {
          headers: {
            ...formData.getHeaders(), // form-data package provides this method
          },
          timeout: 30000, // 30 segundos
        },
      )

      // Extrair resposta do Agno
      const agnoResponse = response.data

      console.log(`✅ [Agno] Resposta recebida do agente ${agentName}`)

      // O Agno retorna a resposta em diferentes formatos dependendo da versão
      // Tentar extrair a mensagem
      let responseText = ''

      if (agnoResponse.content) {
        responseText = agnoResponse.content
      } else if (agnoResponse.messages && agnoResponse.messages.length > 0) {
        const lastMessage = agnoResponse.messages[agnoResponse.messages.length - 1]
        responseText = lastMessage.content || lastMessage.text || ''
      } else if (agnoResponse.response) {
        responseText = agnoResponse.response
      } else if (typeof agnoResponse === 'string') {
        responseText = agnoResponse
      } else {
        // Fallback: tentar extrair qualquer texto
        responseText =
          JSON.stringify(agnoResponse).substring(0, 500) ||
          'Desculpe, não consegui processar sua mensagem.'
      }

      // Limpar resposta
      responseText = responseText.trim()

      if (!responseText) {
        responseText = 'Desculpe, não consegui gerar uma resposta adequada. Pode reformular sua pergunta?'
      }

      return responseText
    } catch (error: any) {
      console.error('❌ [Agno] Erro ao chamar AgentOS:', error.message)
      
      if (error.response?.status) {
        console.error(`   Status: ${error.response.status}`)
        console.error(`   Data:`, error.response.data)
      }

      if (error.code === 'ECONNREFUSED') {
        console.error('❌ [Agno] AgentOS não está rodando!')
        throw new Error(
          'Agno AgentOS não está rodando. Inicie com: python my_os.py',
        )
      }

      if (error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
        console.error('❌ [Agno] Timeout ao chamar AgentOS')
        throw new Error('Timeout ao processar mensagem. Tente novamente.')
      }

      throw error
    }
  }

  /**
   * Verifica se o Agno está online
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await axios.get(`${this.agnoUrl}/health`, {
        timeout: 5000,
      })
      return response.status === 200
    } catch (error) {
      console.error('❌ [Agno] Health check falhou:', error.message)
      return false
    }
  }

  /**
   * Retorna informações sobre os agentes disponíveis
   */
  getAvailableAgents(): string[] {
    return ['Vendedor', 'Agendamento', 'Pagamento', 'Suporte']
  }

  /**
   * Retorna a URL do Agno configurada
   */
  getAgnoUrl(): string {
    return this.agnoUrl
  }
}




