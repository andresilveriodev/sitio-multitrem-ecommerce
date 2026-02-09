package com.multitrem.app.domain.usecases

import com.multitrem.app.data.repository.OrderRepository
import com.multitrem.app.domain.models.Order
import kotlinx.coroutines.flow.Flow
import kotlinx.datetime.Clock

class CreateOrderUseCase(private val orderRepository: OrderRepository) {
    suspend operator fun invoke(order: Order): Long {
        val orderWithTimestamp = order.copy(
            createdAt = order.createdAt.takeIf { it != Clock.System.now() } ?: Clock.System.now()
        )
        return orderRepository.insertOrder(orderWithTimestamp)
    }
}
