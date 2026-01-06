import { type ReactNode } from 'react'
import { X, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import styles from './Chip.module.css'

export interface ChipProps {
  children: ReactNode
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error'
  size?: 'sm' | 'md' | 'lg'
  selected?: boolean
  removable?: boolean
  onRemove?: () => void
  onClick?: () => void
  className?: string
}

export function Chip({
  children,
  variant = 'default',
  size = 'md',
  selected = false,
  removable = false,
  onRemove,
  onClick,
  className,
}: ChipProps) {
  const Component = onClick ? 'button' : 'span'
  
  return (
    <Component
      type={onClick ? 'button' : undefined}
      onClick={onClick}
      className={cn(
        styles.chip,
        styles[`chip--${variant}`],
        styles[`chip--${size}`],
        selected && styles['chip--selected'],
        onClick && styles['chip--clickable'],
        className
      )}
    >
      {selected && (
        <Check className={styles.chip__icon} size={14} />
      )}
      <span className={styles.chip__label}>{children}</span>
      {removable && onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          className={styles.chip__remove}
          aria-label="Remover"
        >
          <X size={14} />
        </button>
      )}
    </Component>
  )
}

