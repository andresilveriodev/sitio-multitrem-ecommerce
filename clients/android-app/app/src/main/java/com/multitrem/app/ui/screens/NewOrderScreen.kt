package com.multitrem.app.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.multitrem.app.domain.models.*
import com.multitrem.app.ui.viewmodels.OrdersViewModel
import com.multitrem.app.ui.viewmodels.ProductsViewModel
import kotlinx.datetime.Clock
import java.text.NumberFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NewOrderScreen(
    productsViewModel: ProductsViewModel,
    ordersViewModel: OrdersViewModel,
    modifier: Modifier = Modifier
) {
    val productsState by productsViewModel.uiState.collectAsState()
    val customerName = remember { mutableStateOf("") }
    val customerPhone = remember { mutableStateOf("") }
    val deliveryType = remember { mutableStateOf(DeliveryType.ENTREGA) }
    val paymentType = remember { mutableStateOf(PaymentType.PIX) }
    val observation = remember { mutableStateOf("") }
    val selectedItems = remember { mutableStateMapOf<Long, Int>() }

    Column(modifier = modifier.fillMaxSize()) {
        TopAppBar(title = { Text("Novo Pedido") })

        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                OutlinedTextField(
                    value = customerName.value,
                    onValueChange = { customerName.value = it },
                    label = { Text("Nome do Cliente *") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
            }

            item {
                OutlinedTextField(
                    value = customerPhone.value,
                    onValueChange = { customerPhone.value = it },
                    label = { Text("Telefone (opcional)") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
            }

            item {
                Text("Tipo de Entrega")
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    DeliveryType.values().forEach { type ->
                        FilterChip(
                            selected = deliveryType.value == type,
                            onClick = { deliveryType.value = type },
                            label = { Text(type.name) }
                        )
                    }
                }
            }

            item {
                Text("Forma de Pagamento")
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    PaymentType.values().forEach { type ->
                        FilterChip(
                            selected = paymentType.value == type,
                            onClick = { paymentType.value = type },
                            label = { Text(type.name) }
                        )
                    }
                }
            }

            item {
                OutlinedTextField(
                    value = observation.value,
                    onValueChange = { observation.value = it },
                    label = { Text("Observação") },
                    modifier = Modifier.fillMaxWidth(),
                    maxLines = 3
                )
            }

            item {
                Divider()
                Text("Produtos", style = MaterialTheme.typography.titleMedium)
            }

            items(productsState.products) { product ->
                ProductItemCard(
                    product = product,
                    quantity = selectedItems[product.id] ?: 0,
                    onQuantityChange = { qty ->
                        if (qty > 0) {
                            selectedItems[product.id] = qty
                        } else {
                            selectedItems.remove(product.id)
                        }
                    }
                )
            }
        }

        Card(
            modifier = Modifier.fillMaxWidth(),
            elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                val total = selectedItems.entries.sumOf { (productId, qty) ->
                    val product = productsState.products.find { it.id == productId }
                    (product?.price ?: 0.0) * qty
                }

                Text(
                    text = "Total: ${NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(total)}",
                    style = MaterialTheme.typography.headlineSmall
                )

                Spacer(modifier = Modifier.height(8.dp))

                Button(
                    onClick = {
                        if (customerName.value.isNotBlank() && selectedItems.isNotEmpty()) {
                            val items = selectedItems.mapNotNull { (productId, qty) ->
                                val product = productsState.products.find { it.id == productId }
                                product?.let {
                                    OrderItem(
                                        productId = it.id,
                                        productName = it.name,
                                        quantity = qty,
                                        unitPrice = it.price,
                                        totalPrice = it.price * qty
                                    )
                                }
                            }

                            val order = Order(
                                customerName = customerName.value,
                                customerPhone = customerPhone.value.takeIf { it.isNotBlank() },
                                deliveryType = deliveryType.value,
                                paymentType = paymentType.value,
                                observation = observation.value.takeIf { it.isNotBlank() },
                                status = OrderStatus.PENDENTE,
                                createdAt = Clock.System.now(),
                                items = items
                            )

                            ordersViewModel.createOrder(order)

                            // Reset form
                            customerName.value = ""
                            customerPhone.value = ""
                            observation.value = ""
                            selectedItems.clear()
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = customerName.value.isNotBlank() && selectedItems.isNotEmpty()
                ) {
                    Text("Criar Pedido")
                }
            }
        }
    }
}

@Composable
fun ProductItemCard(
    product: com.multitrem.app.domain.models.Product,
    quantity: Int,
    onQuantityChange: (Int) -> Unit
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = product.name,
                    style = MaterialTheme.typography.titleMedium
                )
                Text(
                    text = NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(product.price),
                    style = MaterialTheme.typography.bodySmall
                )
            }

            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = { onQuantityChange(quantity - 1) }) {
                    Icon(Icons.Default.Remove, contentDescription = "Diminuir")
                }
                Text("$quantity")
                IconButton(onClick = { onQuantityChange(quantity + 1) }) {
                    Icon(Icons.Default.Add, contentDescription = "Aumentar")
                }
            }
        }
    }
}
