package com.multitrem.app.domain.usecases

import com.multitrem.app.data.repository.OrderRepository
import com.multitrem.app.domain.models.OrderStatus

class UpdateOrderStatusUseCase(private val orderRepository: OrderRepository) {
    suspend operator fun invoke(orderId: Long, status: OrderStatus) {
        orderRepository.updateOrderStatus(orderId, status)
    }
}
