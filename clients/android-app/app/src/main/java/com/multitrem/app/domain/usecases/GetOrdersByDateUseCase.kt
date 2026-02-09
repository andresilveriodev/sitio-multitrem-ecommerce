package com.multitrem.app.domain.usecases

import com.multitrem.app.data.repository.OrderRepository
import com.multitrem.app.domain.models.Order
import kotlinx.coroutines.flow.Flow
import kotlinx.datetime.Instant

class GetOrdersByDateUseCase(private val orderRepository: OrderRepository) {
    operator fun invoke(date: Instant): Flow<List<Order>> {
        return orderRepository.getOrdersByDate(date)
    }
}
