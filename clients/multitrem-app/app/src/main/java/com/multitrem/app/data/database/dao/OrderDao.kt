package com.multitrem.app.data.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import com.multitrem.app.data.database.entities.OrderEntity
import com.multitrem.app.data.database.entities.OrderItemEntity
import com.multitrem.app.domain.models.OrderStatus
import kotlinx.coroutines.flow.Flow
import kotlinx.datetime.Instant

@Dao
interface OrderDao {
    @Query("SELECT * FROM orders ORDER BY createdAt DESC")
    fun getAll(): Flow<List<OrderEntity>>

    @Query("SELECT * FROM orders WHERE DATE(createdAt/1000, 'unixepoch') = DATE(:date/1000, 'unixepoch') ORDER BY createdAt DESC")
    fun getByDate(date: Instant): Flow<List<OrderEntity>>

    @Query("SELECT * FROM orders WHERE id = :id")
    suspend fun getById(id: Long): OrderEntity?

    @Query("SELECT * FROM order_items WHERE orderId = :orderId")
    suspend fun getItemsByOrderId(orderId: Long): List<OrderItemEntity>

    @Query("SELECT SUM(totalPrice) FROM order_items WHERE orderId IN (SELECT id FROM orders WHERE DATE(createdAt/1000, 'unixepoch') = DATE(:date/1000, 'unixepoch'))")
    suspend fun getTotalByDate(date: Instant): Double?

    @Transaction
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrder(order: OrderEntity): Long

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrderItems(items: List<OrderItemEntity>)

    @Query("UPDATE orders SET status = :status WHERE id = :orderId")
    suspend fun updateStatus(orderId: Long, status: OrderStatus)

    @Query("DELETE FROM orders WHERE id = :orderId")
    suspend fun deleteOrder(orderId: Long)
}
