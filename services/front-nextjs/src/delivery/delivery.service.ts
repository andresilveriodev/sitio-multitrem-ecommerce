import { Injectable } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { DeliverySlot } from './entities/delivery-slot.entity'

@Injectable()
export class DeliveryService {
  constructor(
    @InjectRepository(DeliverySlot)
    private readonly deliverySlotRepository: Repository<DeliverySlot>,
  ) {}

  private getDayOfWeek(date: Date): number {
    return date.getDay() // 0=dom, 1=seg, 2=ter, 3=qua, 4=qui, 5=sex, 6=sab
  }

  private isAvailableDay(dayOfWeek: number): boolean {
    return dayOfWeek >= 3 && dayOfWeek <= 6 // qua, qui, sex, sab
  }

  private formatDate(date: Date): string {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  async getAvailableSlots(): Promise<DeliverySlot[]> {
    const slots: DeliverySlot[] = []
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    // Gerar próximos 14 dias
    for (let i = 0; i < 14; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      const dayOfWeek = this.getDayOfWeek(date)

      // Filtrar apenas qua, qui, sex, sab
      if (!this.isAvailableDay(dayOfWeek)) {
        continue
      }

      const dateStr = this.formatDate(date)

      // Verificar se slot já existe
      let slot = await this.deliverySlotRepository.findOne({
        where: { date: dateStr },
      })

      // Verificar slots para manhã e tarde
      const morningSlot = await this.deliverySlotRepository.findOne({
        where: { date: dateStr, period: 'manhã' },
      })

      const afternoonSlot = await this.deliverySlotRepository.findOne({
        where: { date: dateStr, period: 'tarde' },
      })

      // Criar slot manhã se não existir
      if (!morningSlot) {
        const newMorningSlot = this.deliverySlotRepository.create({
          date: dateStr,
          dayOfWeek,
          period: 'manhã',
          maxOrders: 10,
          currentOrders: 0,
          active: true,
        })
        await this.deliverySlotRepository.save(newMorningSlot)
        if (newMorningSlot.currentOrders < newMorningSlot.maxOrders) {
          slots.push(newMorningSlot)
        }
      } else if (morningSlot.currentOrders < morningSlot.maxOrders) {
        slots.push(morningSlot)
      }

      // Criar slot tarde se não existir
      if (!afternoonSlot) {
        const newAfternoonSlot = this.deliverySlotRepository.create({
          date: dateStr,
          dayOfWeek,
          period: 'tarde',
          maxOrders: 10,
          currentOrders: 0,
          active: true,
        })
        await this.deliverySlotRepository.save(newAfternoonSlot)
        if (newAfternoonSlot.currentOrders < newAfternoonSlot.maxOrders) {
          slots.push(newAfternoonSlot)
        }
      } else if (afternoonSlot.currentOrders < afternoonSlot.maxOrders) {
        slots.push(afternoonSlot)
      }
    }

    return slots.sort((a, b) => a.date.localeCompare(b.date))
  }

  async checkAvailability(date: string): Promise<DeliverySlot[]> {
    const slots = await this.deliverySlotRepository.find({
      where: { date, active: true },
    })

    return slots.filter((slot) => slot.currentOrders < slot.maxOrders)
  }
}

