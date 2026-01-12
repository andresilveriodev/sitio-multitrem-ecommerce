'use client'

import { X, ShoppingBag, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { useCart } from '@/hooks/useCart'
import { Button } from '@/components/ui'
import { CartItemCard } from './CartItemCard'
import { cn } from '@/lib/utils'

export function CartDrawer() {
  const {
    isOpen,
    closeCart,
    items,
    total,
    itemCount,
    isEmpty,
    updateQuantity,
    removeItem,
  } = useCart()

  if (!isOpen) return null

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
        onClick={closeCart}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        className={cn(
          'fixed right-0 top-0 z-50 h-full w-full bg-white shadow-xl transition-transform duration-300 ease-in-out sm:w-96',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Carrinho de compras"
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-foreground/10 px-6 py-4">
            <div className="flex items-center gap-2">
              <ShoppingBag className="h-5 w-5 text-primary-600" />
              <h2 className="text-lg font-semibold">Seu Carrinho</h2>
              {itemCount > 0 && (
                <span className="rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-800">
                  {itemCount}
                </span>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={closeCart}
              aria-label="Fechar carrinho"
              className="h-8 w-8 p-0"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Corpo (scrollável) */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {isEmpty ? (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <ShoppingBag className="mb-4 h-16 w-16 text-foreground/20" />
                <h3 className="mb-2 text-lg font-semibold text-foreground">
                  Seu carrinho está vazio
                </h3>
                <p className="mb-6 text-sm text-foreground/70">
                  Adicione produtos para começar
                </p>
                <Button
                  variant="outline"
                  onClick={() => {
                    closeCart()
                    document.getElementById('produtos')?.scrollIntoView({
                      behavior: 'smooth',
                    })
                  }}
                >
                  Ver Produtos
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                {items.map((item) => (
                  <CartItemCard
                    key={`${item.productId}-${JSON.stringify(item.selectedItems || [])}`}
                    item={item}
                    onUpdateQuantity={updateQuantity}
                    onRemove={removeItem}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Footer (fixo) */}
          {!isEmpty && (
            <div className="border-t border-foreground/10 bg-white p-6">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-base font-medium text-foreground">
                  Subtotal:
                </span>
                <span className="text-xl font-bold text-primary-600">
                  R$ {total.toFixed(2).replace('.', ',')}
                </span>
              </div>
              <Link href="/checkout" onClick={closeCart}>
                <Button
                  variant="primary"
                  size="lg"
                  className="w-full"
                  rightIcon={<ArrowRight className="h-5 w-5" />}
                >
                  Finalizar Pedido
                </Button>
              </Link>
              <p className="mt-2 text-center text-xs text-foreground/60">
                Pix, Boleto ou Cartão
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

