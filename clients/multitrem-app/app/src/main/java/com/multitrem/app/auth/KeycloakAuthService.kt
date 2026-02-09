package com.multitrem.app.auth

import android.content.Context
import android.content.Intent
import android.net.Uri
import com.multitrem.app.BuildConfig
import com.multitrem.app.core.result.Result
import net.openid.appauth.*
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant
import kotlin.coroutines.resume

data class AuthSession(
    val accessToken: String,
    val refreshToken: String?,
    val idToken: String?,
    val expiresAt: Instant?
)

class KeycloakAuthService(private val context: Context) {
    private val authService: AuthorizationService = AuthorizationService(context)
    private val config: AuthorizationServiceConfiguration
    private val clientId: String = BuildConfig.KEYCLOAK_CLIENT_ID
    private val redirectUri: Uri = Uri.parse(BuildConfig.KEYCLOAK_REDIRECT_URI)

    init {
        // O issuer já contém o caminho completo do realm
        // Exemplo: https://auth.rendacontinua.com/auth/realms/auth_sso
        val issuerUri = Uri.parse(BuildConfig.KEYCLOAK_ISSUER)
        config = AuthorizationServiceConfiguration(
            AuthorizationEndpoint(issuerUri.buildUpon().appendPath("protocol").appendPath("openid-connect").appendPath("auth").build()),
            TokenEndpoint(issuerUri.buildUpon().appendPath("protocol").appendPath("openid-connect").appendPath("token").build())
        )
    }

    suspend fun login(): Result<Unit> = suspendCancellableCoroutine { continuation ->
        val codeVerifier = CodeVerifierUtil.generateRandomCodeVerifier()
        val codeChallenge = CodeVerifierUtil.getCodeChallenge(codeVerifier)
        val codeChallengeMethod = CodeVerifierUtil.getCodeChallengeMethod()

        val request = AuthorizationRequest.Builder(
            config,
            clientId,
            ResponseTypeValues.CODE,
            redirectUri
        )
            .setCodeVerifier(codeVerifier)
            .setCodeChallenge(codeChallenge)
            .setCodeChallengeMethod(codeChallengeMethod)
            .setScopes("openid", "profile", "email")
            .build()

        val intent = authService.getAuthorizationRequestIntent(request)
        
        // Armazena o request para usar depois no callback
        AuthStateManager.saveAuthRequest(context, request)

        continuation.invokeOnCancellation {
            // Cleanup se cancelado
        }

        try {
            context.startActivity(intent)
            // O resultado virá via handleAuthorizationResponse
            continuation.resume(Result.Success(Unit))
        } catch (e: Exception) {
            continuation.resume(Result.Error(e))
        }
    }

    suspend fun handleAuthorizationResponse(intent: Intent): Result<AuthSession> {
        val response = AuthorizationResponse.fromIntent(intent)
        val exception = AuthorizationException.fromIntent(intent)

        if (exception != null) {
            return Result.Error(exception)
        }

        if (response == null) {
            return Result.Error(Exception("Resposta de autorização inválida"))
        }

        val request = AuthStateManager.getAuthRequest(context)
            ?: return Result.Error(Exception("Request de autorização não encontrado"))

        return suspendCancellableCoroutine { continuation ->
            val tokenRequest = response.createTokenExchangeRequest()
            authService.performTokenRequest(tokenRequest) { response, exception ->
                if (exception != null) {
                    continuation.resume(Result.Error(exception))
                    return@performTokenRequest
                }

                if (response == null) {
                    continuation.resume(Result.Error(Exception("Resposta de token inválida")))
                    return@performTokenRequest
                }

                val expiresAt = response.accessTokenExpirationTime?.let {
                    Instant.fromEpochMilliseconds(it)
                }

                val session = AuthSession(
                    accessToken = response.accessToken ?: "",
                    refreshToken = response.refreshToken,
                    idToken = response.idToken,
                    expiresAt = expiresAt
                )

                AuthStateManager.saveSession(context, session)
                continuation.resume(Result.Success(session))
            }
        }
    }

    suspend fun getCurrentSession(): AuthSession? {
        return AuthStateManager.getSession(context)
    }

    suspend fun refreshToken(): Result<AuthSession> {
        val currentSession = getCurrentSession() ?: return Result.Error(Exception("Nenhuma sessão encontrada"))
        val refreshToken = currentSession.refreshToken ?: return Result.Error(Exception("Refresh token não disponível"))

        return suspendCancellableCoroutine { continuation ->
            val tokenRequest = TokenRequest.Builder(config, clientId)
                .setRefreshToken(refreshToken)
                .setRedirectUri(redirectUri)
                .build()

            authService.performTokenRequest(tokenRequest) { response, exception ->
                if (exception != null) {
                    continuation.resume(Result.Error(exception))
                    return@performTokenRequest
                }

                if (response == null) {
                    continuation.resume(Result.Error(Exception("Resposta de token inválida")))
                    return@performTokenRequest
                }

                val expiresAt = response.accessTokenExpirationTime?.let {
                    Instant.fromEpochMilliseconds(it)
                }

                val session = AuthSession(
                    accessToken = response.accessToken ?: "",
                    refreshToken = response.refreshToken ?: refreshToken,
                    idToken = response.idToken ?: currentSession.idToken,
                    expiresAt = expiresAt
                )

                AuthStateManager.saveSession(context, session)
                continuation.resume(Result.Success(session))
            }
        }
    }

    suspend fun logout() {
        AuthStateManager.clearSession(context)
    }

    fun dispose() {
        authService.dispose()
    }
}
