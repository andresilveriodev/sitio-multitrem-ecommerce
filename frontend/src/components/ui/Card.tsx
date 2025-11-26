import { type ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface CardProps {
  children: ReactNode
  className?: string
  variant?: 'default' | 'elevated' | 'bordered'
  header?: ReactNode
  footer?: ReactNode
}

export function Card({
  children,
  className,
  variant = 'default',
  header,
  footer,
}: CardProps) {
  const baseStyles = 'rounded-lg bg-background'

  const variants = {
    default: 'border border-foreground/10',
    elevated: 'shadow-lg',
    bordered: 'border-2 border-primary-200',
  }

  return (
    <div className={cn(baseStyles, variants[variant], className)}>
      {header && (
        <div className="border-b border-foreground/10 px-6 py-4">
          {header}
        </div>
      )}
      <div className={cn('px-6 py-4', header && 'pt-6', footer && 'pb-6')}>
        {children}
      </div>
      {footer && (
        <div className="border-t border-foreground/10 px-6 py-4">
          {footer}
        </div>
      )}
    </div>
  )
}

