package com.multitrem.app.data.database.converters

import androidx.room.TypeConverter
import com.multitrem.app.domain.models.DeliveryType

class DeliveryTypeConverter {
    @TypeConverter
    fun fromType(value: DeliveryType): String {
        return value.name
    }

    @TypeConverter
    fun toType(value: String): DeliveryType {
        return DeliveryType.valueOf(value)
    }
}
