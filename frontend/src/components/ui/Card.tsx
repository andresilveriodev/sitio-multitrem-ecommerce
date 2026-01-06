import { type ReactNode, type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'
import styles from './Card.module.css'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  className?: string
  variant?: 'default' | 'elevated' | 'bordered' | 'flat' | 'product'
  header?: ReactNode
  footer?: ReactNode
  loading?: boolean
  clickable?: boolean
}

export function Card({
  children,
  className,
  variant = 'default',
  header,
  footer,
  loading = false,
  clickable = false,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        styles.card,
        styles[`card--${variant}`],
        loading && styles['card--loading'],
        clickable && styles['card--clickable'],
        className
      )}
      {...props}
    >
      {header && (
        <div className={styles.card__header}>
          {header}
        </div>
      )}
      <div className={styles.card__body}>
        {children}
      </div>
      {footer && (
        <div className={styles.card__footer}>
          {footer}
        </div>
      )}
    </div>
  )
}

// Componentes auxiliares para facilitar a composição
Card.Image = function CardImage({ src, alt, className }: { src: string; alt: string; className?: string }) {
  return (
    <div className={cn(styles.card__image, className)}>
      <img src={src} alt={alt} />
    </div>
  )
}

Card.Badges = function CardBadges({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn(styles.card__badges, className)}>
      {children}
    </div>
  )
}

Card.Content = function CardContent({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn(styles.card__content, className)}>
      {children}
    </div>
  )
}

Card.Title = function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <h3 className={cn(styles.card__title, className)}>
      {children}
    </h3>
  )
}

Card.Description = function CardDescription({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <p className={cn(styles.card__description, className)}>
      {children}
    </p>
  )
}

Card.Price = function CardPrice({ 
  current, 
  old, 
  className 
}: { 
  current: string; 
  old?: string; 
  className?: string 
}) {
  return (
    <div className={cn(styles.card__price, className)}>
      <span className={styles.card__price_current}>{current}</span>
      {old && <span className={styles.card__price_old}>{old}</span>}
    </div>
  )
}

Card.Actions = function CardActions({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn(styles.card__actions, className)}>
      {children}
    </div>
  )
}

