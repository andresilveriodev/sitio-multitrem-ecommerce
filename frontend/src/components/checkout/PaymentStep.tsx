'use client'

import { useState } from 'react'
import { QrCode, Barcode, CreditCard } from 'lucide-react'
import { Card, Button, Badge } from '@/components/ui'
import { useCheckout } from '@/hooks/useCheckout'
import { useCart } from '@/hooks/useCart'
import { cn } from '@/lib/utils'
import type { PaymentMethod } from '@/types'

const paymentMethods: Array<{
  method: PaymentMethod
  label: string
  icon: typeof QrCode
  description: string
  badge?: string
}> = [
  {
    method: 'pix',
    label: 'Pix',
    icon: QrCode,
    description: 'Aprovação instantânea',
    badge: '5% de desconto',
  },
  {
    method: 'boleto',
    label: 'Boleto Bancário',
    icon: Barcode,
    description: 'Vencimento em 3 dias',
  },
  {
    method: 'cartao',
    label: 'Cartão de Crédito',
    icon: CreditCard,
    description: 'Parcele em até 3x',
  },
]

export function PaymentStep() {
  const { paymentMethod, setPaymentMethod, nextStep, previousStep } =
    useCheckout()
  const { total } = useCart()
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod | null>(
    paymentMethod
  )

  const handleMethodSelect = (method: PaymentMethod) => {
    setSelectedMethod(method)
  }

  const handleContinue = () => {
    if (!selectedMethod) return

    setPaymentMethod(selectedMethod)
    nextStep()
  }

  const calculateDiscount = () => {
    if (selectedMethod === 'pix') {
      return total * 0.05
    }
    return 0
  }

  const finalTotal = total - calculateDiscount()

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Como deseja pagar?
        </h2>
        <p className="text-foreground/70">
          Escolha a forma de pagamento mais conveniente
        </p>
      </div>

      {/* Cards de métodos de pagamento */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {paymentMethods.map((method) => {
          const Icon = method.icon
          const isSelected = selectedMethod === method.method

          return (
            <button
              key={method.method}
              onClick={() => handleMethodSelect(method.method)}
              className={cn(
                'relative p-6 rounded-lg border-2 transition-all text-left',
                isSelected
                  ? 'border-primary-600 bg-primary-50'
                  : 'border-foreground/20 hover:border-primary-300 hover:bg-primary-50/50',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
              )}
            >
              {method.badge && (
                <Badge
                  variant="success"
                  size="sm"
                  className="absolute top-2 right-2"
                >
                  {method.badge}
                </Badge>
              )}
              <div className="flex items-start gap-4">
                <div
                  className={cn(
                    'rounded-full p-3',
                    isSelected ? 'bg-primary-600' : 'bg-primary-100'
                  )}
                >
                  <Icon
                    className={cn(
                      'h-6 w-6',
                      isSelected ? 'text-white' : 'text-primary-600'
                    )}
                  />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-foreground mb-1">
                    {method.label}
                  </h3>
                  <p className="text-sm text-foreground/70">
                    {method.description}
                  </p>
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Área expandida para método selecionado */}
      {selectedMethod && (
        <Card variant="bordered" className="p-6 bg-primary-50/30">
          {selectedMethod === 'pix' && (
            <div>
              <h3 className="font-semibold text-foreground mb-2">
                Pagamento via Pix
              </h3>
              <p className="text-sm text-foreground/70 mb-4">
                O QR Code será gerado após confirmar o pedido
              </p>
              <div className="bg-white rounded-lg p-4 border-2 border-dashed border-foreground/20 flex items-center justify-center h-48">
                <div className="text-center">
                  <QrCode className="h-16 w-16 text-foreground/20 mx-auto mb-2" />
                  <p className="text-sm text-foreground/60">
                    QR Code aparecerá aqui
                  </p>
                </div>
              </div>
            </div>
          )}

          {selectedMethod === 'boleto' && (
            <div>
              <h3 className="font-semibold text-foreground mb-2">
                Pagamento via Boleto
              </h3>
              <p className="text-sm text-foreground/70 mb-2">
                O boleto será gerado após confirmar o pedido
              </p>
              <p className="text-xs text-foreground/60 bg-yellow-50 border border-yellow-200 rounded p-3">
                ⚠️ Pagamentos em boleto podem levar até 3 dias para compensar
              </p>
            </div>
          )}

          {selectedMethod === 'cartao' && (
            <div>
              <h3 className="font-semibold text-foreground mb-2">
                Pagamento via Cartão
              </h3>
              <p className="text-sm text-foreground/70">
                Você será redirecionado para pagamento seguro do Mercado Pago
              </p>
              <p className="text-xs text-foreground/60 mt-2">
                * Integração com Mercado Pago será implementada na FASE 2
              </p>
            </div>
          )}
        </Card>
      )}

      {/* Resumo do pedido */}
      <Card variant="elevated" className="p-6">
        <h3 className="font-semibold text-foreground mb-4">
          Resumo do Pedido
        </h3>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-foreground/70">Subtotal:</span>
            <span className="text-foreground">
              R$ {total.toFixed(2).replace('.', ',')}
            </span>
          </div>
          {selectedMethod === 'pix' && (
            <div className="flex justify-between text-sm text-green-600">
              <span>Desconto Pix (5%):</span>
              <span>- R$ {calculateDiscount().toFixed(2).replace('.', ',')}</span>
            </div>
          )}
          <div className="flex justify-between text-lg font-bold pt-2 border-t border-foreground/10">
            <span>Total:</span>
            <span className="text-primary-600">
              R$ {finalTotal.toFixed(2).replace('.', ',')}
            </span>
          </div>
        </div>
      </Card>

      {/* Botões */}
      <div className="flex justify-between gap-4 pt-4">
        <Button variant="outline" onClick={previousStep} size="lg">
          Voltar
        </Button>
        <Button
          variant="primary"
          onClick={handleContinue}
          disabled={!selectedMethod}
          size="lg"
        >
          Confirmar Pedido
        </Button>
      </div>
    </div>
  )
}

