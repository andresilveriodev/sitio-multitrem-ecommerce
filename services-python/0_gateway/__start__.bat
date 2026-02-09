@echo off
REM Script de inicialização do Gateway Service
REM Ativa o ambiente virtual e inicia o servidor Uvicorn

echo 🚀 Iniciando Gateway Service...

REM Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call .\venv\Scripts\activate.bat

if errorlevel 1 (
    echo ❌ Erro ao ativar ambiente virtual
    exit /b 1
)

REM Iniciar aplicação Uvicorn
echo 🚀 Iniciando servidor Uvicorn na porta 8000...
echo 📖 Documentação disponível em: http://localhost:8000/docs
echo 🔍 Health check: http://localhost:8000/health
echo.
echo Pressione Ctrl+C para parar
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000







