# Multitrem App - Android

App Android para gerenciamento de pedidos offline/online com autenticação híbrida (Keycloak + Offline).

## 📋 Características

- ✅ Autenticação híbrida: Login online via Keycloak (OAuth2 + PKCE) e login offline com biometria/PIN
- ✅ Funcionamento totalmente offline para criar e listar pedidos
- ✅ Armazenamento local seguro com Room Database
- ✅ Criptografia de dados sensíveis com Android Keystore + EncryptedSharedPreferences
- ✅ Arquitetura limpa (MVVM + Repository Pattern)
- ✅ UI moderna com Jetpack Compose

## 🏗️ Arquitetura

```
app/
├── data/
│   ├── database/          # Room entities, DAOs, converters
│   └── repository/         # Implementações dos repositórios
├── domain/
│   ├── models/            # Modelos de domínio
│   └── usecases/          # Casos de uso
├── auth/
│   ├── KeycloakAuthService.kt    # Autenticação Keycloak
│   ├── OfflineAuthManager.kt     # Autenticação offline (biometria/PIN)
│   ├── SessionManager.kt         # Gerenciador de sessão
│   └── AuthStateManager.kt       # Persistência de estado de auth
├── ui/
│   ├── screens/           # Telas Compose
│   ├── viewmodels/        # ViewModels
│   └── theme/             # Tema do app
└── core/
    ├── ProductSeeder.kt    # Seed inicial de produtos
    └── result/            # Result wrapper
```

## 🔧 Configuração

### 1. Configurar Keycloak

#### Informações do Servidor Keycloak

O projeto já está configurado com as seguintes informações do Keycloak:

```yaml
URL Base: https://auth.rendacontinua.com/auth
Realm: auth_sso
Issuer: https://auth.rendacontinua.com/auth/realms/auth_sso
```

#### No servidor Keycloak (Admin Console):

1. Acesse o Keycloak Admin Console: `https://auth.rendacontinua.com/auth/admin`
2. Selecione o Realm: **`auth_sso`**
3. Vá em **Clients** → **Create client**
4. Configure:
   - **Client ID**: `multitrem-android-app`
   - **Client Protocol**: `openid-connect`
   - **Access Type**: `public` (para apps móveis com PKCE)
   - **Standard Flow Enabled**: `ON`
   - **Direct Access Grants Enabled**: `OFF` (recomendado para segurança)
   - **Valid Redirect URIs**: 
     ```
     com.multitrem.app://oauth/callback
     ```
   - **Web Origins**: `*` (ou deixe vazio para apps móveis)
   - **PKCE Code Challenge Method**: `S256` (recomendado)

5. Salve o cliente

#### Configuração no App Android

A configuração já está definida em `app/build.gradle.kts`:

```kotlin
buildConfigField("String", "KEYCLOAK_ISSUER", "\"https://auth.rendacontinua.com/auth/realms/auth_sso\"")
buildConfigField("String", "KEYCLOAK_CLIENT_ID", "\"multitrem-android-app\"")
buildConfigField("String", "KEYCLOAK_REDIRECT_URI", "\"com.multitrem.app://oauth/callback\"")
```

**⚠️ IMPORTANTE**: Certifique-se de que o Client ID `multitrem-android-app` foi criado no Keycloak antes de executar o app!

### 2. Build e Execução

```bash
# Build do projeto
./gradlew build

# Instalar no dispositivo/emulador
./gradlew installDebug

# Executar testes
./gradlew test
```

### 3. Configuração do Ambiente de Desenvolvimento

1. Instale o Android Studio (versão mais recente)
2. Abra o projeto
3. Sincronize o Gradle
4. Configure um emulador Android (API 24+) ou conecte um dispositivo físico
5. Execute o app

## 🔐 Autenticação

### Login Online (Keycloak)

1. O usuário toca em "Login Online"
2. O app abre o navegador/Chrome Custom Tabs
3. Usuário faz login no Keycloak
4. Keycloak redireciona para `com.multitrem.app://oauth/callback`
5. App recebe o código de autorização e troca por tokens
6. Tokens são salvos criptografados
7. Autenticação offline é habilitada automaticamente

### Login Offline

**Pré-requisito**: O usuário deve ter feito login online pelo menos uma vez no dispositivo.

1. O usuário toca em "Login Offline"
2. O app tenta autenticação biométrica primeiro:
   - Se disponível, mostra o BiometricPrompt
   - Se não disponível ou falhar, solicita PIN
3. PIN é validado usando hash PBKDF2
4. Se válido, sessão offline é criada (válida por 7 dias)

**Regras de Segurança**:
- PIN deve ter 4-6 dígitos
- Máximo de 5 tentativas antes de bloqueio (15 minutos)
- Sessão offline expira em 7 dias sem revalidação online
- PIN nunca é armazenado em texto puro (apenas salt + hash)

### Logout

- Remove todos os tokens
- Desabilita autenticação offline
- Limpa credenciais armazenadas

## 📱 Funcionalidades

### Lista de Pedidos

- Exibe pedidos do dia atual
- Mostra total do dia
- Permite alterar status (PENDENTE, SEPARANDO, ENTREGUE, CANCELADO)
- Compartilhar pedido no WhatsApp

### Novo Pedido

- Seleciona cliente (nome, telefone opcional)
- Escolhe tipo de entrega (ENTREGA/RETIRADA)
- Escolhe forma de pagamento (PIX/DINHEIRO)
- Adiciona observação
- Seleciona produtos e quantidades
- Calcula total automaticamente

### Configurações

- Alterar PIN offline
- Logout

## 🧪 Testando Offline

### Modo Avião

1. Faça login online uma vez
2. Configure o PIN offline (se solicitado)
3. Ative o modo avião no dispositivo
4. Abra o app
5. Toque em "Login Offline"
6. Use biometria ou PIN
7. O app deve funcionar normalmente para criar/listar pedidos

### Resetar App/Credenciais

**Opção 1: Via Settings do Android**
1. Configurações → Apps → Multitrem → Armazenamento
2. Limpar dados / Limpar cache

**Opção 2: Desinstalar e Reinstalar**
```bash
adb uninstall com.multitrem.app
./gradlew installDebug
```

**Opção 3: Via ADB (desenvolvimento)**
```bash
adb shell pm clear com.multitrem.app
```

## 🔒 Segurança

### Armazenamento Seguro

- **Tokens OAuth**: Armazenados em `EncryptedSharedPreferences` usando Android Keystore
- **PIN**: Apenas hash PBKDF2 + salt (nunca texto puro)
- **Dados do app**: Room Database (não criptografado, mas isolado por app)

### Android Keystore

O app usa Android Keystore para gerar e armazenar chaves de criptografia. As chaves nunca saem do dispositivo e são protegidas pelo hardware (quando disponível).

## 📦 Dependências Principais

- **Jetpack Compose**: UI moderna
- **Room**: Banco de dados local
- **AppAuth**: OAuth2/OpenID Connect
- **Security Crypto**: Criptografia de dados
- **Biometric**: Autenticação biométrica
- **Coroutines**: Programação assíncrona
- **Kotlinx DateTime**: Manipulação de datas

## 🐛 Troubleshooting

### Erro: "Redirect URI mismatch"

- Verifique se o redirect URI no Keycloak está exatamente como: `com.multitrem.app://oauth/callback`
- Certifique-se de que o `KEYCLOAK_REDIRECT_URI` no `build.gradle.kts` corresponde
- No Keycloak Admin, verifique se o Client `multitrem-android-app` existe e está configurado corretamente

### Erro: "Client not found" ou "Invalid client"

- Certifique-se de que o Client ID `multitrem-android-app` foi criado no Keycloak
- Verifique se está no realm correto: `auth_sso`
- Confirme que o Access Type está como `public` (para PKCE)

### Erro: "Offline não habilitado"

- O usuário precisa fazer login online pelo menos uma vez
- Verifique se o login online foi concluído com sucesso

### Biometria não funciona

- Verifique se o dispositivo suporta biometria
- Verifique se há biometria cadastrada nas configurações do dispositivo
- O app usa fallback para PIN automaticamente

### PIN bloqueado

- Aguarde 15 minutos
- Ou limpe os dados do app (isso também remove o PIN)

## 📝 Notas de Desenvolvimento

### Seed de Produtos

O app vem com 5 produtos pré-cadastrados. Para modificar, edite `core/ProductSeeder.kt`.

### Expiração Offline

A expiração padrão é de 7 dias. Para alterar, modifique `OFFLINE_EXPIRY_DAYS` em `OfflineAuthManager.kt`.

### Limite de Tentativas de PIN

Padrão: 5 tentativas. Para alterar, modifique `MAX_PIN_ATTEMPTS` em `OfflineAuthManager.kt`.

## 📄 Licença

Este projeto é parte do sistema Multitrem E-commerce.

## 👥 Contribuindo

1. Faça fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

Para questões ou problemas, abra uma issue no repositório.
