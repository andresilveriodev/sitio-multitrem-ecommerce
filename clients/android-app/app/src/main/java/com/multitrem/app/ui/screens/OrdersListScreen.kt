package com.multitrem.app.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.multitrem.app.domain.models.Order
import com.multitrem.app.domain.models.OrderStatus
import com.multitrem.app.ui.viewmodels.OrdersViewModel
import java.text.NumberFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OrdersListScreen(
    viewModel: OrdersViewModel,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()

    Column(modifier = modifier.fillMaxSize()) {
        TopAppBar(
            title = { Text("Pedidos do Dia") }
        )

        if (uiState.totalToday > 0) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            ) {
                Text(
                    text = "Total do Dia: ${NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(uiState.totalToday)}",
                    style = MaterialTheme.typography.headlineSmall,
                    modifier = Modifier.padding(16.dp)
                )
            }
        }

        if (uiState.isLoading) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = androidx.compose.ui.Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(uiState.orders) { order ->
                    OrderCard(order = order, onStatusChange = { newStatus ->
                        viewModel.updateOrderStatus(order.id, newStatus)
                    })
                }
            }
        }
    }
}

@Composable
fun OrderCard(
    order: Order,
    onStatusChange: (OrderStatus) -> Unit
) {
    var showDetails by remember { mutableStateOf(false) }

    Card(
        modifier = Modifier.fillMaxWidth(),
        onClick = { showDetails = !showDetails }
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = order.customerName,
                style = MaterialTheme.typography.titleMedium
            )
            Text(
                text = "Status: ${order.status.name}",
                style = MaterialTheme.typography.bodyMedium
            )
            Text(
                text = "Total: ${NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(order.items.sumOf { it.totalPrice })}",
                style = MaterialTheme.typography.bodySmall
            )

            if (showDetails) {
                Spacer(modifier = Modifier.height(8.dp))
                OrderDetailsContent(order = order, onStatusChange = onStatusChange)
            }
        }
    }
}

@Composable
fun OrderDetailsContent(
    order: Order,
    onStatusChange: (OrderStatus) -> Unit
) {
    val context = LocalContext.current
    Column {
        order.customerPhone?.let {
            Text("Telefone: $it")
        }
        Text("Tipo: ${order.deliveryType.name}")
        Text("Pagamento: ${order.paymentType.name}")
        order.observation?.let {
            Text("Obs: $it")
        }

        Spacer(modifier = Modifier.height(8.dp))

        Text("Itens:")
        order.items.forEach { item ->
            Text("  ${item.productName} x${item.quantity} = ${NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(item.totalPrice)}")
        }

        Spacer(modifier = Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OrderStatus.values().forEach { status ->
                FilterChip(
                    selected = order.status == status,
                    onClick = { onStatusChange(status) },
                    label = { Text(status.name) }
                )
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

    }
}

fun formatOrderForWhatsApp(order: Order): String {
    val sb = StringBuilder()
    sb.appendLine("📦 *Pedido #${order.id}*")
    sb.appendLine("Cliente: ${order.customerName}")
    order.customerPhone?.let { sb.appendLine("Telefone: $it") }
    sb.appendLine("Tipo: ${order.deliveryType.name}")
    sb.appendLine("Pagamento: ${order.paymentType.name}")
    sb.appendLine("Status: ${order.status.name}")
    sb.appendLine("\n*Itens:*")
    order.items.forEach { item ->
        sb.appendLine("• ${item.productName} x${item.quantity} = ${NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(item.totalPrice)}")
    }
    sb.appendLine("\n*Total: ${NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(order.items.sumOf { it.totalPrice })}*")
    order.observation?.let { sb.appendLine("\nObs: $it") }
    return sb.toString()
}
