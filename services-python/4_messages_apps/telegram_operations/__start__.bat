@echo off
REM Script de inicialização do Telegram Operations Service
REM Ativa o ambiente virtual e inicia o servidor Uvicorn

echo 🚀 Iniciando Telegram Operations Service...

REM Verificar se existe ambiente virtual
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Ambiente virtual não encontrado!
    echo 💡 Criando ambiente virtual...
    
    REM Criar ambiente virtual
    python -m venv venv
    
    if errorlevel 1 (
        echo ❌ Erro ao criar ambiente virtual
        exit /b 1
    )
    
    echo ✅ Ambiente virtual criado com sucesso!
    echo 💡 Instalando dependências...
    
    REM Ativar e instalar dependências
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    
    if errorlevel 1 (
        echo ❌ Erro ao instalar dependências
        exit /b 1
    )
)

REM Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Verificar se existe arquivo .env
if not exist ".env" (
    echo ⚠️  Arquivo .env não encontrado!
    if exist "env.example" (
        echo 💡 Copiando env.example para .env...
        copy env.example .env
        echo ✅ Arquivo .env criado. Configure as variáveis necessárias!
    ) else (
        echo ⚠️  Arquivo env.example não encontrado. Configure manualmente o .env
    )
)

REM Iniciar aplicação
echo 🚀 Iniciando servidor Uvicorn na porta 8021...
echo 📖 Documentação disponível em: http://localhost:8021/docs
echo 🔍 Health check: http://localhost:8021/health
echo 📱 Telegram Service: http://localhost:8021
echo.
echo Pressione Ctrl+C para parar
echo.

python main.py

pause
