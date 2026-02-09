package com.multitrem.app.data.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.multitrem.app.domain.models.Product

@Entity(tableName = "products")
data class ProductEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val name: String,
    val description: String? = null,
    val price: Double,
    val active: Boolean = true
) {
    fun toDomain() = Product(
        id = id,
        name = name,
        description = description,
        price = price,
        active = active
    )

    companion object {
        fun fromDomain(product: Product) = ProductEntity(
            id = product.id,
            name = product.name,
            description = product.description,
            price = product.price,
            active = product.active
        )
    }
}
