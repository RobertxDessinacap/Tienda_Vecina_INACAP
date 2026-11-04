@echo off
chcp 65001 > nul
echo Deteniendo procesos de Django, Vite/Node y PostgreSQL...
taskkill /FI "WINDOWTITLE eq Inacap E-Commerce Backend*" /T /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq Inacap E-Commerce Frontend*" /T /F > nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /PID %%a /F > nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173') do taskkill /PID %%a /F > nul 2>&1
echo Servidores detenidos.
pause
