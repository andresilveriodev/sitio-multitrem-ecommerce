'use client'

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from 'react'
import type { AIMessage } from '@/types'

interface ChatContextType {
  messages: AIMessage[]
  isOpen: boolean
  isTyping: boolean
  sendMessage: (content: string) => void
  addAssistantMessage: (content: string, intent?: string) => void
  clearMessages: () => void
  openChat: () => void
  closeChat: () => void
  toggleChat: () => void
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<AIMessage[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [isTyping, setIsTyping] = useState(false)

  const sendMessage = (content: string) => {
    if (!content.trim()) return

    const userMessage: AIMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsTyping(true)
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

