# Tratamento de Usuários Existentes - SSO

## 🔄 **Visão Geral**

Este documento descreve como o sistema trata usuários que já possuem cadastro no Keycloak, considerando que é um sistema Single Sign-On (SSO).

## 🎯 **Cenários Possíveis**

### **1. Usuário com CPF Já Cadastrado**
```
CPF: 123.456.789-00 (já existe)
Email: novo@exemplo.com (diferente)
Resultado: ❌ Erro 409 - CPF duplicado
```

### **2. Usuário com Email Já Cadastrado**
```
CPF: 987.654.321-00 (novo)
Email: usuario@exemplo.com (já existe)
Resultado: ❌ Erro 409 - Email duplicado
```

### **3. Usuário com Dados Idênticos**
```
CPF: 123.456.789-00 (já existe)
Email: usuario@exemplo.com (já existe)
Resultado: ❌ Erro 409 - Usuário duplicado
```

### **4. Usuário Completamente Novo**
```
CPF: 111.222.333-44 (novo)
Email: novo@exemplo.com (novo)
Resultado: ✅ Sucesso - Usuário criado
```

## 🔍 **Verificação Prévia**

### **Endpoint de Verificação**
```
GET /auth/check-user?cpf=123.456.789-00
GET /auth/check-user?email=usuario@exemplo.com
```

### **Implementação Backend**

```python
async def check_user_exists(self, cpf: str = None, email: str = None) -> Optional[Dict[str, Any]]:
    """Verifica se usuário já existe no Keycloak por CPF ou email"""
    try:
        token = await self.get_admin_token()
        if not token:
            return None
        
        # Buscar por CPF
        if cpf:
            cpf_clean = re.sub(r'[^0-9]', '', cpf)
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users",
                    params={"username": cpf_clean},
                    headers={"Authorization": f"Bearer {token}"}
                )
                r.raise_for_status()
                users = r.json()
                if users:
                    return users[0]
        
        # Buscar por email
        if email:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{settings.KEYCLOAK_AUTH_SERVER_URL}/admin/realms/{settings.KEYCLOAK_REALM}/users",
                    params={"email": email},
                    headers={"Authorization": f"Bearer {token}"}
                )
                r.raise_for_status()
                users = r.json()
                if users:
                    return users[0]
        
        return None
        
    except Exception as e:
        logger.error("Erro ao verificar usuário existente", error=str(e))
        return None
```

## 🛡️ **Proteção no Cadastro**

### **Validação Antes da Criação**

```python
async def create_user_in_keycloak(self, user_data: Dict[str, Any]) -> Optional[str]:
    """Cria usuário no Keycloak via Admin API"""
    try:
        # Verificar se usuário já existe
        existing_user = await self.check_user_exists(cpf=cpf, email=email)
        if existing_user:
            logger.warning("Usuário já existe no Keycloak", 
                          keycloak_id=existing_user.get("id"),
                          username=existing_user.get("username"),
                          email=existing_user.get("email"))
            raise ValueError(f"Usuário já existe no sistema. CPF ou email já cadastrado.")
        
        # Continuar com a criação...
        
    except ValueError as e:
        # Re-raise para ser tratado na rota
        raise e
```

### **Tratamento na Rota**

```python
@router.post("/register", response_model=RegisterResponse)
async def register_user(request: RegisterRequest):
    try:
        keycloak_id = await keycloak_service.create_user_in_keycloak(user_data)
        
    except ValueError as e:
        # Usuário já existe
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
```

## 📱 **Implementação Frontend**

### **Verificação em Tempo Real**

```typescript
const checkUserExists = async (cpf?: string, email?: string): Promise<boolean> => {
  try {
    const params = new URLSearchParams();
    if (cpf) params.append('cpf', cpf);
    if (email) params.append('email', email);
    
    const response = await fetch(`/auth/check-user?${params}`);
    const data = await response.json();
    
    return data.exists;
  } catch (error) {
    console.error('Erro ao verificar usuário:', error);
    return false;
  }
};
```

### **Validação no Formulário**

```typescript
const handleCPFChange = async (cpf: string) => {
  setFormData(prev => ({ ...prev, cpf }));
  
  if (validateCPF(cpf)) {
    const exists = await checkUserExists(cpf);
    if (exists) {
      setErrors(prev => ({ 
        ...prev, 
        cpf: 'CPF já cadastrado no sistema. Faça login ou recupere sua senha.' 
      }));
    } else {
      setErrors(prev => ({ ...prev, cpf: undefined }));
    }
  }
};

const handleEmailChange = async (email: string) => {
  setFormData(prev => ({ ...prev, email }));
  
  if (validateEmail(email)) {
    const exists = await checkUserExists(undefined, email);
    if (exists) {
      setErrors(prev => ({ 
        ...prev, 
        email: 'Email já cadastrado no sistema. Faça login ou recupere sua senha.' 
      }));
    } else {
      setErrors(prev => ({ ...prev, email: undefined }));
    }
  }
};
```

## 🎨 **UX para Usuários Existentes**

### **Mensagens Informativas**

```typescript
// Quando CPF já existe
"CPF já cadastrado no sistema. Faça login ou recupere sua senha."

// Quando email já existe
"Email já cadastrado no sistema. Faça login ou recupere sua senha."

// Link para login
"Já tem uma conta? <a href='/login'>Faça login</a>"

// Link para recuperação
"Esqueceu sua senha? <a href='/forgot-password'>Recupere aqui</a>"
```

### **Componente de Sugestão**

```tsx
const ExistingUserSuggestion: React.FC<{ field: string }> = ({ field }) => {
  return (
    <div className="existing-user-suggestion">
      <p>Este {field} já está cadastrado no sistema.</p>
      <div className="suggestion-actions">
        <a href="/login" className="btn btn-primary">Fazer Login</a>
        <a href="/forgot-password" className="btn btn-secondary">Recuperar Senha</a>
      </div>
    </div>
  );
};
```

## 🔄 **Fluxo de Recuperação**

### **1. Usuário Tenta Cadastrar**
- Sistema verifica se CPF/email já existe
- Retorna erro 409 com mensagem clara

### **2. Usuário Clica em "Fazer Login"**
- Redirecionado para página de login
- Pode usar CPF ou email como username

### **3. Usuário Clica em "Recuperar Senha"**
- Redirecionado para recuperação de senha
- Recebe email/SMS com link de reset

### **4. Usuário Faz Login Normal**
- Acesso ao sistema via SSO
- Dados sincronizados automaticamente

## 📊 **Métricas e Monitoramento**

### **Logs Importantes**

```python
# Tentativa de cadastro duplicado
logger.warning("Tentativa de cadastro de usuário já existente", 
              cpf=user_data.cpf, email=user_data.email)

# Usuário encontrado por CPF
logger.info("Usuário encontrado por CPF", cpf=cpf_clean)

# Usuário encontrado por email
logger.info("Usuário encontrado por email", email=email)
```

### **Métricas para Acompanhar**

- Taxa de tentativas de cadastro duplicado
- Distribuição por CPF vs Email
- Taxa de conversão para login
- Taxa de uso da recuperação de senha

## 🚀 **Estratégias de Migração**

### **Para Sistemas Legados**

1. **Importação em Lote**
   - Migrar usuários existentes para Keycloak
   - Manter CPF como username
   - Preservar dados de contato

2. **Cadastro Progressivo**
   - Permitir cadastro apenas para novos usuários
   - Usuários existentes fazem login direto

3. **Sincronização Bidirecional**
   - Manter dados sincronizados entre sistemas
   - Migração gradual e transparente

## 🔧 **Configurações Keycloak**

### **Username Policy**
```
^[0-9]{11}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
```

### **Atributos Importantes**
- `cpf` - CPF limpo (username)
- `cpf_formatted` - CPF com formatação
- `phone` - Telefone internacional
- `source` - Origem do cadastro

## 📋 **Checklist de Implementação**

- [ ] Verificação prévia de usuário existente
- [ ] Tratamento de erro 409 no backend
- [ ] Validação em tempo real no frontend
- [ ] Mensagens claras para usuário
- [ ] Links para login e recuperação
- [ ] Logs detalhados para monitoramento
- [ ] Testes com usuários duplicados
- [ ] Documentação para suporte

---

**Status**: ✅ **Implementado**  
**Versão**: 1.0  
**Data**: Janeiro 2024
