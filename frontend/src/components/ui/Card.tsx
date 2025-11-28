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
    default: 'border border-gray-200',
    elevated: 'shadow-lg hover:shadow-xl transition-shadow',
    bordered: 'border-2 border-primary-200',
  }

  return (
    <div className={cn(baseStyles, variants[variant], className)}>
      {header && (
        <div className="border-b border-gray-200 px-6 py-5 sm:px-8 sm:py-6">
          {header}
        </div>
      )}
      <div className={cn('p-5 sm:p-6 md:p-8', header && 'pt-6 sm:pt-8', footer && 'pb-6 sm:pb-8')}>
        {children}
      </div>
      {footer && (
        <div className="border-t border-gray-200 px-6 py-5 sm:px-8 sm:py-6">
          {footer}
        </div>
      )}
    </div>
  )
}

