package com.multitrem.app.data.database.converters

import androidx.room.TypeConverter
import com.multitrem.app.domain.models.OrderStatus

class OrderStatusConverter {
    @TypeConverter
    fun fromStatus(value: OrderStatus): String {
        return value.name
    }

    @TypeConverter
    fun toStatus(value: String): OrderStatus {
        return OrderStatus.valueOf(value)
    }
}
