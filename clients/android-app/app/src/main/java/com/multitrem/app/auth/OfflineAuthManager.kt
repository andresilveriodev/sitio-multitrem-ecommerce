package com.multitrem.app.auth

import android.content.Context
import android.content.SharedPreferences
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant
import java.security.SecureRandom
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.PBEKeySpec
import kotlin.coroutines.resume

data class OfflineSession(
    val expiresAt: Instant
) {
    fun isExpired(): Boolean {
        return Clock.System.now() >= expiresAt
    }
}

class OfflineAuthManager(private val context: Context) {
    private val prefs: SharedPreferences
    private val OFFLINE_EXPIRY_DAYS = 7L
    private val MAX_PIN_ATTEMPTS = 5
    private val PIN_LOCKOUT_DURATION_MS = 15 * 60 * 1000L // 15 minutos

    private val KEY_OFFLINE_ENABLED = "offline_enabled"
    private val KEY_PIN_HASH = "pin_hash"
    private val KEY_PIN_SALT = "pin_salt"
    private val KEY_OFFLINE_EXPIRES_AT = "offline_expires_at"
    private val KEY_PIN_ATTEMPTS = "pin_attempts"
    private val KEY_PIN_LOCKOUT_UNTIL = "pin_lockout_until"

    init {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        prefs = EncryptedSharedPreferences.create(
            context,
            "offline_auth_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun isOfflineEnabled(): Boolean {
        return prefs.getBoolean(KEY_OFFLINE_ENABLED, false)
    }

    fun enableOffline() {
        prefs.edit()
            .putBoolean(KEY_OFFLINE_ENABLED, true)
            .putLong(KEY_OFFLINE_EXPIRES_AT, Clock.System.now().plus(java.time.Duration.ofDays(OFFLINE_EXPIRY_DAYS)).toEpochMilliseconds())
            .apply()
    }

    fun disableOffline() {
        prefs.edit()
            .clear()
            .apply()
    }

    suspend fun setPin(pin: String): Result<Unit> {
        if (pin.length < 4 || pin.length > 6) {
            return Result.Error(Exception("PIN deve ter entre 4 e 6 dígitos"))
        }

        val salt = ByteArray(16).apply {
            SecureRandom().nextBytes(this)
        }

        val hash = hashPin(pin, salt)

        prefs.edit()
            .putString(KEY_PIN_HASH, hash)
            .putString(KEY_PIN_SALT, android.util.Base64.encodeToString(salt, android.util.Base64.NO_WRAP))
            .putInt(KEY_PIN_ATTEMPTS, 0)
            .apply()

        return Result.Success(Unit)
    }

    suspend fun authenticateWithBiometric(
        activity: androidx.fragment.app.FragmentActivity,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        val biometricManager = BiometricManager.from(context)
        val canAuthenticate = biometricManager.canAuthenticate(
            BiometricManager.Authenticators.BIOMETRIC_STRONG or BiometricManager.Authenticators.DEVICE_CREDENTIAL
        )

        if (canAuthenticate != BiometricManager.BIOMETRIC_SUCCESS) {
            onError("Biometria não disponível")
            return
        }

        val executor = ContextCompat.getMainExecutor(context)
        val biometricPrompt = BiometricPrompt(
            activity,
            executor,
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    onSuccess()
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    onError(errString.toString())
                }

                override fun onAuthenticationFailed() {
                    onError("Autenticação falhou")
                }
            }
        )

        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle(context.getString(com.multitrem.app.R.string.biometric_prompt_title))
            .setSubtitle(context.getString(com.multitrem.app.R.string.biometric_prompt_subtitle))
            .setDescription(context.getString(com.multitrem.app.R.string.biometric_prompt_description))
            .setNegativeButtonText(context.getString(com.multitrem.app.R.string.biometric_prompt_negative))
            .setAllowedAuthenticators(
                BiometricManager.Authenticators.BIOMETRIC_STRONG or
                BiometricManager.Authenticators.DEVICE_CREDENTIAL
            )
            .build()

        biometricPrompt.authenticate(promptInfo)
    }

    suspend fun authenticateWithPin(pin: String): Result<Unit> {
        // Verifica lockout
        val lockoutUntil = prefs.getLong(KEY_PIN_LOCKOUT_UNTIL, 0)
        if (lockoutUntil > System.currentTimeMillis()) {
            val remainingMinutes = ((lockoutUntil - System.currentTimeMillis()) / 60000) + 1
            return Result.Error(Exception("PIN bloqueado. Tente novamente em $remainingMinutes minuto(s)."))
        }

        val storedHash = prefs.getString(KEY_PIN_HASH, null)
        val storedSalt = prefs.getString(KEY_PIN_SALT, null)

        if (storedHash == null || storedSalt == null) {
            return Result.Error(Exception("PIN não configurado"))
        }

        val salt = android.util.Base64.decode(storedSalt, android.util.Base64.NO_WRAP)
        val hash = hashPin(pin, salt)

        if (hash == storedHash) {
            // Reset tentativas
            prefs.edit()
                .putInt(KEY_PIN_ATTEMPTS, 0)
                .putLong(KEY_PIN_LOCKOUT_UNTIL, 0)
                .apply()
            return Result.Success(Unit)
        } else {
            val attempts = prefs.getInt(KEY_PIN_ATTEMPTS, 0) + 1
            prefs.edit().putInt(KEY_PIN_ATTEMPTS, attempts).apply()

            if (attempts >= MAX_PIN_ATTEMPTS) {
                val lockoutUntil = System.currentTimeMillis() + PIN_LOCKOUT_DURATION_MS
                prefs.edit().putLong(KEY_PIN_LOCKOUT_UNTIL, lockoutUntil).apply()
                return Result.Error(Exception("Muitas tentativas. PIN bloqueado por 15 minutos."))
            }

            val remaining = MAX_PIN_ATTEMPTS - attempts
            return Result.Error(Exception("PIN incorreto. $remaining tentativa(s) restante(s)."))
        }
    }

    fun getOfflineSession(): OfflineSession? {
        if (!isOfflineEnabled()) return null

        val expiresAtMs = prefs.getLong(KEY_OFFLINE_EXPIRES_AT, 0)
        if (expiresAtMs == 0L) return null

        val expiresAt = Instant.fromEpochMilliseconds(expiresAtMs)
        val session = OfflineSession(expiresAt)

        if (session.isExpired()) {
            return null
        }

        return session
    }

    private fun hashPin(pin: String, salt: ByteArray): String {
        val spec = PBEKeySpec(pin.toCharArray(), salt, 10000, 256)
        val factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
        val hash = factory.generateSecret(spec).encoded
        return android.util.Base64.encodeToString(hash, android.util.Base64.NO_WRAP)
    }
}
