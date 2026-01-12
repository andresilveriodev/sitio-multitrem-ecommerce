'use client'

import Image from 'next/image'
import { useChat } from '@/contexts/ChatContext'
import { ChatPanel } from './ChatPanel'
import { Badge } from '@/components/ui'
import { cn } from '@/lib/utils'

export function ChatWidget() {
  const { isOpen } = useChat()

  const handleWhatsAppClick = () => {
    window.open('https://wa.me/5562981225993', '_blank')
  }

  return (
    <>
      <button
        onClick={handleWhatsAppClick}
        className={cn(
          'fixed bottom-4 right-4 z-50 flex items-center justify-center bg-transparent p-0 rounded-full shadow-lg hover:shadow-xl transition-all duration-300',
          'hover:scale-110 active:scale-95',
          isOpen && 'opacity-0 pointer-events-none'
        )}
        aria-label="Abrir WhatsApp"
      >
        <div className="relative">
          <Image
            src="/images/products/chatboot-em-baixa.png"
            alt="Chat WhatsApp"
            width={64}
            height={64}
            className="animate-blink"
            unoptimized
          />
          <Badge
            variant="success"
            size="sm"
            className="absolute -top-1 -right-1 animate-pulse"
          >
            Online
          </Badge>
        </div>
      </button>
      <ChatPanel />
    </>
  )
}




