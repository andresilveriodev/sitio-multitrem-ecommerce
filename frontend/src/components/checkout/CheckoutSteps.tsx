import { User, Truck, CreditCard, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

const steps = [
  { number: 1, label: 'Dados', icon: User },
  { number: 2, label: 'Entrega', icon: Truck },
  { number: 3, label: 'Pagamento', icon: CreditCard },
  { number: 4, label: 'Confirmação', icon: Check },
]

export interface CheckoutStepsProps {
  currentStep: number
}

export function CheckoutSteps({ currentStep }: CheckoutStepsProps) {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const Icon = step.icon
          const isActive = currentStep === step.number
          const isCompleted = currentStep > step.number
          const isLast = index === steps.length - 1

          return (
            <div key={step.number} className="flex items-center flex-1">
              {/* Step Circle */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all',
                    isCompleted &&
                      'bg-primary-600 border-primary-600 text-white',
                    isActive &&
                      !isCompleted &&
                      'bg-primary-100 border-primary-600 text-primary-600',
                    !isActive &&
                      !isCompleted &&
                      'bg-background border-foreground/20 text-foreground/40'
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-6 w-6" />
                  ) : (
                    <Icon className="h-6 w-6" />
                  )}
                </div>
                <span
                  className={cn(
                    'mt-2 text-xs font-medium',
                    isActive || isCompleted
                      ? 'text-foreground'
                      : 'text-foreground/40'
                  )}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector Line */}
              {!isLast && (
                <div
                  className={cn(
                    'flex-1 h-0.5 mx-4 transition-all',
                    isCompleted ? 'bg-primary-600' : 'bg-foreground/20'
                  )}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

