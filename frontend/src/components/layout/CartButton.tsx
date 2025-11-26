'use client'

import { ShoppingBag } from 'lucide-react'
import { Badge } from '@/components/ui'
import { cn } from '@/lib/utils'

export interface CartButtonProps {
  itemCount?: number
  onClick?: () => void
  className?: string
}

export function CartButton({
  itemCount = 0,
  onClick,
  className,
}: CartButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'relative flex items-center justify-center rounded-lg p-2 text-foreground transition-colors hover:bg-primary-50 hover:text-primary-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
        className
      )}
      aria-label={`Carrinho de compras${itemCount > 0 ? ` com ${itemCount} itens` : ''}`}
    >
      <ShoppingBag className="h-6 w-6" />
      {itemCount > 0 && (
        <Badge
          variant="error"
          size="sm"
          className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center p-0 text-xs"
        >
          {itemCount > 99 ? '99+' : itemCount}
        </Badge>
      )}
    </button>
  )
}

