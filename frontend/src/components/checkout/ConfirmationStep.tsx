'use client'

import { useState, useEffect } from 'react'
import { Check, Copy, Download, MessageCircle, Home } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { Card, Button, Spinner } from '@/components/ui'
import { useCheckout } from '@/hooks/useCheckout'
import { useCart } from '@/hooks/useCart'
import { cn } from '@/lib/utils'

export function ConfirmationStep() {
  const router = useRouter()
  const { customerData, deliveryData, paymentMethod, reset } = useCheckout()
  const { clearCart, total } = useCart()
  const [isProcessing, setIsProcessing] = useState(true)
  const [orderNumber, setOrderNumber] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Simular processamento do pedido
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsProcessing(false)
      // Gerar número de pedido mock
      setOrderNumber(`#${Math.floor(Math.random() * 100000)}`)
      clearCart()
    }, 2000)

    return () => clearTimeout(timer)
  }, [clearCart])

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleBackToHome = () => {
    reset()
    router.push('/')
  }

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('pt-BR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
      })
    } catch {
      return dateString
    }
  }

  const formatAddress = () => {
    if (!customerData) return ''
    const { address } = customerData
    return `${address.street}, ${address.number}${
      address.complement ? ` - ${address.complement}` : ''
    }, ${address.neighborhood}, ${address.city} - ${address.state}, CEP: ${address.zipCode}`
  }

  if (isProcessing) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Spinner size="lg" className="mb-4" />
        <h2 className="text-xl font-semibold text-foreground mb-2">
          Processando seu pedido...
        </h2>
        <p className="text-foreground/70">Aguarde um momento</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Card de confirmação */}
      <Card variant="elevated" className="p-8 text-center">
        <div className="flex justify-center mb-4">
          <div className="rounded-full bg-green-100 p-4">
            <Check className="h-12 w-12 text-green-600" />
          </div>
        </div>
        <h2 className="text-3xl font-bold text-foreground mb-2">
          Pedido Confirmado!
        </h2>
        <p className="text-lg text-primary-600 font-semibold mb-6">
          {orderNumber}
        </p>

        {/* Resumo */}
        <div className="text-left max-w-md mx-auto space-y-2 mb-6">
          <div className="flex justify-between">
            <span className="text-foreground/70">Cliente:</span>
            <span className="font-medium">{customerData?.name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-foreground/70">Telefone:</span>
            <span className="font-medium">{customerData?.phone}</span>
          </div>
          {deliveryData && (
            <div className="flex justify-between">
              <span className="text-foreground/70">Entrega:</span>
              <span className="font-medium">
                {formatDate(deliveryData.date)}, pela manhã
              </span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-foreground/70">Endereço:</span>
            <span className="font-medium text-right max-w-xs">
              {formatAddress()}
            </span>
          </div>
          <div className="flex justify-between pt-2 border-t border-foreground/10">
            <span className="text-foreground/70">Total:</span>
            <span className="text-xl font-bold text-primary-600">
              R$ {total.toFixed(2).replace('.', ',')}
            </span>
          </div>
        </div>
      </Card>

      {/* Seção de Pagamento */}
      {paymentMethod && (
        <Card variant="elevated" className="p-6">
          <h3 className="text-xl font-semibold mb-4">
            Dados para Pagamento
          </h3>

          {paymentMethod === 'pix' && (
            <div className="space-y-4">
              <div className="bg-white rounded-lg p-4 border-2 border-dashed border-foreground/20 flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="mb-4">
                    <div className="inline-block bg-foreground/10 p-8 rounded">
                      <div className="grid grid-cols-8 gap-1">
                        {Array.from({ length: 64 }).map((_, i) => (
                          <div
                            key={i}
                            className={cn(
                              'w-2 h-2 rounded',
                              Math.random() > 0.5
                                ? 'bg-foreground'
                                : 'bg-transparent'
                            )}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-foreground/60 mb-4">
                    QR Code será gerado aqui
                  </p>
                  <div className="bg-foreground/5 rounded p-3 mb-2">
                    <p className="text-xs font-mono text-foreground/80 break-all">
                      00020126580014BR.GOV.BCB.PIX0136123e4567-e89b-12d3-a456-426614174000520400005303986540510.005802BR5925SITIO MULTITREM6009ABADIANIA62070503***6304
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      handleCopy(
                        '00020126580014BR.GOV.BCB.PIX0136123e4567-e89b-12d3-a456-426614174000520400005303986540510.005802BR5925SITIO MULTITREM6009ABADIANIA62070503***6304'
                      )
                    }
                    leftIcon={copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  >
                    {copied ? 'Copiado!' : 'Copiar código'}
                  </Button>
                </div>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-sm text-foreground/70">
                  ⏰ Expira em 30 minutos
                </p>
              </div>
              <p className="text-sm text-foreground/70">
                Após o pagamento, você receberá a confirmação no WhatsApp
              </p>
            </div>
          )}

          {paymentMethod === 'boleto' && (
            <div className="space-y-4">
              <div className="bg-white rounded-lg p-4 border-2 border-dashed border-foreground/20">
                <p className="text-xs font-mono text-foreground/80 mb-4 text-center">
                  34191.79001 01043.510047 91020.150008 1 9999000001000
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      handleCopy(
                        '34191.79001 01043.510047 91020.150008 1 9999000001000'
                      )
                    }
                    leftIcon={copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    className="flex-1"
                  >
                    {copied ? 'Copiado!' : 'Copiar código'}
                  </Button>
                  <Button variant="outline" size="sm" leftIcon={<Download className="h-4 w-4" />}>
                    Baixar Boleto
                  </Button>
                </div>
              </div>
              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-sm text-foreground/70">
                  📅 Vencimento: {new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toLocaleDateString('pt-BR')}
                </p>
              </div>
            </div>
          )}

          {paymentMethod === 'cartao' && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded p-4 text-center">
                <Check className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <p className="font-semibold text-foreground mb-1">
                  Pagamento aprovado!
                </p>
                <p className="text-sm text-foreground/70">
                  Cartão finalizado em **** 1234
                </p>
              </div>
              <p className="text-xs text-foreground/60 text-center">
                * Por enquanto é apenas visual. Integração real será na FASE 2
              </p>
            </div>
          )}
        </Card>
      )}

      {/* Ações finais */}
      <div className="flex flex-col sm:flex-row gap-4">
        <a
          href={`https://wa.me/5562981225993?text=Olá! Meu pedido é ${orderNumber}. Gostaria de acompanhar o status.`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1"
        >
          <Button
            variant="primary"
            size="lg"
            leftIcon={<MessageCircle className="h-5 w-5" />}
            className="w-full"
          >
            Acompanhar no WhatsApp
          </Button>
        </a>
        <Button
          variant="outline"
          size="lg"
          leftIcon={<Home className="h-5 w-5" />}
          onClick={handleBackToHome}
          className="flex-1"
        >
          Voltar para Loja
        </Button>
      </div>
    </div>
  )
}

