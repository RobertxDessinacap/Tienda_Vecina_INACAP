@echo off
chcp 65001 > nul
echo ===================================================
echo Iniciando Inacap E-Commerce (PostgreSQL + Backend + Frontend)
echo ===================================================

cd /d "%~dp0"

echo [1/3] Verificando servicio PostgreSQL...
sc start postgresql_inacap > nul 2>&1
if exist "%USERPROFILE%\pgsql\pgsql\bin\postgres.exe" (
    netstat -ano | findstr :5432 > nul 2>&1
    if errorlevel 1 (
        start "Inacap PostgreSQL" /min "%USERPROFILE%\pgsql\pgsql\bin\postgres.exe" -D "%USERPROFILE%\pgsql\data"
    )
)

echo [2/3] Iniciando Backend Django (Puerto 8000)...
start "Inacap E-Commerce Backend" cmd /k "cd backend && call .venv\Scripts\activate.bat && python manage.py runserver 127.0.0.1:8000"

echo [3/3] Iniciando Frontend Vue 3 + Vite (Puerto 5173)...
start "Inacap E-Commerce Frontend" cmd /k "cd frontend && npm run dev -- --host 0.0.0.0"

echo.
echo ===================================================
echo Servidores iniciados en ventanas separadas.
echo Frontend: http://localhost:5173
echo Backend API: http://127.0.0.1:8000/api/v1/
echo Base de Datos: PostgreSQL 16 (127.0.0.1:5432)
echo ===================================================
timeout /t 5
