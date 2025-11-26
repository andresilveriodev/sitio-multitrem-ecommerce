'use client'

import Image from 'next/image'
import { Plus, Minus, Trash2 } from 'lucide-react'
import type { CartItem } from '@/types'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'

export interface CartItemCardProps {
  item: CartItem
  onUpdateQuantity: (productId: number, quantity: number) => void
  onRemove: (productId: number) => void
}

export function CartItemCard({
  item,
  onUpdateQuantity,
  onRemove,
}: CartItemCardProps) {
  const PLACEHOLDER_IMAGE =
    'https://placehold.co/100x100/22c55e/white?text=Produto'

  return (
    <div className="flex gap-4 py-4 border-b border-foreground/10 last:border-0">
      {/* Imagem */}
      <div className="relative h-20 w-20 flex-shrink-0 rounded-lg overflow-hidden bg-primary-50">
        <Image
          src={PLACEHOLDER_IMAGE}
          alt={item.productName}
          fill
          className="object-cover"
        />
      </div>

      {/* Conteúdo */}
      <div className="flex-1 min-w-0">
        <h4 className="font-medium text-foreground mb-1 truncate">
          {item.productName}
        </h4>

        {/* Hortaliças selecionadas (para kits) */}
        {item.selectedItems && item.selectedItems.length > 0 && (
          <p className="text-xs text-foreground/60 mb-2">
            {item.selectedItems.join(', ')}
          </p>
        )}

        {/* Controles */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onUpdateQuantity(item.productId, item.quantity - 1)}
              className="h-8 w-8 p-0"
              aria-label="Diminuir quantidade"
            >
              <Minus className="h-4 w-4" />
            </Button>
            <span className="w-8 text-center text-sm font-medium">
              {item.quantity}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onUpdateQuantity(item.productId, item.quantity + 1)}
              className="h-8 w-8 p-0"
              aria-label="Aumentar quantidade"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-semibold text-foreground">
                R$ {item.subtotal.toFixed(2).replace('.', ',')}
              </p>
              {item.quantity > 1 && (
                <p className="text-xs text-foreground/60">
                  R$ {item.unitPrice.toFixed(2).replace('.', ',')} cada
                </p>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemove(item.productId)}
              className="h-8 w-8 p-0 text-red-500 hover:text-red-700 hover:bg-red-50"
              aria-label="Remover item"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

