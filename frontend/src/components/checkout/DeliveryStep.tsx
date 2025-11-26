'use client'

import { useState } from 'react'
import { Calendar, Clock } from 'lucide-react'
import { Card, Button } from '@/components/ui'
import { useCheckout } from '@/hooks/useCheckout'
import { getAvailableDeliveryDays } from '@/lib/mock-data'
import { cn } from '@/lib/utils'
import type { DeliveryDay } from '@/types'

const dayNames: Record<number, DeliveryDay> = {
  3: 'quarta',
  4: 'quinta',
  5: 'sexta',
  6: 'sabado',
}

const dayLabels: Record<DeliveryDay, string> = {
  quarta: 'Quarta',
  quinta: 'Quinta',
  sexta: 'Sexta',
  sabado: 'Sábado',
}

const monthNames = [
  'Jan',
  'Fev',
  'Mar',
  'Abr',
  'Mai',
  'Jun',
  'Jul',
  'Ago',
  'Set',
  'Out',
  'Nov',
  'Dez',
]

export function DeliveryStep() {
  const { deliveryData, setDeliveryData, nextStep, previousStep } =
    useCheckout()
  const [selectedDate, setSelectedDate] = useState<Date | null>(
    deliveryData ? new Date(deliveryData.date) : null
  )

  const availableDays = getAvailableDeliveryDays()

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date)
  }

  const handleContinue = () => {
    if (!selectedDate) return

    const dayOfWeek = selectedDate.getDay()
    const deliveryDay = dayNames[dayOfWeek] as DeliveryDay

    setDeliveryData({
      date: selectedDate.toISOString().split('T')[0],
      dayOfWeek: deliveryDay,
      period: 'manha',
    })

    nextStep()
  }

  const formatDate = (date: Date): string => {
    const day = date.getDate()
    const month = monthNames[date.getMonth()]
    const dayOfWeek = dayNames[date.getDay()] as DeliveryDay
    return `${dayLabels[dayOfWeek]}, ${day}/${month}`
  }

  const formatFullDate = (date: Date): string => {
    const day = date.getDate()
    const month = date.toLocaleDateString('pt-BR', { month: 'long' })
    const dayOfWeek = dayNames[date.getDay()] as DeliveryDay
    return `${dayLabels[dayOfWeek]}-feira, ${day} de ${month}`
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Quando deseja receber?
        </h2>
        <p className="text-foreground/70">
          Escolha o melhor dia para receber seus produtos fresquinhos
        </p>
      </div>

      {/* Calendário de dias disponíveis */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Dias Disponíveis</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-3">
          {availableDays.map((date) => {
            const isSelected =
              selectedDate?.toDateString() === date.toDateString()

            return (
              <button
                key={date.toISOString()}
                onClick={() => handleDateSelect(date)}
                className={cn(
                  'p-4 rounded-lg border-2 transition-all text-center',
                  isSelected
                    ? 'border-primary-600 bg-primary-50 text-primary-700'
                    : 'border-foreground/20 hover:border-primary-300 hover:bg-primary-50/50',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
                )}
              >
                <div className="text-xs text-foreground/60 mb-1">
                  {dayLabels[dayNames[date.getDay()] as DeliveryDay]}
                </div>
                <div className="text-lg font-semibold">{date.getDate()}</div>
                <div className="text-xs text-foreground/60">
                  {monthNames[date.getMonth()]}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Informações de entrega */}
      <Card variant="elevated" className="p-6">
        <div className="flex items-start gap-4">
          <div className="rounded-full bg-primary-100 p-3">
            <Clock className="h-6 w-6 text-primary-600" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground mb-2">
              Período: Manhã (8h às 12h)
            </h3>
            <p className="text-sm text-foreground/70">
              Você receberá uma mensagem no WhatsApp quando sairmos para
              entrega
            </p>
          </div>
        </div>
      </Card>

      {/* Resumo da seleção */}
      {selectedDate && (
        <Card variant="bordered" className="p-4 bg-primary-50/30">
          <div className="flex items-center gap-3">
            <Calendar className="h-5 w-5 text-primary-600" />
            <div>
              <p className="text-sm text-foreground/70">Entrega agendada:</p>
              <p className="font-semibold text-foreground">
                {formatFullDate(selectedDate)}, pela manhã
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Botões */}
      <div className="flex justify-between gap-4 pt-4">
        <Button variant="outline" onClick={previousStep} size="lg">
          Voltar
        </Button>
        <Button
          variant="primary"
          onClick={handleContinue}
          disabled={!selectedDate}
          size="lg"
        >
          Continuar
        </Button>
      </div>
    </div>
  )
}

