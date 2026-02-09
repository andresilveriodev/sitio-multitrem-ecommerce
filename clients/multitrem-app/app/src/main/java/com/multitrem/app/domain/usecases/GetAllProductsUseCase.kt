package com.multitrem.app.domain.usecases

import com.multitrem.app.data.repository.ProductRepository
import com.multitrem.app.domain.models.Product
import kotlinx.coroutines.flow.Flow

class GetAllProductsUseCase(private val productRepository: ProductRepository) {
    operator fun invoke(): Flow<List<Product>> {
        return productRepository.getAllProducts()
    }
}
