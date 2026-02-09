package com.multitrem.app.data.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.multitrem.app.data.database.converters.InstantConverter
import com.multitrem.app.data.database.converters.OrderStatusConverter
import com.multitrem.app.data.database.converters.DeliveryTypeConverter
import com.multitrem.app.data.database.converters.PaymentTypeConverter
import com.multitrem.app.domain.models.Order
import com.multitrem.app.domain.models.OrderStatus
import com.multitrem.app.domain.models.DeliveryType
import com.multitrem.app.domain.models.PaymentType
import kotlinx.datetime.Instant

@Entity(tableName = "orders")
@TypeConverters(
    InstantConverter::class,
    OrderStatusConverter::class,
    DeliveryTypeConverter::class,
    PaymentTypeConverter::class
)
data class OrderEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val customerName: String,
    val customerPhone: String? = null,
    val deliveryType: DeliveryType,
    val paymentType: PaymentType,
    val observation: String? = null,
    val status: OrderStatus = OrderStatus.PENDENTE,
    val createdAt: Instant
)
