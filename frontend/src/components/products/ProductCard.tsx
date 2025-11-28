'use client'

import Image from 'next/image'
import { Leaf, Egg, Package, Gift } from 'lucide-react'
import type { Product, KitProduct } from '@/types'
import { Badge, Button } from '@/components/ui'
import { cn } from '@/lib/utils'

const categoryIcons = {
  hortalica: Leaf,
  ovos: Egg,
  kit: Package,
  combo: Gift,
}

const categoryLabels = {
  hortalica: 'Hortaliça',
  ovos: 'Ovos',
  kit: 'Kit',
  combo: 'Combo',
}

export interface ProductCardProps {
  product: Product | KitProduct
  onAddToCart?: (product: Product | KitProduct) => void
  onSelectKit?: (product: KitProduct) => void
}

export function ProductCard({
  product,
  onAddToCart,
  onSelectKit,
}: ProductCardProps) {
  const Icon = categoryIcons[product.category]
  const isKit = product.category === 'kit'

  const handleClick = () => {
    if (isKit && onSelectKit) {
      onSelectKit(product as KitProduct)
    } else if (onAddToCart) {
      onAddToCart(product)
    }
  }

  return (
    <div className="group relative flex h-full flex-col overflow-hidden rounded-lg border border-gray-200 bg-background transition-all hover:shadow-xl">
      {/* Imagem */}
      <div className="relative aspect-square w-full overflow-hidden bg-primary-50">
        {product.imageUrl ? (
          <Image
            src={product.imageUrl}
            alt={product.name}
            fill
            className="object-cover transition-transform group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <Icon className="h-16 w-16 text-primary-300" />
          </div>
        )}

        {/* Badge de categoria */}
        <div className="absolute top-3 right-3">
          <Badge variant="default" size="sm" className="bg-white/95 backdrop-blur-sm">
            <Icon className="mr-1 h-3 w-3" />
            {categoryLabels[product.category]}
          </Badge>
        </div>
      </div>

      {/* Conteúdo */}
      <div className="flex flex-1 flex-col justify-between p-5 sm:p-6">
        <div>
          <h3 className="mb-2 text-lg sm:text-xl font-semibold text-foreground leading-snug">
            {product.name}
          </h3>

          {product.description && (
            <p className="mb-3 text-sm text-gray-700 leading-relaxed">
              {product.description}
            </p>
          )}

          {isKit && (product as KitProduct).kitSize && (
            <p className="mb-4 text-sm text-primary-600 font-medium">
              {(product as KitProduct).kitSize} hortaliças à escolha
            </p>
          )}
        </div>

        {/* Preço e botão */}
        <div className="mt-auto flex items-center justify-between gap-3">
          <div>
            <span className="text-2xl sm:text-3xl font-bold text-primary-600">
              R$ {product.price.toFixed(2).replace('.', ',')}
            </span>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={handleClick}
            className="flex-shrink-0"
          >
            {isKit ? 'Escolher' : 'Adicionar'}
          </Button>
        </div>
      </div>
    </div>
  )
}

