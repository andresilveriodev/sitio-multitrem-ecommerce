import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm'
import { ProductCategory } from '@sitio/shared'

@Entity('products')
export class Product {
  @PrimaryGeneratedColumn()
  id!: number

  @Column({ type: 'varchar', length: 100 })
  name!: string

  @Column({ type: 'varchar', length: 100, unique: true })
  slug!: string

  @Column({ type: 'text', nullable: true })
  description?: string

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  price!: number

  @Column({
    type: 'enum',
    enum: ['hortalica', 'ovos', 'kit', 'combo'],
  })
  category!: ProductCategory

  @Column({ type: 'varchar', length: 255, nullable: true })
  imageUrl?: string

  @Column({ type: 'boolean', default: true })
  active!: boolean

  @Column({ type: 'int', nullable: true })
  kitSize?: number

  @CreateDateColumn()
  createdAt!: Date

  @UpdateDateColumn()
  updatedAt!: Date
}


