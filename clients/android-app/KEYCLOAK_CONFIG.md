# 🔐 Configuração Keycloak para App Android

Este documento contém todas as informações necessárias para configurar o Keycloak para o app Android Multitrem.

## 📋 Informações do Servidor

```yaml
# URL Base do Servidor de Autenticação
KEYCLOAK_AUTH_SERVER_URL: "https://auth.rendacontinua.com/auth"

# Realm (Domínio de Autenticação)
KEYCLOAK_REALM: "auth_sso"

# Issuer (URL completa do realm)
KEYCLOAK_ISSUER: "https://auth.rendacontinua.com/auth/realms/auth_sso"

# Endpoint de Configuração OpenID Connect
OPENID_CONFIG_URL: "https://auth.rendacontinua.com/auth/realms/auth_sso/.well-known/openid-configuration"
```

## 🔗 Endpoints Principais

```yaml
# Token Endpoint (para obter tokens)
TOKEN_ENDPOINT: "https://auth.rendacontinua.com/auth/realms/auth_sso/protocol/openid-connect/token"

# Authorization Endpoint (para login)
AUTHORIZATION_ENDPOINT: "https://auth.rendacontinua.com/auth/realms/auth_sso/protocol/openid-connect/auth"

# UserInfo Endpoint (para obter dados do usuário)
USERINFO_ENDPOINT: "https://auth.rendacontinua.com/auth/realms/auth_sso/protocol/openid-connect/userinfo"

# Logout Endpoint
LOGOUT_ENDPOINT: "https://auth.rendacontinua.com/auth/realms/auth_sso/protocol/openid-connect/logout"

# JWKS Endpoint (para validação de tokens)
JWKS_URI: "https://auth.rendacontinua.com/auth/realms/auth_sso/protocol/openid-connect/certs"
```

## 📱 Configuração do Cliente Android

### Passo a Passo no Keycloak Admin Console

1. **Acesse o Admin Console**
   - URL: `https://auth.rendacontinua.com/auth/admin`
   - Faça login com credenciais de administrador

2. **Selecione o Realm**
   - No canto superior esquerdo, selecione: **`auth_sso`**

3. **Criar o Cliente**
   - No menu lateral, clique em **"Clients"**
   - Clique no botão **"Create client"** (canto superior direito)
   - Preencha:
     - **Client ID**: `multitrem-android-app`
     - **Client Protocol**: `openid-connect`
     - Clique em **"Next"**

4. **Configurar Capabilities**
   - **Client authentication**: `OFF` (para usar PKCE)
   - **Authorization**: `OFF`
   - **Authentication flow**: `Standard flow` → `ON`
   - Clique em **"Next"**

5. **Configurar Login Settings**
   - **Root URL**: (deixe vazio ou `com.multitrem.app://`)
   - **Home URL**: (deixe vazio)
   - **Valid redirect URIs**: 
     ```
     com.multitrem.app://oauth/callback
     ```
     ⚠️ **IMPORTANTE**: Deve ser exatamente este valor, sem espaços extras!
   
   - **Valid post logout redirect URIs**: (deixe vazio ou adicione se necessário)
   - **Web origins**: `*` (ou deixe vazio)
   - Clique em **"Save"**

6. **Configurar Advanced Settings** (aba "Advanced")
   - **Proof Key for Code Exchange Code Challenge Method**: `S256` (recomendado)
   - **Access token lifespan**: (padrão ou conforme necessário)
   - **Refresh token lifespan**: (padrão ou conforme necessário)

### Configurações Recomendadas

```yaml
Client ID: multitrem-android-app
Client Protocol: openid-connect
Access Type: public
Standard Flow Enabled: true
Direct Access Grants Enabled: false (mais seguro)
Valid Redirect URIs: com.multitrem.app://oauth/callback
Web Origins: * (ou vazio)
PKCE Code Challenge Method: S256
```

## 🔄 Fluxo de Autenticação

O app Android usa **Authorization Code Flow com PKCE** (Proof Key for Code Exchange):

1. App gera `code_verifier` e `code_challenge`
2. App redireciona para Keycloak com `code_challenge`
3. Usuário faz login no Keycloak
4. Keycloak redireciona para `com.multitrem.app://oauth/callback` com `authorization_code`
5. App troca o código pelo token usando `code_verifier`
6. Tokens são armazenados de forma segura no dispositivo

## 🔒 Segurança

### Armazenamento de Tokens

- Tokens são armazenados em `EncryptedSharedPreferences` usando Android Keystore
- Chaves de criptografia nunca saem do dispositivo
- PIN é armazenado apenas como hash PBKDF2 (nunca texto puro)

### PKCE (Proof Key for Code Exchange)

- Usa `S256` (SHA256) para gerar o code challenge
- Code verifier é gerado aleatoriamente a cada requisição
- Aumenta a segurança para apps públicos (sem client secret)

## 📝 Estrutura do Token JWT

Após autenticação bem-sucedida, o token JWT contém:

```json
{
  "sub": "keycloak-user-id",
  "preferred_username": "username",
  "email": "user@example.com",
  "exp": 1234567890,
  "iat": 1234567890,
  "iss": "https://auth.rendacontinua.com/auth/realms/auth_sso",
  "aud": "multitrem-android-app"
}
```

## 🧪 Testando a Configuração

### 1. Verificar Cliente no Keycloak

1. Acesse: `https://auth.rendacontinua.com/auth/admin`
2. Realm: `auth_sso`
3. Clients → `multitrem-android-app`
4. Verifique se todas as configurações estão corretas

### 2. Testar no App

1. Execute o app Android
2. Toque em "Login Online"
3. Deve abrir o navegador/Chrome Custom Tabs
4. Faça login no Keycloak
5. Deve redirecionar de volta para o app
6. App deve estar autenticado

### 3. Verificar Logs

Se houver erros, verifique:
- Logcat do Android Studio
- Erros de "redirect_uri mismatch"
- Erros de "invalid client"

## 🐛 Troubleshooting

### Erro: "Invalid redirect URI"

**Causa**: O redirect URI no Keycloak não corresponde ao do app.

**Solução**:
1. Verifique no Keycloak Admin: Clients → `multitrem-android-app` → Settings
2. Confirme que "Valid redirect URIs" contém exatamente: `com.multitrem.app://oauth/callback`
3. Certifique-se de que não há espaços extras ou caracteres especiais

### Erro: "Client not found"

**Causa**: O Client ID não existe no Keycloak ou está no realm errado.

**Solução**:
1. Verifique se o Client `multitrem-android-app` foi criado
2. Confirme que está no realm `auth_sso`
3. Verifique se o Client ID no `build.gradle.kts` corresponde

### Erro: "PKCE verification failed"

**Causa**: Problema com code verifier/challenge.

**Solução**:
1. Verifique se o PKCE está habilitado no Keycloak
2. Confirme que o método é `S256`
3. Verifique se o app está gerando o code verifier corretamente

## 📚 Referências

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [AppAuth for Android](https://github.com/openid/AppAuth-Android)
- [OAuth 2.0 PKCE](https://oauth.net/2/pkce/)
- [Android Keystore System](https://developer.android.com/training/articles/keystore)

## ✅ Checklist de Configuração

- [ ] Cliente `multitrem-android-app` criado no Keycloak
- [ ] Realm `auth_sso` selecionado
- [ ] Access Type configurado como `public`
- [ ] Valid Redirect URI: `com.multitrem.app://oauth/callback`
- [ ] PKCE habilitado com método `S256`
- [ ] Standard Flow habilitado
- [ ] App Android configurado com valores corretos no `build.gradle.kts`
- [ ] Testado login online no app
- [ ] Tokens sendo armazenados corretamente
- [ ] Logout funcionando

---

**Última atualização**: Configuração baseada no servidor Keycloak em produção: `https://auth.rendacontinua.com/auth`
