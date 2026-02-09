package com.multitrem.app.auth

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.multitrem.app.auth.AuthSession
import net.openid.appauth.AuthorizationRequest
import org.json.JSONObject
import kotlinx.datetime.Instant
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json

object AuthStateManager {
    private const val PREFS_NAME = "encrypted_prefs"
    private const val KEY_SESSION = "auth_session"
    private const val KEY_AUTH_REQUEST = "auth_request"

    private fun getEncryptedPrefs(context: Context): SharedPreferences {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        return EncryptedSharedPreferences.create(
            context,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun saveSession(context: Context, session: AuthSession) {
        val prefs = getEncryptedPrefs(context)
        val sessionData = mapOf(
            "accessToken" to session.accessToken,
            "refreshToken" to (session.refreshToken ?: ""),
            "idToken" to (session.idToken ?: ""),
            "expiresAt" to (session.expiresAt?.toEpochMilliseconds()?.toString() ?: "")
        )
        prefs.edit().putString(KEY_SESSION, Json.encodeToString(sessionData)).apply()
    }

    fun getSession(context: Context): AuthSession? {
        val prefs = getEncryptedPrefs(context)
        val sessionJson = prefs.getString(KEY_SESSION, null) ?: return null
        
        return try {
            val sessionData = Json.decodeFromString<Map<String, String>>(sessionJson)
            val expiresAt = sessionData["expiresAt"]?.takeIf { it.isNotEmpty() }?.toLongOrNull()
            AuthSession(
                accessToken = sessionData["accessToken"] ?: "",
                refreshToken = sessionData["refreshToken"]?.takeIf { it.isNotEmpty() },
                idToken = sessionData["idToken"]?.takeIf { it.isNotEmpty() },
                expiresAt = expiresAt?.let { Instant.fromEpochMilliseconds(it) }
            )
        } catch (e: Exception) {
            null
        }
    }

    fun clearSession(context: Context) {
        val prefs = getEncryptedPrefs(context)
        prefs.edit().remove(KEY_SESSION).apply()
    }

    fun saveAuthRequest(context: Context, request: AuthorizationRequest) {
        val prefs = getEncryptedPrefs(context)
        // Serializa o request usando JSONObject do AppAuth
        val requestJson = request.jsonSerialize().toString()
        prefs.edit().putString(KEY_AUTH_REQUEST, requestJson).apply()
    }

    fun getAuthRequest(context: Context): AuthorizationRequest? {
        val prefs = getEncryptedPrefs(context)
        val requestJson = prefs.getString(KEY_AUTH_REQUEST, null) ?: return null
        
        return try {
            AuthorizationRequest.fromJson(JSONObject(requestJson))
        } catch (e: Exception) {
            null
        }
    }
}
