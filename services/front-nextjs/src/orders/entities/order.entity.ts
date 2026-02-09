import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
} from 'typeorm'
import { OrderItem } from './order-item.entity'
import { OrderStatus, PaymentStatus, PaymentMethod } from '@sitio/shared'

@Entity('orders')
export class Order {
  @PrimaryGeneratedColumn()
  id: number

  @Column({ type: 'varchar', length: 100 })
  visitorId: string

  @Column({ type: 'int', nullable: true })
  customerId: number | null

  @Column({
    type: 'varchar',
    length: 20,
    default: 'pending',
  })
  status: OrderStatus

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  total: number

  @Column({ type: 'date' })
  deliveryDate: string

  @Column({ type: 'varchar', length: 50 })
  deliveryPeriod: string

  @Column({
    type: 'varchar',
    length: 20,
  })
  paymentMethod: PaymentMethod

  @Column({
    type: 'varchar',
    length: 20,
    default: 'pending',
  })
  paymentStatus: PaymentStatus

  @Column({ type: 'varchar', length: 100 })
  customerName: string

  @Column({ type: 'varchar', length: 20 })
  customerPhone: string

  @Column({ type: 'varchar', length: 200 })
  customerAddress: string

  @Column({ type: 'varchar', length: 10, nullable: true })
  customerCep: string | null

  @Column({ type: 'varchar', length: 100, nullable: true })
  customerCity: string | null

  @Column({ type: 'varchar', length: 2, nullable: true })
  customerState: string | null

  @OneToMany(() => OrderItem, (item) => item.order, { cascade: true })
  items: OrderItem[]

  @CreateDateColumn()
  createdAt: Date

  @UpdateDateColumn()
  updatedAt: Date
}

