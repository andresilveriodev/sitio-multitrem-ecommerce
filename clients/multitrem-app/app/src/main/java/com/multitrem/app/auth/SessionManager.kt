package com.multitrem.app.auth

import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant

sealed class AuthState {
    object Unauthenticated : AuthState()
    data class Authenticated(val isOnline: Boolean, val expiresAt: Instant?) : AuthState()
}

class SessionManager(private val context: Context) {
    private val _authState = MutableStateFlow<AuthState>(AuthState.Unauthenticated)
    val authState: StateFlow<AuthState> = _authState.asStateFlow()

    private val offlineAuthManager = OfflineAuthManager(context)
    private val keycloakAuthService = KeycloakAuthService(context)

    suspend fun checkSession() {
        // Primeiro verifica se há sessão online
        val onlineSession = keycloakAuthService.getCurrentSession()
        if (onlineSession != null) {
            _authState.value = AuthState.Authenticated(isOnline = true, expiresAt = onlineSession.expiresAt)
            return
        }

        // Se não há sessão online, verifica offline
        if (offlineAuthManager.isOfflineEnabled()) {
            val offlineSession = offlineAuthManager.getOfflineSession()
            if (offlineSession != null && !offlineSession.isExpired()) {
                _authState.value = AuthState.Authenticated(isOnline = false, expiresAt = offlineSession.expiresAt)
                return
            }
        }

        _authState.value = AuthState.Unauthenticated
    }

    suspend fun loginOnline(): Result<Unit> {
        return try {
            val result = keycloakAuthService.login()
            if (result is Result.Success) {
                // Após login online bem-sucedido, habilita offline
                offlineAuthManager.enableOffline()
                _authState.value = AuthState.Authenticated(isOnline = true, expiresAt = null)
            }
            result
        } catch (e: Exception) {
            Result.Error(e)
        }
    }

    suspend fun loginOffline(): Result<Unit> {
        return try {
            if (!offlineAuthManager.isOfflineEnabled()) {
                return Result.Error(Exception("Offline não habilitado. Faça login online primeiro."))
            }

            val session = offlineAuthManager.getOfflineSession()
            if (session == null || session.isExpired()) {
                return Result.Error(Exception("Sessão offline expirada ou não encontrada."))
            }

            _authState.value = AuthState.Authenticated(isOnline = false, expiresAt = session.expiresAt)
            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(e)
        }
    }

    suspend fun logout() {
        keycloakAuthService.logout()
        offlineAuthManager.disableOffline()
        _authState.value = AuthState.Unauthenticated
    }

    fun getKeycloakAuthService(): KeycloakAuthService = keycloakAuthService
    fun getOfflineAuthManager(): OfflineAuthManager = offlineAuthManager
}
