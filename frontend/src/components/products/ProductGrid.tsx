'use client'

import type { Product, KitProduct } from '@/types'
import { ProductCard } from './ProductCard'
import { Skeleton } from '@/components/ui'
import styles from './ProductGrid.module.css'

export interface ProductGridProps {
  products: (Product | KitProduct)[]
  loading?: boolean
  onAddToCart?: (product: Product | KitProduct) => void
  onSelectKit?: (product: KitProduct) => void
}

export function ProductGrid({ products, loading = false, onAddToCart, onSelectKit }: ProductGridProps) {
  if (loading) {
    return (
      <div className={styles['grid--loading']}>
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} variant="card" className={styles.skeleton} />
        ))}
      </div>
    )
  }

  if (products.length === 0) {
    return (
      <div className={styles.empty}>
        <p className={styles.empty__message}>Nenhum produto encontrado nesta categoria.</p>
      </div>
    )
  }

  return (
    <div className={styles.grid}>
      {products.map((product) => (
        <ProductCard key={product.id} product={product} onAddToCart={onAddToCart} onSelectKit={onSelectKit} />
      ))}
    </div>
  )
}

