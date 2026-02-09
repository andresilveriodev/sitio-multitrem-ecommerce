# Virtual Environment - Auth Service

## 🐍 Configuração da Virtual Environment

Este módulo possui uma virtual environment isolada para garantir compatibilidade e evitar conflitos de dependências.

### 📋 Pré-requisitos

- Python 3.12+ (configurado para Python 3.12.5)
- pip (gerenciador de pacotes Python)

### 🚀 Como usar

#### Windows (PowerShell)
```powershell
# Ativar virtual environment
.\activate_venv.ps1

# Ou manualmente:
.\venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt)
```cmd
# Ativar virtual environment
activate_venv.bat

# Ou manualmente:
venv\Scripts\activate.bat
```

#### Linux/Mac
```bash
# Ativar virtual environment
source venv/bin/activate
```

### 📦 Instalação de Dependências

Com a virtual environment ativada:

```bash
# Instalar todas as dependências
pip install -r requirements.txt

# Verificar instalação
python -c "import fastapi, uvicorn, sqlalchemy, pydantic, keycloak; print('✅ Dependências OK!')"
```

### 🔧 Dependências Principais

- **FastAPI 0.104.1**: Framework web de alta performance
- **Uvicorn 0.24.0**: Servidor ASGI
- **SQLAlchemy 2.0.23**: ORM para banco de dados
- **Pydantic 2.5.0**: Validação de dados
- **Python-Keycloak 3.7.0**: Integração com Keycloak
- **Redis 5.0.1**: Cache e mensageria
- **Structlog 23.2.0**: Logging estruturado
- **AsyncPG 0.29.0**: Driver PostgreSQL assíncrono
- **Psycopg2-binary 2.9.9**: Driver PostgreSQL síncrono
- **Email-validator 2.1.0**: Validação de email

### ⚠️ Notas Importantes

1. **Python 3.12**: Configurado para Python 3.12.5 para máxima compatibilidade
2. **Compatibilidade**: Todas as dependências são compatíveis com Python 3.12
3. **Isolamento**: Cada serviço tem sua própria virtual environment
4. **Ativação**: Sempre ative a virtual environment antes de trabalhar no projeto

### 🧪 Testando a Instalação

```bash
# Com virtual environment ativada
python -c "
import fastapi
import uvicorn
import sqlalchemy
import pydantic
import keycloak
import redis
import structlog
import asyncpg
import psycopg2
print('✅ Todas as dependências estão funcionando!')
"
```

### 🚫 Desativar Virtual Environment

```bash
deactivate
```

### 🔄 Recriar Virtual Environment

Se houver problemas:

```bash
# Remover virtual environment atual
rm -rf venv/  # Linux/Mac
# ou
Remove-Item -Recurse -Force venv  # Windows PowerShell

# Criar nova virtual environment com Python 3.12
py -3.12 -m venv venv

# Ativar e instalar dependências
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### 📁 Estrutura

```
auth_service/
├── venv/                    # Virtual environment (Python 3.12)
├── requirements.txt         # Dependências
├── activate_venv.ps1       # Script PowerShell
├── activate_venv.bat       # Script CMD
├── .gitignore              # Arquivos ignorados
├── db_session.py           # Configuração de sessão local
└── README_VENV.md         # Este arquivo
```

### 🎯 Status Atual

- ✅ Virtual environment criada com Python 3.12.5
- ✅ Todas as dependências instaladas com sucesso
- ✅ Compatibilidade verificada
- ✅ Aplicação FastAPI criada com sucesso
- ✅ Módulos independentes (sem dependência do shared)
- ✅ Pronto para desenvolvimento e teste

### 🔧 Correções Implementadas

1. **Dependências**: Atualizadas para versões compatíveis com Python 3.12
2. **Email-validator**: Adicionado para validação de email no Pydantic
3. **Módulos independentes**: Criados `db_session.py` e base local para evitar dependência do módulo `shared`
4. **OAuth2 scheme**: Criado localmente para evitar conflitos
5. **Modelos**: Adicionado `UserResponse` que estava faltando

### 🚀 Como testar o serviço

```bash
# Com virtual environment ativada
python main.py
```

O serviço estará disponível em: `http://localhost:8001`
