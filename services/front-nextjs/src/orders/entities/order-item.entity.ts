import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToOne,
  JoinColumn,
} from 'typeorm'
import { Order } from './order.entity'

@Entity('order_items')
export class OrderItem {
  @PrimaryGeneratedColumn()
  id: number

  @Column({ type: 'int' })
  orderId: number

  @ManyToOne(() => Order, (order) => order.items, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'orderId' })
  order: Order

  @Column({ type: 'int' })
  productId: number

  @Column({ type: 'varchar', length: 100 })
  productName: string

  @Column({ type: 'int' })
  quantity: number

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  unitPrice: number

  @Column({ type: 'jsonb', nullable: true })
  selectedItems: string[] | null

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  subtotal: number
}

