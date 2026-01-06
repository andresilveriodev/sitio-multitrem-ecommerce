import { cn } from '@/lib/utils'
import styles from './Skeleton.module.css'

export interface SkeletonProps {
  variant?: 'text' | 'heading' | 'card' | 'image' | 'avatar' | 'button' | 'product'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

export function Skeleton({ variant = 'text', size, className }: SkeletonProps) {
  return (
    <div
      className={cn(
        styles.skeleton,
        styles[`skeleton--${variant}`],
        size && styles[`skeleton--${size}`],
        className
      )}
      aria-busy="true"
      aria-label="Carregando..."
    />
  )
}

