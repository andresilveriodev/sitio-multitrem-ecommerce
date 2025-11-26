'use client'

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from 'react'
import type { Address, DeliveryDay, PaymentMethod } from '@/types'

export interface CustomerData {
  name: string
  phone: string
  email?: string
  address: Address
}

export interface DeliveryData {
  date: string
  dayOfWeek: DeliveryDay
  period: 'manha'
}

interface CheckoutContextType {
  currentStep: number
  customerData: CustomerData | null
  deliveryData: DeliveryData | null
  paymentMethod: PaymentMethod | null
  setCurrentStep: (step: number) => void
  setCustomerData: (data: CustomerData) => void
  setDeliveryData: (data: DeliveryData) => void
  setPaymentMethod: (method: PaymentMethod) => void
  nextStep: () => void
  previousStep: () => void
  reset: () => void
}

const CheckoutContext = createContext<CheckoutContextType | undefined>(
  undefined
)

export function CheckoutProvider({ children }: { children: ReactNode }) {
  const [currentStep, setCurrentStep] = useState(1)
  const [customerData, setCustomerData] = useState<CustomerData | null>(null)
  const [deliveryData, setDeliveryData] = useState<DeliveryData | null>(null)
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | null>(
    null
  )

  const nextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1)
    }
  }

  const previousStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const reset = () => {
    setCurrentStep(1)
    setCustomerData(null)
    setDeliveryData(null)
    setPaymentMethod(null)
  }

  return (
    <CheckoutContext.Provider
      value={{
        currentStep,
        customerData,
        deliveryData,
        paymentMethod,
        setCurrentStep,
        setCustomerData,
        setDeliveryData,
        setPaymentMethod,
        nextStep,
        previousStep,
        reset,
      }}
    >
      {children}
    </CheckoutContext.Provider>
  )
}

export function useCheckout() {
  const context = useContext(CheckoutContext)
  if (context === undefined) {
    throw new Error('useCheckout must be used within a CheckoutProvider')
  }
  return context
}

