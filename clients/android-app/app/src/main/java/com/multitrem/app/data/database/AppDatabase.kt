package com.multitrem.app.data.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.multitrem.app.data.database.dao.OrderDao
import com.multitrem.app.data.database.dao.ProductDao
import com.multitrem.app.data.database.entities.OrderEntity
import com.multitrem.app.data.database.entities.OrderItemEntity
import com.multitrem.app.data.database.entities.ProductEntity

@Database(
    entities = [ProductEntity::class, OrderEntity::class, OrderItemEntity::class],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun productDao(): ProductDao
    abstract fun orderDao(): OrderDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "multitrem_database"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
