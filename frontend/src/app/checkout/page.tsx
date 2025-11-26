'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useCart } from '@/hooks/useCart'
import { CheckoutProvider, useCheckout } from '@/contexts/CheckoutContext'
import { Header } from '@/components/layout/Header'
import { CheckoutSteps } from '@/components/checkout/CheckoutSteps'
import { OrderSummary } from '@/components/checkout/OrderSummary'
import { CustomerDataStep } from '@/components/checkout/CustomerDataStep'
import { DeliveryStep } from '@/components/checkout/DeliveryStep'
import { PaymentStep } from '@/components/checkout/PaymentStep'
import { ConfirmationStep } from '@/components/checkout/ConfirmationStep'

function CheckoutContent() {
  const router = useRouter()
  const { isEmpty } = useCart()
  const { currentStep } = useCheckout()

  // Redirecionar se carrinho vazio
  useEffect(() => {
    if (isEmpty) {
      router.push('/')
    }
  }, [isEmpty, router])

  if (isEmpty) {
    return null
  }

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <CustomerDataStep />
      case 2:
        return <DeliveryStep />
      case 3:
        return <PaymentStep />
      case 4:
        return <ConfirmationStep />
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="pt-16">
        <div className="container-custom py-8">
          {/* Header simplificado */}
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-foreground">
              Finalizar Pedido
            </h1>
            <p className="mt-2 text-foreground/70">
              Complete seus dados para receber seus produtos fresquinhos
            </p>
          </div>

          {/* Steps */}
          <CheckoutSteps currentStep={currentStep} />

          {/* Conteúdo principal */}
          <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Formulário (2/3) */}
            <div className="lg:col-span-2">{renderStepContent()}</div>

            {/* Resumo (1/3) */}
            <div className="lg:col-span-1">
              <OrderSummary />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function CheckoutPage() {
  return (
    <CheckoutProvider>
      <CheckoutContent />
    </CheckoutProvider>
  )
}

