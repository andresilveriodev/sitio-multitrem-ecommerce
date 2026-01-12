'use client'

import Image from 'next/image'
import { Plus, Minus, Trash2 } from 'lucide-react'
import type { CartItem } from '@/types'
import { Button } from '@/components/ui'
import styles from './CartItemCard.module.css'

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
  const getImageUrl = (slug?: string): string => {
    if (item.imageUrl) return item.imageUrl
    if (slug) return `/images/products/${slug}.jpg`
    return 'https://placehold.co/100x100/22c55e/white?text=Produto'
  }

  // Tentar extrair slug do nome do produto para fallback
  const slug = item.productName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
  const imageUrl = getImageUrl(slug)

  return (
    <div className={styles.item}>
      {/* Imagem */}
      <div className={styles.item__image}>
        <Image src={imageUrl} alt={item.productName} fill className={styles.item__image} />
      </div>

      {/* Conteúdo */}
      <div className={styles.item__content}>
        <h4 className={styles.item__name}>{item.productName}</h4>

        {/* Hortaliças selecionadas (para kits) */}
        {item.selectedItems && item.selectedItems.length > 0 && (
          <p className={styles.item__selected}>{item.selectedItems.join(', ')}</p>
        )}

        {/* Controles */}
        <div className={styles.item__controls}>
          <div className={styles.item__quantity}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onUpdateQuantity(item.productId, item.quantity - 1)}
              className="h-8 w-8 p-0"
              aria-label="Diminuir quantidade"
            >
              <Minus className="h-4 w-4" />
            </Button>
            <span className={styles.item__quantity_value}>{item.quantity}</span>
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
            <p className={styles.item__price}>R$ {item.subtotal.toFixed(2).replace('.', ',')}</p>
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

