package com.multitrem.app.ui.screens

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.fragment.app.FragmentActivity
import com.multitrem.app.auth.SessionManager
import com.multitrem.app.core.result.Result
import com.multitrem.app.ui.theme.MultitremTheme
import kotlinx.coroutines.launch

class OfflineUnlockActivity : FragmentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val sessionManager = SessionManager(this)

        setContent {
            MultitremTheme {
                OfflineUnlockScreen(
                    sessionManager = sessionManager,
                    onSuccess = {
                        startActivity(Intent(this, MainActivity::class.java))
                        finish()
                    },
                    onCancel = {
                        finish()
                    }
                )
            }
        }
    }
}

@Composable
fun OfflineUnlockScreen(
    sessionManager: SessionManager,
    onSuccess: () -> Unit,
    onCancel: () -> Unit
) {
    val offlineAuthManager = sessionManager.getOfflineAuthManager()
    val showPinInput = remember { mutableStateOf(false) }
    val pin = remember { mutableStateOf("") }
    val error = remember { mutableStateOf<String?>(null) }
    val isLoading = remember { mutableStateOf(false) }
    val coroutineScope = rememberCoroutineScope()
    val context = androidx.compose.ui.platform.LocalContext.current
    val activity = context as? FragmentActivity
    
    LaunchedEffect(Unit) {
        // Tenta biometria primeiro
        val biometricManager = androidx.biometric.BiometricManager.from(context)
        val canAuthenticate = biometricManager.canAuthenticate(
            androidx.biometric.BiometricManager.Authenticators.BIOMETRIC_STRONG or
            androidx.biometric.BiometricManager.Authenticators.DEVICE_CREDENTIAL
        )
        
        if (canAuthenticate == androidx.biometric.BiometricManager.BIOMETRIC_SUCCESS && activity != null) {
            offlineAuthManager.authenticateWithBiometric(
                activity = activity,
                onSuccess = {
                    coroutineScope.launch {
                        sessionManager.loginOffline()
                    }
                },
                onError = { errorMsg ->
                    error.value = errorMsg
                    showPinInput.value = true
                }
            )
        } else {
            showPinInput.value = true
        }
    }

    LaunchedEffect(sessionManager.authState) {
        sessionManager.authState.collect { state ->
            if (state is com.multitrem.app.auth.AuthState.Authenticated) {
                onSuccess()
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Desbloqueio Offline",
            style = MaterialTheme.typography.headlineMedium
        )

        Spacer(modifier = Modifier.height(32.dp))

        if (showPinInput.value) {
            OutlinedTextField(
                value = pin.value,
                onValueChange = { pin.value = it },
                label = { Text("PIN") },
                visualTransformation = PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                maxLines = 1
            )

            Spacer(modifier = Modifier.height(16.dp))

            Button(
                onClick = {
                    isLoading.value = true
                    error.value = null
                    coroutineScope.launch {
                        val result = offlineAuthManager.authenticateWithPin(pin.value)
                        isLoading.value = false
                        when (result) {
                            is Result.Success -> {
                                sessionManager.loginOffline()
                            }
                            is Result.Error -> {
                                error.value = result.exception.message
                            }
                            else -> {}
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = !isLoading.value && pin.value.length >= 4
            ) {
                if (isLoading.value) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp))
                } else {
                    Text("Confirmar")
                }
            }
        } else {
            CircularProgressIndicator()
            Text("Aguardando biometria...")
        }

        error.value?.let {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = it,
                color = MaterialTheme.colorScheme.error
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        TextButton(onClick = onCancel) {
            Text("Cancelar")
        }
    }
}
