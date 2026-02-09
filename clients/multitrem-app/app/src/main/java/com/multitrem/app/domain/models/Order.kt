package com.multitrem.app.domain.models

import kotlinx.datetime.Instant

enum class OrderStatus {
    PENDENTE,
    SEPARANDO,
    ENTREGUE,
    CANCELADO
}

enum class DeliveryType {
    ENTREGA,
    RETIRADA
}

enum class PaymentType {
    PIX,
    DINHEIRO
}

data class Order(
    val id: Long = 0,
    val customerName: String,
    val customerPhone: String? = null,
    val deliveryType: DeliveryType,
    val paymentType: PaymentType,
    val observation: String? = null,
    val status: OrderStatus = OrderStatus.PENDENTE,
    val createdAt: Instant,
    val items: List<OrderItem> = emptyList()
)

data class OrderItem(
    val id: Long = 0,
    val orderId: Long = 0,
    val productId: Long,
    val productName: String,
    val quantity: Int,
    val unitPrice: Double,
    val totalPrice: Double
)
