package com.multitrem.app.core

import com.multitrem.app.data.database.AppDatabase
import com.multitrem.app.data.database.entities.ProductEntity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

object ProductSeeder {
    fun seedProducts(database: AppDatabase) {
        val products = listOf(
            ProductEntity(
                name = "Produto 1",
                description = "Descrição do produto 1",
                price = 29.90,
                active = true
            ),
            ProductEntity(
                name = "Produto 2",
                description = "Descrição do produto 2",
                price = 39.90,
                active = true
            ),
            ProductEntity(
                name = "Produto 3",
                description = "Descrição do produto 3",
                price = 49.90,
                active = true
            ),
            ProductEntity(
                name = "Produto 4",
                description = "Descrição do produto 4",
                price = 59.90,
                active = true
            ),
            ProductEntity(
                name = "Produto 5",
                description = "Descrição do produto 5",
                price = 69.90,
                active = true
            )
        )

        CoroutineScope(Dispatchers.IO).launch {
            database.productDao().insertAll(products)
        }
    }
}
