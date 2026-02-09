package com.multitrem.app.ui.screens

import android.content.Intent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.multitrem.app.auth.SessionManager
import com.multitrem.app.core.result.Result
import com.multitrem.app.ui.screens.LoginActivity
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val sessionManager = SessionManager(context)
    val offlineAuthManager = sessionManager.getOfflineAuthManager()
    val coroutineScope = rememberCoroutineScope()

    val offlineEnabled = remember { mutableStateOf(false) }
    val showPinDialog = remember { mutableStateOf(false) }
    val newPin = remember { mutableStateOf("") }
    val confirmPin = remember { mutableStateOf("") }
    val pinError = remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        offlineEnabled.value = offlineAuthManager.isOfflineEnabled()
    }

    Column(modifier = modifier.fillMaxSize()) {
        TopAppBar(title = { Text("Configurações") })

        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Autenticação Offline",
                        style = MaterialTheme.typography.titleMedium
                    )
                    Text(
                        text = if (offlineEnabled.value) "Habilitada" else "Desabilitada",
                        style = MaterialTheme.typography.bodyMedium
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    if (offlineEnabled.value) {
                        Button(
                            onClick = { showPinDialog.value = true },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("Alterar PIN")
                        }
                    }
                }
            }

            Button(
                onClick = {
                    coroutineScope.launch {
                        sessionManager.logout()
                        // Navega para LoginActivity
                        val intent = Intent(context, LoginActivity::class.java).apply {
                            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                        }
                        context.startActivity(intent)
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.error
                )
            ) {
                Text("Sair")
            }
        }
    }

    if (showPinDialog.value) {
        AlertDialog(
            onDismissRequest = { showPinDialog.value = false },
            title = { Text("Definir PIN") },
            text = {
                Column {
                    OutlinedTextField(
                        value = newPin.value,
                        onValueChange = { newPin.value = it },
                        label = { Text("Novo PIN (4-6 dígitos)") },
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = confirmPin.value,
                        onValueChange = { confirmPin.value = it },
                        label = { Text("Confirmar PIN") },
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth()
                    )
                    pinError.value?.let {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = it,
                            color = MaterialTheme.colorScheme.error
                        )
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        if (newPin.value != confirmPin.value) {
                            pinError.value = "PINs não coincidem"
                        } else if (newPin.value.length < 4 || newPin.value.length > 6) {
                            pinError.value = "PIN deve ter entre 4 e 6 dígitos"
                        } else {
                            coroutineScope.launch {
                                val result = offlineAuthManager.setPin(newPin.value)
                                if (result is Result.Success) {
                                    showPinDialog.value = false
                                    newPin.value = ""
                                    confirmPin.value = ""
                                    pinError.value = null
                                } else {
                                    pinError.value = result.exception.message
                                }
                            }
                        }
                    }
                ) {
                    Text("Salvar")
                }
            },
            dismissButton = {
                TextButton(onClick = { showPinDialog.value = false }) {
                    Text("Cancelar")
                }
            }
        )
    }
}
