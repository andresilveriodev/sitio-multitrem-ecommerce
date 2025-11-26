import { cn } from '@/lib/utils'

export interface SkeletonProps {
  variant?: 'text' | 'card' | 'image'
  className?: string
}

export function Skeleton({ variant = 'text', className }: SkeletonProps) {
  const baseStyles = 'animate-pulse rounded bg-foreground/10'

  const variants = {
    text: 'h-4 w-full',
    card: 'h-32 w-full',
    image: 'aspect-square w-full',
  }

  return (
    <div
      className={cn(baseStyles, variants[variant], className)}
      aria-busy="true"
      aria-label="Carregando..."
    />
  )
}

