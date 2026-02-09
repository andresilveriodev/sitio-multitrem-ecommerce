# Exemplos de Implementação Frontend

Este diretório contém exemplos práticos de implementação do formulário de cadastro de usuários.

## Arquivos Incluídos

- `registration-example.tsx` - Componente React completo com TypeScript
- `registration-example.css` - Estilos CSS modernos e responsivos
- `README.md` - Este arquivo

## Como Usar

### 1. Instalação

Copie os arquivos para seu projeto React:

```bash
# Copie os arquivos para seu projeto
cp registration-example.tsx src/components/RegistrationForm.tsx
cp registration-example.css src/components/RegistrationForm.css
```

### 2. Importação

```tsx
import RegistrationForm from './components/RegistrationForm';
import './components/RegistrationForm.css';
```

### 3. Uso no App

```tsx
import React from 'react';
import RegistrationForm from './components/RegistrationForm';

function App() {
  return (
    <div className="App">
      <RegistrationForm />
    </div>
  );
}
```

## Características do Exemplo

### ✅ Funcionalidades Implementadas

- **Validação em tempo real** - Campos são validados conforme o usuário digita
- **Validação no blur** - Campos são validados quando perdem o foco
- **Estados visuais** - Feedback visual para campos válidos/inválidos
- **Loading state** - Spinner durante o envio
- **Mensagens de erro** - Erros específicos para cada campo
- **Mensagem de sucesso** - Feedback positivo após cadastro
- **Redirecionamento** - Redireciona para login após sucesso
- **Responsivo** - Funciona em desktop e mobile
- **Acessível** - Labels, focus states, navegação por teclado

### 🎨 Design Features

- **Gradiente moderno** - Background com gradiente
- **Card elevado** - Sombras e bordas arredondadas
- **Animações suaves** - Transições e animações CSS
- **Estados visuais** - Cores diferentes para válido/erro
- **Spinner customizado** - Loading spinner animado
- **Tipografia clara** - Hierarquia visual bem definida

### 🔧 Validações Implementadas

- **Email válido** - Regex para formato de email
- **Campos obrigatórios** - Validação de campos vazios
- **Comprimento mínimo/máximo** - Limites de caracteres
- **Caracteres especiais** - Regex para nomes (apenas letras)
- **Senha forte** - Regex para senha complexa (opcional)

## Personalização

### Cores

Para alterar as cores, modifique as variáveis CSS no arquivo `.css`:

```css
/* Cores principais */
--primary-color: #667eea;
--secondary-color: #764ba2;
--success-color: #27ae60;
--error-color: #e74c3c;
--warning-color: #f39c12;
```

### Validações

Para modificar as validações, edite o objeto `validations`:

```typescript
const validations = {
  username: {
    required: true,
    minLength: 3,
    maxLength: 50,
    pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    message: "Username deve ser um email válido"
  },
  // ... outras validações
};
```

### Endpoint da API

Para alterar o endpoint da API:

```typescript
const registerUser = async (userData: RegistrationForm): Promise<RegistrationResponse> => {
  const response = await fetch('/auth/register', { // ← Altere aqui
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  // ...
};
```

## Testes

### Teste Manual

1. Abra o formulário no navegador
2. Teste validações em tempo real
3. Teste envio com dados válidos
4. Teste envio com dados inválidos
5. Teste responsividade em mobile

### Teste Automatizado

```typescript
// Exemplo de teste com Jest + Testing Library
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RegistrationForm from './RegistrationForm';

test('should validate email format', async () => {
  render(<RegistrationForm />);
  
  const emailInput = screen.getByLabelText(/email/i);
  fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
  fireEvent.blur(emailInput);
  
  await waitFor(() => {
    expect(screen.getByText(/email deve ter formato válido/i)).toBeInTheDocument();
  });
});
```

## Troubleshooting

### Problemas Comuns

1. **Erro de CORS**
   - Configure o proxy no `package.json`:
   ```json
   {
     "proxy": "http://localhost:8001"
   }
   ```

2. **Erro de validação**
   - Verifique se o backend está rodando
   - Confirme se o endpoint está correto

3. **Estilos não carregam**
   - Verifique se o arquivo CSS foi importado
   - Confirme se o caminho está correto

### Debug

Para debug, adicione logs:

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  console.log('Form data:', formData); // Debug
  
  try {
    const response = await registerUser(formData);
    console.log('Response:', response); // Debug
  } catch (error) {
    console.error('Error:', error); // Debug
  }
};
```

## Próximos Passos

1. **Integrar com seu backend** - Ajuste o endpoint da API
2. **Personalizar design** - Modifique cores e estilos
3. **Adicionar campos** - Inclua campos específicos do seu negócio
4. **Implementar testes** - Adicione testes automatizados
5. **Configurar monitoramento** - Adicione analytics e logs

## Suporte

Para dúvidas sobre implementação:
- Consulte o `FRONTEND_REGISTRATION_GUIDE.md`
- Verifique a documentação da API
- Entre em contato com o time de backend

---

**Versão**: 1.0  
**Última atualização**: Janeiro 2024  
**Autor**: Time de Backend - Auth Service

