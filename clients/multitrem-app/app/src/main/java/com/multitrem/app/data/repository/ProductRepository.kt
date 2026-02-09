package com.multitrem.app.data.repository

import com.multitrem.app.data.database.dao.ProductDao
import com.multitrem.app.data.database.entities.ProductEntity
import com.multitrem.app.domain.models.Product
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class ProductRepository(private val productDao: ProductDao) {
    fun getAllProducts(): Flow<List<Product>> {
        return productDao.getAll().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    suspend fun getProductById(id: Long): Product? {
        return productDao.getById(id)?.toDomain()
    }

    suspend fun insertProduct(product: Product): Long {
        return productDao.insert(ProductEntity.fromDomain(product))
    }
}
