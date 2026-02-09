package com.multitrem.app.ui.screens

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.multitrem.app.MultitremApplication
import com.multitrem.app.data.database.AppDatabase
import com.multitrem.app.data.repository.OrderRepository
import com.multitrem.app.data.repository.ProductRepository
import com.multitrem.app.domain.usecases.CreateOrderUseCase
import com.multitrem.app.domain.usecases.GetAllProductsUseCase
import com.multitrem.app.domain.usecases.GetOrdersByDateUseCase
import com.multitrem.app.domain.usecases.UpdateOrderStatusUseCase
import com.multitrem.app.ui.theme.MultitremTheme
import com.multitrem.app.ui.viewmodels.OrdersViewModel
import com.multitrem.app.ui.viewmodels.ProductsViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val app = application as MultitremApplication
        val database = app.database
        val productRepository = ProductRepository(database.productDao())
        val orderRepository = OrderRepository(database.orderDao())

        setContent {
            MultitremTheme {
                MainScreen(
                    productRepository = productRepository,
                    orderRepository = orderRepository
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    productRepository: ProductRepository,
    orderRepository: OrderRepository
) {
    val navController = rememberNavController()
    var selectedTab by remember { mutableStateOf(0) }

    val getAllProductsUseCase = GetAllProductsUseCase(productRepository)
    val getOrdersByDateUseCase = GetOrdersByDateUseCase(orderRepository)
    val createOrderUseCase = CreateOrderUseCase(orderRepository)
    val updateOrderStatusUseCase = UpdateOrderStatusUseCase(orderRepository)

    val ordersViewModel = remember {
        OrdersViewModel(
            getOrdersByDateUseCase,
            createOrderUseCase,
            updateOrderStatusUseCase,
            orderRepository
        )
    }

    val productsViewModel = remember {
        ProductsViewModel(getAllProductsUseCase)
    }

    Scaffold(
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    icon = { Icon(Icons.Filled.List, contentDescription = "Pedidos") },
                    label = { Text("Pedidos") }
                )
                NavigationBarItem(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    icon = { Icon(Icons.Filled.Add, contentDescription = "Novo Pedido") },
                    label = { Text("Novo Pedido") }
                )
                NavigationBarItem(
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 },
                    icon = { Icon(Icons.Filled.Settings, contentDescription = "Configurações") },
                    label = { Text("Configurações") }
                )
            }
        }
    ) { paddingValues ->
        when (selectedTab) {
            0 -> OrdersListScreen(
                viewModel = ordersViewModel,
                modifier = Modifier.padding(paddingValues)
            )
            1 -> NewOrderScreen(
                productsViewModel = productsViewModel,
                ordersViewModel = ordersViewModel,
                modifier = Modifier.padding(paddingValues)
            )
            2 -> SettingsScreen(modifier = Modifier.padding(paddingValues))
        }
    }
}
