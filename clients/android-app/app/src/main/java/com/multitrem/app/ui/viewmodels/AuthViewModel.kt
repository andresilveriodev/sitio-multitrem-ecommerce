package com.multitrem.app.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.multitrem.app.auth.AuthState
import com.multitrem.app.auth.SessionManager
import com.multitrem.app.core.result.Result
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class AuthViewModel(private val sessionManager: SessionManager) : ViewModel() {
    val authState: StateFlow<AuthState> = sessionManager.authState

    init {
        viewModelScope.launch {
            sessionManager.checkSession()
        }
    }

    fun loginOnline() {
        viewModelScope.launch {
            sessionManager.loginOnline()
        }
    }

    fun loginOffline() {
        viewModelScope.launch {
            sessionManager.loginOffline()
        }
    }

    fun logout() {
        viewModelScope.launch {
            sessionManager.logout()
        }
    }

    fun getSessionManager() = sessionManager
}
