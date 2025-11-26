'use client'

import { Leaf, Egg, Package, Gift, Grid3x3 } from 'lucide-react'
import type { ProductCategory } from '@/types'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'

const categories: Array<{
  value: ProductCategory | 'all'
  label: string
  icon: typeof Leaf
}> = [
  { value: 'all', label: 'Todos', icon: Grid3x3 },
  { value: 'hortalica', label: 'Hortaliças', icon: Leaf },
  { value: 'ovos', label: 'Ovos', icon: Egg },
  { value: 'kit', label: 'Kits', icon: Package },
  { value: 'combo', label: 'Combos', icon: Gift },
]

export interface CategoryTabsProps {
  selectedCategory: ProductCategory | 'all'
  onCategoryChange: (category: ProductCategory | 'all') => void
}

export function CategoryTabs({
  selectedCategory,
  onCategoryChange,
}: CategoryTabsProps) {
  return (
    <div className="flex flex-wrap gap-2 justify-center mb-8">
      {categories.map((category) => {
        const Icon = category.icon
        const isActive = selectedCategory === category.value

        return (
          <Button
            key={category.value}
            variant={isActive ? 'primary' : 'outline'}
            size="sm"
            onClick={() => onCategoryChange(category.value)}
            leftIcon={<Icon className="h-4 w-4" />}
            className={cn(
              'transition-all',
              isActive && 'shadow-md'
            )}
          >
            {category.label}
          </Button>
        )
      })}
    </div>
  )
}

