'use client'

import { useCart } from '@/hooks/useCart'
import { Card } from '@/components/ui'
import Image from 'next/image'

export function OrderSummary() {
  const { items, total } = useCart()

  const getImageUrl = (item: typeof items[0]): string => {
    if (item.imageUrl) return item.imageUrl
    // Tentar extrair slug do nome do produto para fallback
    const slug = item.productName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
    return `/images/products/${slug}.jpg`
  }

  return (
    <Card variant="elevated" className="sticky top-24">
      <h3 className="text-lg font-semibold mb-4">Resumo do Pedido</h3>

      {/* Lista de itens */}
      <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
        {items.map((item, index) => (
          <div
            key={`${item.productId}-${index}`}
            className="flex gap-3 text-sm"
          >
            <div className="relative h-16 w-16 flex-shrink-0 rounded overflow-hidden bg-primary-50">
              <Image
                src={getImageUrl(item)}
                alt={item.productName}
                fill
                className="object-cover"
              />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-foreground truncate">
                {item.productName}
              </p>
              {item.selectedItems && item.selectedItems.length > 0 && (
                <p className="text-xs text-foreground/60 mt-1">
                  {item.selectedItems.join(', ')}
                </p>
              )}
              <p className="text-xs text-foreground/60 mt-1">
                {item.quantity}x R$ {item.unitPrice.toFixed(2).replace('.', ',')}
              </p>
            </div>
            <div className="text-right">
              <p className="font-semibold text-foreground">
                R$ {item.subtotal.toFixed(2).replace('.', ',')}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Totais */}
      <div className="border-t border-foreground/10 pt-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-foreground/70">Subtotal:</span>
          <span className="text-foreground">R$ {total.toFixed(2).replace('.', ',')}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-foreground/70">Frete:</span>
          <span className="text-foreground">A calcular</span>
        </div>
        <div className="flex justify-between text-lg font-bold pt-2 border-t border-foreground/10">
          <span>Total:</span>
          <span className="text-primary-600">
            R$ {total.toFixed(2).replace('.', ',')}
          </span>
        </div>
      </div>
    </Card>
  )
}

