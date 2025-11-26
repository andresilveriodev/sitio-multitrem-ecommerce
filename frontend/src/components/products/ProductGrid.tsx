'use client'

import type { Product, KitProduct } from '@/types'
import { ProductCard } from './ProductCard'
import { Skeleton } from '@/components/ui'

export interface ProductGridProps {
  products: (Product | KitProduct)[]
  loading?: boolean
  onAddToCart?: (product: Product | KitProduct) => void
  onSelectKit?: (product: KitProduct) => void
}

export function ProductGrid({
  products,
  loading = false,
  onAddToCart,
  onSelectKit,
}: ProductGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} variant="card" className="h-80" />
        ))}
      </div>
    )
  }

  if (products.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-lg text-foreground/70">
          Nenhum produto encontrado nesta categoria.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          onAddToCart={onAddToCart}
          onSelectKit={onSelectKit}
        />
      ))}
    </div>
  )
}

