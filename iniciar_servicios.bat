@echo off
chcp 65001 > nul
echo ===================================================
echo Iniciando Inacap E-Commerce (Backend + Frontend)
echo ===================================================

cd /d "%~dp0"

echo [1/2] Iniciando Backend Django (Puerto 8000)...
start "Inacap E-Commerce Backend" cmd /k "cd backend && call .venv\Scripts\activate.bat && python manage.py runserver 127.0.0.1:8000"

echo [2/2] Iniciando Frontend Vue 3 + Vite (Puerto 5173)...
start "Inacap E-Commerce Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo Servidores iniciados en ventanas separadas.
echo Frontend: http://localhost:5173
echo Backend API: http://127.0.0.1:8000/api/v1/
echo ===================================================
timeout /t 5
