'use client'

import { useState } from 'react'
import { Check } from 'lucide-react'
import type { KitProduct } from '@/types'
import { AVAILABLE_VEGETABLES } from '@/lib/mock-data'
import { Modal, Button, Badge } from '@/components/ui'
import { cn } from '@/lib/utils'

export interface KitSelectionModalProps {
  isOpen: boolean
  onClose: () => void
  product: KitProduct | null
  onConfirm: (selectedItems: string[]) => void
}

export function KitSelectionModal({
  isOpen,
  onClose,
  product,
  onConfirm,
}: KitSelectionModalProps) {
  const [selectedItems, setSelectedItems] = useState<string[]>([])

  if (!product) return null

  const handleToggleItem = (item: string) => {
    if (selectedItems.includes(item)) {
      setSelectedItems(selectedItems.filter((i) => i !== item))
    } else {
      if (selectedItems.length < product.kitSize) {
        setSelectedItems([...selectedItems, item])
      }
    }
  }

  const handleConfirm = () => {
    if (selectedItems.length === product.kitSize) {
      onConfirm(selectedItems)
      setSelectedItems([])
      onClose()
    }
  }

  const isComplete = selectedItems.length === product.kitSize

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={product.name}
      size="md"
    >
      <div className="space-y-6">
        {/* Subtítulo e contador */}
        <div>
          <p className="text-sm text-foreground/70 mb-2">
            Escolha {product.kitSize} hortaliças
          </p>
          <div className="flex items-center gap-2">
            <Badge
              variant={isComplete ? 'success' : 'default'}
              size="sm"
            >
              {selectedItems.length} de {product.kitSize} selecionadas
            </Badge>
          </div>
        </div>

        {/* Lista de hortaliças */}
        <div className="grid grid-cols-2 gap-3 max-h-64 overflow-y-auto">
          {AVAILABLE_VEGETABLES.map((vegetable) => {
            const isSelected = selectedItems.includes(vegetable)
            const isDisabled =
              !isSelected && selectedItems.length >= product.kitSize

            return (
              <button
                key={vegetable}
                onClick={() => handleToggleItem(vegetable)}
                disabled={isDisabled}
                className={cn(
                  'relative flex items-center justify-between rounded-lg border-2 p-3 text-left transition-all',
                  isSelected
                    ? 'border-primary-600 bg-primary-50'
                    : 'border-foreground/20 hover:border-primary-300',
                  isDisabled && 'opacity-50 cursor-not-allowed'
                )}
              >
                <span className="text-sm font-medium text-foreground">
                  {vegetable}
                </span>
                {isSelected && (
                  <div className="flex-shrink-0 ml-2">
                    <div className="rounded-full bg-primary-600 p-1">
                      <Check className="h-3 w-3 text-white" />
                    </div>
                  </div>
                )}
              </button>
            )
          })}
        </div>

        {/* Resumo e ações */}
        <div className="border-t border-foreground/10 pt-4 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-foreground/70">Total:</span>
            <span className="text-xl font-bold text-primary-600">
              R$ {product.price.toFixed(2).replace('.', ',')}
            </span>
          </div>

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirm}
              disabled={!isComplete}
              className="flex-1"
            >
              Adicionar ao Carrinho
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  )
}

