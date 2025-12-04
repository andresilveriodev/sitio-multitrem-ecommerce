'use client'

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from 'react'
import type { AIMessage } from '@/types'
import { aiService } from '@/services/ai.service'

interface ChatContextType {
  messages: AIMessage[]
  isOpen: boolean
  isTyping: boolean
  sendMessage: (content: string, visitorId: string) => Promise<void>
  addAssistantMessage: (content: string, intent?: string) => void
  clearMessages: () => void
  openChat: () => void
  closeChat: () => void
  toggleChat: () => void
  paymentLink: string | null
  setPaymentLink: (link: string | null) => void
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<AIMessage[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [paymentLink, setPaymentLink] = useState<string | null>(null)

  const sendMessage = async (content: string, visitorId: string) => {
    if (!content.trim()) return

    const userMessage: AIMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsTyping(true)

    try {
      // Buscar histórico da conversa
      const history = messages
        .slice(-10)
        .map((msg) => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp,
        }))

      // Chamar ai-service
      const response = await aiService.sendMessage({
        visitorId,
        message: content.trim(),
        conversationHistory: history,
        source: 'web',
      })

      // Adicionar resposta do assistente
      const assistantMessage: AIMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        intent: response.actions.length > 0 ? 'other' : undefined,
      }

      setMessages((prev) => [...prev, assistantMessage])
      setIsTyping(false)

      // Processar ações
      if (response.paymentLink) {
        setPaymentLink(response.paymentLink)
      } else {
        setPaymentLink(null)
      }

      // Sincronizar carrinho se foi modificado
      // O carrinho será atualizado automaticamente quando o usuário interagir com a página
      // ou podemos disparar um evento customizado para atualizar o carrinho
      if (response.cart || response.actions.some((a: any) => 
        a.function === 'add_to_cart' || 
        a.function === 'remove_from_cart' || 
        a.function === 'view_cart'
      )) {
        // Disparar evento para atualizar carrinho
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('cart:refresh'))
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: AIMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
      setIsTyping(false)
    }
  }

  // Função auxiliar para adicionar mensagem do assistente (será usada externamente)
  const addAssistantMessage = (content: string, intent?: string) => {
    const assistantMessage: AIMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content,
      timestamp: new Date().toISOString(),
      intent: intent as any,
    }

    setMessages((prev) => [...prev, assistantMessage])
    setIsTyping(false)
  }

  const clearMessages = () => {
    setMessages([])
  }

  const openChat = () => {
    setIsOpen(true)
    // Adicionar mensagem inicial se for a primeira vez
    if (messages.length === 0) {
      const initialMessage: AIMessage = {
        id: 'initial',
        role: 'assistant',
        content:
          'Olá! 🌿 Sou o assistente do Sítio Multitrem. Posso ajudar você a escolher produtos, montar seu pedido e agendar a entrega. Como posso ajudar?',
        timestamp: new Date().toISOString(),
      }
      setMessages([initialMessage])
    }
  }

  const closeChat = () => {
    setIsOpen(false)
  }

  const toggleChat = () => {
    if (isOpen) {
      closeChat()
    } else {
      openChat()
    }
  }

  return (
    <ChatContext.Provider
      value={{
        messages,
        isOpen,
        isTyping,
        sendMessage,
        addAssistantMessage,
        clearMessages,
        openChat,
        closeChat,
        toggleChat,
        paymentLink,
        setPaymentLink,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const context = useContext(ChatContext)
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider')
  }
  return context
}

// Exportar função para adicionar mensagem do assistente (será usada pelo mock-chat)
export function useChatActions() {
  const context = useContext(ChatContext)
  if (context === undefined) {
    throw new Error('useChatActions must be used within a ChatProvider')
  }
  return {
    addAssistantMessage: (content: string, intent?: string) => {
      const assistantMessage: AIMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content,
        timestamp: new Date().toISOString(),
        intent: intent as any,
      }
      // Acessar setMessages através do contexto
      // Isso será ajustado quando integrarmos com mock-chat
    },
    setIsTyping: (typing: boolean) => {
      // Será implementado
    },
  }
}

