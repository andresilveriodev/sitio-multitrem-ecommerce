package com.multitrem.app.data.database.converters

import androidx.room.TypeConverter
import com.multitrem.app.domain.models.PaymentType

class PaymentTypeConverter {
    @TypeConverter
    fun fromType(value: PaymentType): String {
        return value.name
    }

    @TypeConverter
    fun toType(value: String): PaymentType {
        return PaymentType.valueOf(value)
    }
}
