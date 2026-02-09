package com.multitrem.app.ui.screens

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.multitrem.app.MultitremApplication
import com.multitrem.app.auth.AuthState
import com.multitrem.app.auth.SessionManager
import com.multitrem.app.ui.theme.MultitremTheme
import com.multitrem.app.ui.viewmodels.AuthViewModel

class SplashActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val app = application as MultitremApplication
        val sessionManager = SessionManager(this)

        setContent {
            MultitremTheme {
                SplashScreen(
                    sessionManager = sessionManager,
                    onNavigateToLogin = {
                        startActivity(Intent(this, LoginActivity::class.java))
                        finish()
                    },
                    onNavigateToHome = {
                        startActivity(Intent(this, MainActivity::class.java))
                        finish()
                    }
                )
            }
        }
    }
}

@Composable
fun SplashScreen(
    sessionManager: SessionManager,
    onNavigateToLogin: () -> Unit,
    onNavigateToHome: () -> Unit
) {
    LaunchedEffect(Unit) {
        sessionManager.checkSession()
        sessionManager.authState.collect { state ->
            when (state) {
                is AuthState.Authenticated -> onNavigateToHome()
                is AuthState.Unauthenticated -> onNavigateToLogin()
            }
        }
    }

    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        CircularProgressIndicator()
    }
}
