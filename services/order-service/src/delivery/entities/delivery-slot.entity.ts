import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm'

@Entity('delivery_slots')
export class DeliverySlot {
  @PrimaryGeneratedColumn()
  id: number

  @Column({ type: 'date', unique: true })
  date: string

  @Column({ type: 'int' })
  dayOfWeek: number // 3=qua, 4=qui, 5=sex, 6=sab

  @Column({ type: 'varchar', length: 50 })
  period: string

  @Column({ type: 'int', default: 10 })
  maxOrders: number

  @Column({ type: 'int', default: 0 })
  currentOrders: number

  @Column({ type: 'boolean', default: true })
  active: boolean

  @CreateDateColumn()
  createdAt: Date

  @UpdateDateColumn()
  updatedAt: Date
}

