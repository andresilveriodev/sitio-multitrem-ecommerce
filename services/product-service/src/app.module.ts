import { Module, OnModuleInit } from '@nestjs/common'
import { ConfigModule, ConfigService } from '@nestjs/config'
import { TypeOrmModule } from '@nestjs/typeorm'
import { DataSource } from 'typeorm'
import { getDatabaseConfig } from './config/database.config'
import { ProductsModule } from './products/products.module'
import { ProductsService } from './products/products.service'

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: getDatabaseConfig,
      inject: [ConfigService],
    }),
    ProductsModule,
  ],
})
export class AppModule implements OnModuleInit {
  constructor(
    private readonly dataSource: DataSource,
    private readonly productsService: ProductsService,
  ) {}

  async onModuleInit() {
    // Executar seed automaticamente ao iniciar (apenas se banco estiver vazio)
    try {
      await this.productsService.seed()
    } catch (error) {
      console.error('Error seeding database:', error)
    }
  }
}

