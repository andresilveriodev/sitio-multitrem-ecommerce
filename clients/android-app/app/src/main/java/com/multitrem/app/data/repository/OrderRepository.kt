package com.multitrem.app.data.repository

import com.multitrem.app.data.database.dao.OrderDao
import com.multitrem.app.data.database.entities.OrderEntity
import com.multitrem.app.data.database.entities.OrderItemEntity
import com.multitrem.app.domain.models.Order
import com.multitrem.app.domain.models.OrderItem
import com.multitrem.app.domain.models.OrderStatus
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant

class OrderRepository(private val orderDao: OrderDao) {
    fun getAllOrders(): Flow<List<Order>> {
        return orderDao.getAll().map { entities ->
            entities.map { entity ->
                toOrderWithItems(entity)
            }
        }
    }

    fun getOrdersByDate(date: Instant): Flow<List<Order>> {
        return orderDao.getByDate(date).map { entities ->
            entities.map { entity ->
                toOrderWithItems(entity)
            }
        }
    }

    suspend fun getOrderById(id: Long): Order? {
        val entity = orderDao.getById(id) ?: return null
        return toOrderWithItems(entity)
    }

    suspend fun insertOrder(order: Order): Long {
        val orderId = orderDao.insertOrder(
            OrderEntity(
                id = order.id,
                customerName = order.customerName,
                customerPhone = order.customerPhone,
                deliveryType = order.deliveryType,
                paymentType = order.paymentType,
                observation = order.observation,
                status = order.status,
                createdAt = order.createdAt
            )
        )
        
        val items = order.items.map { item ->
            OrderItemEntity(
                id = item.id,
                orderId = orderId,
                productId = item.productId,
                productName = item.productName,
                quantity = item.quantity,
                unitPrice = item.unitPrice,
                totalPrice = item.totalPrice
            )
        }
        
        orderDao.insertOrderItems(items)
        return orderId
    }

    suspend fun updateOrderStatus(orderId: Long, status: OrderStatus) {
        orderDao.updateStatus(orderId, status)
    }

    suspend fun getTotalByDate(date: Instant): Double {
        return orderDao.getTotalByDate(date) ?: 0.0
    }

    private suspend fun toOrderWithItems(entity: OrderEntity): Order {
        val items = orderDao.getItemsByOrderId(entity.id).map { itemEntity ->
            OrderItem(
                id = itemEntity.id,
                orderId = itemEntity.orderId,
                productId = itemEntity.productId,
                productName = itemEntity.productName,
                quantity = itemEntity.quantity,
                unitPrice = itemEntity.unitPrice,
                totalPrice = itemEntity.totalPrice
            )
        }
        
        return Order(
            id = entity.id,
            customerName = entity.customerName,
            customerPhone = entity.customerPhone,
            deliveryType = entity.deliveryType,
            paymentType = entity.paymentType,
            observation = entity.observation,
            status = entity.status,
            createdAt = entity.createdAt,
            items = items
        )
    }
}
