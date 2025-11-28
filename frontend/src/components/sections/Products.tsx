'use client'

import { useState } from 'react'
import type { Product, KitProduct, ProductCategory } from '@/types'
import {
  getProductsByCategory,
  getProductById,
} from '@/lib/mock-data'
import { CategoryTabs, ProductGrid, KitSelectionModal } from '@/components/products'

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
      <section id="produtos" className="py-20 sm:py-24 md:py-32 bg-background">
        <div className="container-custom">
          {/* Header */}
          <div className="text-center mb-12 sm:mb-16 md:mb-20">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground mb-3 sm:mb-4 leading-tight">
              Nossos Produtos
            </h2>
            <p className="text-lg sm:text-xl text-gray-700 max-w-2xl mx-auto leading-relaxed">
              Tudo fresquinho, colhido no dia do seu pedido
            </p>
          </div>

          {/* Tabs de categoria */}
          <CategoryTabs
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
          />

          {/* Grid de produtos */}
          <ProductGrid
            products={products}
            onAddToCart={onAddToCart}
            onSelectKit={handleSelectKit}
          />
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

