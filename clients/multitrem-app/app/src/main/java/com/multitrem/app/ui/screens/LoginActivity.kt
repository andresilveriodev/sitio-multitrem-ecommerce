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
import androidx.compose.ui.unit.dp
import com.multitrem.app.auth.SessionManager
import com.multitrem.app.ui.theme.MultitremTheme
import net.openid.appauth.AuthorizationException
import net.openid.appauth.AuthorizationResponse
import kotlinx.coroutines.launch

class LoginActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val sessionManager = SessionManager(this)
        
        // Verifica se é um callback OAuth
        handleAuthResponse(intent)

        setContent {
            MultitremTheme {
                LoginScreen(
                    sessionManager = sessionManager,
                    onLoginSuccess = {
                        startActivity(Intent(this, MainActivity::class.java))
                        finish()
                    },
                    onOfflineUnlock = {
                        startActivity(Intent(this, OfflineUnlockActivity::class.java))
                    }
                )
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleAuthResponse(intent)
    }

    private fun handleAuthResponse(intent: Intent) {
        val response = AuthorizationResponse.fromIntent(intent)
        val exception = AuthorizationException.fromIntent(intent)

        if (response != null || exception != null) {
            val sessionManager = SessionManager(this)
            val authService = sessionManager.getKeycloakAuthService()
            
            if (response != null) {
                // Processa o callback OAuth
                kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.Main).launch {
                    val result = authService.handleAuthorizationResponse(intent)
                    if (result is com.multitrem.app.core.result.Result.Success) {
                        // Login bem-sucedido, navega para MainActivity
                        startActivity(Intent(this@LoginActivity, MainActivity::class.java))
                        finish()
                    }
                }
            }
        }
    }
}

@Composable
fun LoginScreen(
    sessionManager: SessionManager,
    onLoginSuccess: () -> Unit,
    onOfflineUnlock: () -> Unit
) {
    val offlineEnabled = remember { mutableStateOf(false) }
    val isLoading = remember { mutableStateOf(false) }
    val error = remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        offlineEnabled.value = sessionManager.getOfflineAuthManager().isOfflineEnabled()
    }

    LaunchedEffect(sessionManager.authState) {
        sessionManager.authState.collect { state ->
            when (state) {
                is com.multitrem.app.auth.AuthState.Authenticated -> {
                    onLoginSuccess()
                }
                is com.multitrem.app.auth.AuthState.Unauthenticated -> {
                    // Continua na tela de login
                }
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
            text = "Multitrem",
            style = MaterialTheme.typography.headlineLarge
        )

        Spacer(modifier = Modifier.height(32.dp))

        Button(
            onClick = {
                isLoading.value = true
                error.value = null
                sessionManager.loginOnline()
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = !isLoading.value
        ) {
            if (isLoading.value) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp))
            } else {
                Text("Login Online")
            }
        }

        if (offlineEnabled.value) {
            Spacer(modifier = Modifier.height(16.dp))

            OutlinedButton(
                onClick = { onOfflineUnlock() },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Login Offline")
            }
        }

        error.value?.let {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = it,
                color = MaterialTheme.colorScheme.error
            )
        }
    }
}
