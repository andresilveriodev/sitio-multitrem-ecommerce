import { forwardRef, useId, type InputHTMLAttributes, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  leftIcon?: ReactNode
  variant?: 'default' | 'error'
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    { className, label, error, leftIcon, variant, id, ...props },
    ref
  ) => {
    const generatedId = useId()
    const inputId = id || generatedId
    const hasError = error || variant === 'error'

    const baseStyles =
      'flex h-11 w-full rounded-lg border bg-background px-3 py-2 text-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'

    const variants = {
      default:
        'border-foreground/20 focus-visible:ring-primary-500 focus-visible:border-primary-500',
      error:
        'border-red-500 focus-visible:ring-red-500 focus-visible:border-red-500',
    }

    // Remover aria-invalid dos props se existir para evitar conflito
    const { 'aria-invalid': _, ...restProps } = props

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="mb-2 block text-sm font-medium text-foreground"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground/60">
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              baseStyles,
              variants[hasError ? 'error' : 'default'],
              leftIcon && 'pl-10',
              className
            )}
            aria-invalid={hasError ? true : undefined}
            aria-describedby={hasError ? `${inputId}-error` : undefined}
            {...restProps}
          />
        </div>
        {error && (
          <p
            id={`${inputId}-error`}
            className="mt-1 text-sm text-red-500"
            role="alert"
          >
            {error}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

