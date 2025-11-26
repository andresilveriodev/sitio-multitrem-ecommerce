'use client'

import { MessageCircle } from 'lucide-react'
import { useChat } from '@/contexts/ChatContext'
import { ChatPanel } from './ChatPanel'
import { Badge } from '@/components/ui'
import { cn } from '@/lib/utils'

export function ChatWidget() {
  const { isOpen, toggleChat } = useChat()

  return (
    <>
      <button
        onClick={toggleChat}
        className={cn(
          'fixed bottom-4 right-4 z-50 flex items-center gap-2 bg-primary-600 text-white p-4 rounded-full shadow-lg hover:bg-primary-700 transition-all duration-300',
          'hover:scale-110 active:scale-95',
          isOpen && 'opacity-0 pointer-events-none'
        )}
        aria-label="Abrir chat"
      >
        <MessageCircle className="h-6 w-6" />
        <Badge
          variant="success"
          size="sm"
          className="absolute -top-1 -right-1 animate-pulse"
        >
          Online
        </Badge>
      </button>
      <ChatPanel />
    </>
  )
}

