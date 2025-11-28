'use client'

import { useEffect, useRef, useState } from 'react'
import { X, Minimize2, Send, Leaf, ShoppingCart, ExternalLink } from 'lucide-react'
import { useChat } from '@/contexts/ChatContext'
import { ChatMessage } from './ChatMessage'
import { Input, Button } from '@/components/ui'
import { useCart } from '@/hooks/useCart'
import { cn } from '@/lib/utils'
import { aiService } from '@/services/ai.service'

export function ChatPanel() {
  const {
    messages,
    isOpen,
    isTyping,
    sendMessage: sendMessageContext,
    closeChat,
    paymentLink,
  } = useChat()
  const { visitorId } = useCart()
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isMinimized, setIsMinimized] = useState(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const handleSend = async () => {
    if (!inputValue.trim() || isTyping) return

    const userMessage = inputValue.trim()
    setInputValue('')
    
    // Enviar mensagem (já processa a resposta do ai-service)
    await sendMessageContext(userMessage, visitorId)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!isOpen) return null

  return (
    <div
      className={cn(
        'fixed bottom-20 right-4 z-50 flex flex-col bg-background border border-foreground/20 rounded-lg shadow-2xl transition-all duration-300',
        isMinimized ? 'h-14 w-80 sm:w-96' : 'h-[500px] w-80 sm:w-96'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-foreground/10 bg-primary-50">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-primary-600 p-2">
            <Leaf className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground text-sm">
              Assistente Sítio Multitrem
            </h3>
            <p className="text-xs text-foreground/70">Online</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 hover:bg-foreground/10 rounded transition-colors"
            aria-label={isMinimized ? 'Expandir' : 'Minimizar'}
          >
            <Minimize2 className="h-4 w-4 text-foreground/70" />
          </button>
          <button
            onClick={closeChat}
            className="p-1 hover:bg-foreground/10 rounded transition-colors"
            aria-label="Fechar"
          >
            <X className="h-4 w-4 text-foreground/70" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-foreground/10 rounded-lg px-4 py-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce" />
                    <div
                      className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce"
                      style={{ animationDelay: '0.1s' }}
                    />
                    <div
                      className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce"
                      style={{ animationDelay: '0.2s' }}
                    />
                  </div>
                </div>
              </div>
            )}
            {paymentLink && (
              <div className="flex justify-start">
                <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 max-w-[80%]">
                  <p className="text-sm font-medium text-foreground mb-2">
                    Link de pagamento gerado
                  </p>
                  <a
                    href={paymentLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 text-sm underline"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Abrir link de pagamento
                  </a>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-foreground/10">
            <div className="flex gap-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Digite sua mensagem..."
                disabled={isTyping}
                className="flex-1"
              />
              <Button
                variant="primary"
                size="sm"
                onClick={handleSend}
                disabled={!inputValue.trim() || isTyping}
                leftIcon={<Send className="h-4 w-4" />}
              >
                Enviar
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

