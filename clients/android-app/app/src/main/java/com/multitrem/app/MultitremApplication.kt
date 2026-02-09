package com.multitrem.app

import android.app.Application
import com.multitrem.app.core.ProductSeeder
import com.multitrem.app.data.database.AppDatabase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class MultitremApplication : Application() {
    val database by lazy { AppDatabase.getDatabase(this) }
    private val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    
    override fun onCreate() {
        super.onCreate()
        // Seed inicial de produtos
        applicationScope.launch {
            val products = database.productDao().getAll().first()
            if (products.isEmpty()) {
                ProductSeeder.seedProducts(database)
            }
        }
    }
}
