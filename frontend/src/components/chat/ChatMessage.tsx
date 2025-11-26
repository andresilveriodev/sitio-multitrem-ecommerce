'use client'

import { cn } from '@/lib/utils'
import type { AIMessage } from '@/types'

interface ChatMessageProps {
  message: AIMessage
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const timestamp =
    typeof message.timestamp === 'string'
      ? new Date(message.timestamp)
      : message.timestamp
  const time = timestamp.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <div
      className={cn(
        'flex w-full',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-2',
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-foreground/10 text-foreground'
        )}
      >
        <p className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </p>
        <p
          className={cn(
            'text-xs mt-1',
            isUser ? 'text-primary-100' : 'text-foreground/50'
          )}
        >
          {time}
        </p>
      </div>
    </div>
  )
}

