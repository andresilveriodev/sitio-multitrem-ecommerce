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
    <div className="group relative flex flex-col overflow-hidden rounded-lg border border-foreground/10 bg-background transition-all hover:shadow-lg">
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
        <div className="absolute top-2 right-2">
          <Badge variant="default" size="sm">
            <Icon className="mr-1 h-3 w-3" />
            {categoryLabels[product.category]}
          </Badge>
        </div>
      </div>

      {/* Conteúdo */}
      <div className="flex flex-1 flex-col p-4">
        <h3 className="mb-1 text-lg font-semibold text-foreground">
          {product.name}
        </h3>

        {product.description && (
          <p className="mb-3 text-sm text-foreground/70">
            {product.description}
          </p>
        )}

        {isKit && (product as KitProduct).kitSize && (
          <p className="mb-3 text-xs text-primary-600 font-medium">
            {(product as KitProduct).kitSize} hortaliças à escolha
          </p>
        )}

        {/* Preço e botão */}
        <div className="mt-auto flex items-center justify-between">
          <div>
            <span className="text-2xl font-bold text-primary-600">
              R$ {product.price.toFixed(2).replace('.', ',')}
            </span>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={handleClick}
            className="ml-2"
          >
            {isKit ? 'Escolher' : 'Adicionar'}
          </Button>
        </div>
      </div>
    </div>
  )
}

