'use client'

import Image from 'next/image'
import { useState } from 'react'
import { Leaf, Egg, Package, Gift } from 'lucide-react'
import type { Product, KitProduct } from '@/types'
import { Button } from '@/components/ui'
import styles from './ProductCard.module.css'

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
  const [imageError, setImageError] = useState(false)

  const handleClick = () => {
    if (isKit && onSelectKit) {
      onSelectKit(product as KitProduct)
    } else if (onAddToCart) {
      onAddToCart(product)
    }
  }

  return (
    <div className={styles.card}>
      {/* Imagem */}
      <div className={styles.card__image}>
        {product.imageUrl && !imageError ? (
          <Image 
            src={product.imageUrl} 
            alt={product.name} 
            fill 
            className={styles.card__image}
            onError={() => {
              console.error('Erro ao carregar imagem:', product.imageUrl)
              setImageError(true)
            }}
            unoptimized={product.imageUrl?.startsWith('/images/')}
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        ) : (
          <div className={styles.card__image_placeholder}>
            <Icon className={styles.card__image_icon} />
          </div>
        )}

        {/* Badge de categoria */}
        <div className={styles.card__badge}>
          <div className={styles.card__badge_content}>
            <Icon className={styles.card__badge_icon} />
            {categoryLabels[product.category]}
          </div>
        </div>
      </div>

      {/* Conteúdo */}
      <div className={styles.card__content}>
        <div className={styles.card__info}>
          <h3 className={styles.card__title}>{product.name}</h3>

          {product.description && <p className={styles.card__description}>{product.description}</p>}

          {isKit && (product as KitProduct).kitSize && (
            <p className={styles.card__kit_info}>{(product as KitProduct).kitSize} hortaliças à escolha</p>
          )}
        </div>

        {/* Preço e botão */}
        <div className={styles.card__footer}>
          <div className={styles.card__price}>
            <span className={styles.card__price_value}>{product.price.toFixed(2).replace('.', ',')}</span>
          </div>
          <Button variant="primary" size="sm" onClick={handleClick} className={styles.card__button}>
            {isKit ? 'Escolher' : 'Adicionar'}
          </Button>
        </div>
      </div>
    </div>
  )
}

