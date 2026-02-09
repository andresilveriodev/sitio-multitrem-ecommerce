package com.multitrem.app.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.multitrem.app.data.repository.OrderRepository
import com.multitrem.app.domain.models.Order
import com.multitrem.app.domain.models.OrderStatus
import com.multitrem.app.domain.usecases.CreateOrderUseCase
import com.multitrem.app.domain.usecases.GetOrdersByDateUseCase
import com.multitrem.app.domain.usecases.UpdateOrderStatusUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant

data class OrdersUiState(
    val orders: List<Order> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val totalToday: Double = 0.0
)

class OrdersViewModel(
    private val getOrdersByDateUseCase: GetOrdersByDateUseCase,
    private val createOrderUseCase: CreateOrderUseCase,
    private val updateOrderStatusUseCase: UpdateOrderStatusUseCase,
    private val orderRepository: OrderRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(OrdersUiState())
    val uiState: StateFlow<OrdersUiState> = _uiState.asStateFlow()

    init {
        loadOrdersToday()
    }

    fun loadOrdersToday() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            try {
                val today = Clock.System.now()
                getOrdersByDateUseCase(today).collect { orders ->
                    val total = orderRepository.getTotalByDate(today)
                    _uiState.value = _uiState.value.copy(
                        orders = orders,
                        isLoading = false,
                        totalToday = total
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message
                )
            }
        }
    }

    fun createOrder(order: Order) {
        viewModelScope.launch {
            try {
                createOrderUseCase(order)
                loadOrdersToday()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = e.message)
            }
        }
    }

    fun updateOrderStatus(orderId: Long, status: OrderStatus) {
        viewModelScope.launch {
            try {
                updateOrderStatusUseCase(orderId, status)
                loadOrdersToday()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = e.message)
            }
        }
    }
}
