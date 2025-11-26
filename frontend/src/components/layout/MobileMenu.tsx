'use client'

import { X } from 'lucide-react'
import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui'

export interface MobileMenuProps {
  isOpen: boolean
  onClose: () => void
  children: ReactNode
}

export function MobileMenu({ isOpen, onClose, children }: MobileMenuProps) {
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Drawer */}
      <div
        className={cn(
          'fixed left-0 top-0 z-50 h-full w-80 bg-background shadow-xl transition-transform duration-300 ease-in-out',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Menu de navegação"
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-foreground/10 px-6 py-4">
            <h2 className="text-lg font-semibold">Menu</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              aria-label="Fechar menu"
              className="h-8 w-8 p-0"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Content */}
          <nav className="flex-1 overflow-y-auto px-6 py-4">{children}</nav>
        </div>
      </div>
    </>
  )
}

