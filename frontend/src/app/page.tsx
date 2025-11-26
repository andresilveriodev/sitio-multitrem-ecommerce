'use client'

import { Hero } from '@/components/sections/Hero'
import { HowItWorks } from '@/components/sections/HowItWorks'
import { Products } from '@/components/sections/Products'
import { useCart } from '@/hooks/useCart'
import type { Product, KitProduct } from '@/types'

export default function Home() {
  const { addItem, openCart } = useCart()

  const handleAddToCart = (
    product: Product | KitProduct,
    selectedItems?: string[]
  ) => {
    addItem(product, 1, selectedItems)
    openCart()
  }

  return (
    <>
      <Hero />
      <HowItWorks />
      <Products onAddToCart={handleAddToCart} />
      {/* Outras seções serão adicionadas aqui */}
    </>
  )
}
