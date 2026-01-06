'use client'

import { useState } from 'react'
import type { Product, KitProduct, ProductCategory } from '@/types'
import { getProductsByCategory, getProductById } from '@/lib/mock-data'
import { CategoryTabs, ProductGrid, KitSelectionModal } from '@/components/products'
import styles from './Products.module.css'

export interface ProductsProps {
  onAddToCart?: (product: Product | KitProduct, selectedItems?: string[]) => void
  onSelectKit?: (product: KitProduct) => void
}

export function Products({ onAddToCart, onSelectKit }: ProductsProps) {
  const [selectedCategory, setSelectedCategory] = useState<
    ProductCategory | 'all'
  >('all')
  const [selectedKit, setSelectedKit] = useState<KitProduct | null>(null)
  const [isKitModalOpen, setIsKitModalOpen] = useState(false)

  const products = getProductsByCategory(
    selectedCategory === 'all' ? undefined : selectedCategory
  )

  const handleSelectKit = (product: KitProduct) => {
    setSelectedKit(product)
    setIsKitModalOpen(true)
    if (onSelectKit) {
      onSelectKit(product)
    }
  }

  const handleKitConfirm = (selectedItems: string[]) => {
    if (selectedKit && onAddToCart) {
      onAddToCart(selectedKit, selectedItems)
    }
    setIsKitModalOpen(false)
    setSelectedKit(null)
  }

  return (
    <>
      <section id="produtos" className={styles.products}>
        <div className={styles.products__container}>
          {/* Header */}
          <div className={styles.products__header}>
            <h2 className={styles.products__title}>Nossos Produtos</h2>
            <p className={styles.products__subtitle}>
              Tudo fresquinho, colhido no dia do seu pedido
            </p>
          </div>

          {/* Tabs de categoria */}
          <CategoryTabs selectedCategory={selectedCategory} onCategoryChange={setSelectedCategory} />

          {/* Grid de produtos */}
          <ProductGrid products={products} onAddToCart={onAddToCart} onSelectKit={handleSelectKit} />
        </div>
      </section>

      {/* Modal de seleção de kit */}
      <KitSelectionModal
        isOpen={isKitModalOpen}
        onClose={() => {
          setIsKitModalOpen(false)
          setSelectedKit(null)
        }}
        product={selectedKit}
        onConfirm={handleKitConfirm}
      />
    </>
  )
}

