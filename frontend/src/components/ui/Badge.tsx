import { type ReactNode } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'
import styles from './Badge.module.css'

export interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'organic' | 'discount' | 'new' | 'neutral'
  size?: 'sm' | 'md' | 'lg'
  dot?: boolean
  removable?: boolean
  onRemove?: () => void
  className?: string
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  removable = false,
  onRemove,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        styles.badge,
        styles[`badge--${variant}`],
        styles[`badge--${size}`],
        dot && styles['badge--dot'],
        removable && styles['badge--removable'],
        className
      )}
    >
      {children}
      {removable && onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className={styles.badge__remove}
          aria-label="Remover"
        >
          <X size={12} />
        </button>
      )}
    </span>
  )
}

