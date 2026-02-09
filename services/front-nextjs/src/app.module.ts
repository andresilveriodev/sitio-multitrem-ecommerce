import { Module } from '@nestjs/common'
import { ConfigModule, ConfigService } from '@nestjs/config'
import { TypeOrmModule } from '@nestjs/typeorm'
import { OrdersModule } from './orders/orders.module'
import { DeliveryModule } from './delivery/delivery.module'
import { getDatabaseConfig } from './config/database.config'

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
    OrdersModule,
    DeliveryModule,
  ],
})
export class AppModule {}


