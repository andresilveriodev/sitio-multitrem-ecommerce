import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm'
import { PaymentMethod, PaymentStatus } from '@sitio/shared'

@Entity('payments')
export class PaymentEntity {
  @PrimaryGeneratedColumn()
  id: number

  @Column({ type: 'int' })
  orderId: number

  @Column({
    type: 'varchar',
    length: 20,
  })
  method: PaymentMethod

  @Column({
    type: 'varchar',
    length: 20,
    default: 'pending',
  })
  status: PaymentStatus

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  amount: number

  @Column({ type: 'varchar', length: 100, nullable: true })
  mercadoPagoId: string | null

  @Column({ type: 'text', nullable: true })
  pixQrCode: string | null

  @Column({ type: 'text', nullable: true })
  pixQrCodeBase64: string | null

  @Column({ type: 'varchar', length: 500, nullable: true })
  boletoUrl: string | null

  @Column({ type: 'varchar', length: 100, nullable: true })
  boletoBarcode: string | null

  @Column({ type: 'timestamp', nullable: true })
  expiresAt: Date | null

  @Column({ type: 'timestamp', nullable: true })
  paidAt: Date | null

  @CreateDateColumn()
  createdAt: Date

  @UpdateDateColumn()
  updatedAt: Date
}


