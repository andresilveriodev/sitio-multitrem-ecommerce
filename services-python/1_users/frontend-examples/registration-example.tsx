import React, { useState } from 'react';
import './registration-example.css';

// Interfaces TypeScript
interface RegistrationForm {
  cpf: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  password?: string;
}

interface RegistrationResponse {
  success: boolean;
  keycloak_id?: string;
  message: string;
  user_data?: {
    id: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    enabled: boolean;
    emailVerified: boolean;
    attributes: Record<string, string[]>;
  };
}

// Função para validar CPF
const validateCPF = (cpf: string): boolean => {
  cpf = cpf.replace(/[^\d]/g, '');
  if (cpf.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(cpf)) return false;
  
  let soma = 0;
  for (let i = 0; i < 9; i++) {
    soma += parseInt(cpf[i]) * (10 - i);
  }
  let resto = soma % 11;
  let digito1 = resto < 2 ? 0 : 11 - resto;
  
  soma = 0;
  for (let i = 0; i < 10; i++) {
    soma += parseInt(cpf[i]) * (11 - i);
  }
  resto = soma % 11;
  let digito2 = resto < 2 ? 0 : 11 - resto;
  
  return cpf.slice(-2) === `${digito1}${digito2}`;
};

// Função para validar username (CPF ou email)
const validateUsername = (username: string): boolean => {
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailPattern.test(username) || validateCPF(username);
};

// Validações
const validations = {
  cpf: {
    required: true,
    minLength: 11,
    maxLength: 20,
    validate: validateCPF,
    message: "CPF deve ser válido"
  },
  email: {
    required: true,
    pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    message: "Email deve ter formato válido"
  },
  first_name: {
    required: true,
    minLength: 2,
    maxLength: 100,
    pattern: /^[a-zA-ZÀ-ÿ\s]+$/,
    message: "Nome deve ter entre 2 e 100 caracteres"
  },
  last_name: {
    required: true,
    minLength: 2,
    maxLength: 100,
    pattern: /^[a-zA-ZÀ-ÿ\s]+$/,
    message: "Sobrenome deve ter entre 2 e 100 caracteres"
  },
  phone: {
    required: true,
    minLength: 10,
    maxLength: 20,
    pattern: /^\+[1-9]\d{1,3}-\d{1,4}-\d{4,15}$/,
    message: "Telefone deve estar no formato internacional: +pais-dd-telefone"
  },
  password: {
    required: false,
    minLength: 6,
    pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
    message: "Senha deve ter pelo menos 8 caracteres, incluindo maiúscula, minúscula, número e caractere especial"
  }
};

// Função de validação
const validateField = (field: keyof RegistrationForm, value: string): string | null => {
  const validation = validations[field];
  
  if (validation.required && !value) {
    return `${field} é obrigatório`;
  }
  
  if (value && 'minLength' in validation && validation.minLength && value.length < validation.minLength) {
    return `${field} deve ter pelo menos ${validation.minLength} caracteres`;
  }
  
  if (value && 'maxLength' in validation && validation.maxLength && value.length > validation.maxLength) {
    return `${field} deve ter no máximo ${validation.maxLength} caracteres`;
  }
  
  if (value && 'pattern' in validation && validation.pattern && !validation.pattern.test(value)) {
    return validation.message;
  }
  
  if (value && 'validate' in validation && validation.validate && !validation.validate(value)) {
    return validation.message;
  }
  
  return null;
};

// Função para validar todo o formulário
const validateForm = (formData: RegistrationForm): Partial<RegistrationForm> => {
  const errors: Partial<RegistrationForm> = {};
  
  Object.keys(formData).forEach((field) => {
    const error = validateField(field as keyof RegistrationForm, formData[field as keyof RegistrationForm] || '');
    if (error) {
      errors[field as keyof RegistrationForm] = error;
    }
  });
  
  return errors;
};

// Função para registrar usuário
const registerUser = async (userData: RegistrationForm): Promise<RegistrationResponse> => {
  try {
    const response = await fetch('/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erro no cadastro');
    }

    return await response.json();
  } catch (error) {
    throw new Error(`Falha no cadastro: ${error instanceof Error ? error.message : 'Erro desconhecido'}`);
  }
};

// Componente principal
export const RegistrationForm: React.FC = () => {
  const [formData, setFormData] = useState<RegistrationForm>({
    cpf: '',
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    password: ''
  });
  
  const [errors, setErrors] = useState<Partial<RegistrationForm>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [touched, setTouched] = useState<Partial<RegistrationForm>>({});

  // Handler para mudanças nos campos
  const handleChange = (field: keyof RegistrationForm, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Validar em tempo real se o campo foi tocado
    if (touched[field]) {
      const error = validateField(field, value);
      setErrors(prev => ({ ...prev, [field]: error || undefined }));
    }
  };

  // Handler para blur (campo perdeu foco)
  const handleBlur = (field: keyof RegistrationForm) => {
    setTouched(prev => ({ ...prev, [field]: true }));
    const error = validateField(field, formData[field] || '');
    setErrors(prev => ({ ...prev, [field]: error || undefined }));
  };

  // Handler para submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors({});

    try {
      // Marcar todos os campos como tocados
      setTouched({
        cpf: true,
        email: true,
        first_name: true,
        last_name: true,
        phone: true,
        password: true
      });

      // Validar formulário
      const validationErrors = validateForm(formData);
      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors);
        setIsLoading(false);
        return;
      }

      // Enviar requisição
      const response = await registerUser(formData);
      
      if (response.success) {
        setSuccess(true);
        // Redirecionar para login após 3 segundos
        setTimeout(() => {
          window.location.href = '/login';
        }, 3000);
      }
    } catch (error) {
      setErrors({ cpf: error instanceof Error ? error.message : 'Erro desconhecido' });
    } finally {
      setIsLoading(false);
    }
  };

  // Verificar se o formulário é válido
  const isFormValid = () => {
    return Object.keys(validateForm(formData)).length === 0;
  };

  return (
    <div className="registration-container">
      <div className="registration-card">
        <h2>Cadastro de Usuário</h2>
        <p className="subtitle">Preencha os dados para criar sua conta</p>

        <form onSubmit={handleSubmit} className="registration-form">
          {/* CPF */}
          <div className="form-group">
            <label htmlFor="cpf">CPF *</label>
            <input
              id="cpf"
              type="text"
              value={formData.cpf}
              onChange={(e) => handleChange('cpf', e.target.value)}
              onBlur={() => handleBlur('cpf')}
              className={`form-input ${errors.cpf ? 'error' : ''} ${touched.cpf && !errors.cpf ? 'valid' : ''}`}
              placeholder="123.456.789-00"
              required
            />
            {errors.cpf && <span className="error-message">{errors.cpf}</span>}
          </div>

          {/* Email */}
          <div className="form-group">
            <label htmlFor="email">Email *</label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              onBlur={() => handleBlur('email')}
              className={`form-input ${errors.email ? 'error' : ''} ${touched.email && !errors.email ? 'valid' : ''}`}
              placeholder="seu@email.com"
              required
            />
            {errors.email && <span className="error-message">{errors.email}</span>}
          </div>

          {/* Telefone */}
          <div className="form-group">
            <label htmlFor="phone">Telefone *</label>
            <input
              id="phone"
              type="tel"
              value={formData.phone}
              onChange={(e) => handleChange('phone', e.target.value)}
              onBlur={() => handleBlur('phone')}
              className={`form-input ${errors.phone ? 'error' : ''} ${touched.phone && !errors.phone ? 'valid' : ''}`}
              placeholder="+55-11-99999-9999"
              required
            />
            {errors.phone && <span className="error-message">{errors.phone}</span>}
            <small className="help-text">Formato internacional: +pais-dd-telefone</small>
          </div>

          {/* Nome */}
          <div className="form-group">
            <label htmlFor="first_name">Nome *</label>
            <input
              id="first_name"
              type="text"
              value={formData.first_name}
              onChange={(e) => handleChange('first_name', e.target.value)}
              onBlur={() => handleBlur('first_name')}
              className={`form-input ${errors.first_name ? 'error' : ''} ${touched.first_name && !errors.first_name ? 'valid' : ''}`}
              placeholder="João"
              required
            />
            {errors.first_name && <span className="error-message">{errors.first_name}</span>}
          </div>

          {/* Sobrenome */}
          <div className="form-group">
            <label htmlFor="last_name">Sobrenome *</label>
            <input
              id="last_name"
              type="text"
              value={formData.last_name}
              onChange={(e) => handleChange('last_name', e.target.value)}
              onBlur={() => handleBlur('last_name')}
              className={`form-input ${errors.last_name ? 'error' : ''} ${touched.last_name && !errors.last_name ? 'valid' : ''}`}
              placeholder="Silva"
              required
            />
            {errors.last_name && <span className="error-message">{errors.last_name}</span>}
          </div>

          {/* Senha */}
          <div className="form-group">
            <label htmlFor="password">Senha (opcional)</label>
            <input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => handleChange('password', e.target.value)}
              onBlur={() => handleBlur('password')}
              className={`form-input ${errors.password ? 'error' : ''} ${touched.password && !errors.password ? 'valid' : ''}`}
              placeholder="Mínimo 6 caracteres"
            />
            {errors.password && <span className="error-message">{errors.password}</span>}
            <small className="help-text">
              Se não informar, uma senha temporária será gerada e enviada por email
            </small>
          </div>

          {/* Botão de Submit */}
          <button 
            type="submit" 
            disabled={isLoading || !isFormValid()}
            className="submit-button"
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Cadastrando...
              </>
            ) : (
              'Criar Conta'
            )}
          </button>
        </form>

        {/* Mensagem de Sucesso */}
        {success && (
          <div className="success-message">
            <div className="success-icon">✅</div>
            <h3>Cadastro realizado com sucesso!</h3>
            <p>Verifique seu email para ativar sua conta.</p>
            <p><strong>Importante:</strong> Para fazer login, você pode usar seu CPF ou email como usuário.</p>
            <p>Você será redirecionado para o login em alguns segundos...</p>
          </div>
        )}

        {/* Link para Login */}
        <div className="login-link">
          <p>
            Já tem uma conta? <a href="/login">Faça login</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegistrationForm;
