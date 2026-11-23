@echo off
chcp 65001 > nul
echo Deteniendo procesos locales de Tienda Vecina de forma segura...

taskkill /FI "WINDOWTITLE eq TiendaVecina Backend*" /T > nul 2>&1
taskkill /FI "WINDOWTITLE eq TiendaVecina Frontend*" /T > nul 2>&1
taskkill /FI "WINDOWTITLE eq Inacap E-Commerce Backend*" /T > nul 2>&1
taskkill /FI "WINDOWTITLE eq Inacap E-Commerce Frontend*" /T > nul 2>&1

if exist "%USERPROFILE%\pgsql\pgsql\bin\pg_ctl.exe" (
    if exist "%USERPROFILE%\pgsql\data\postmaster.pid" (
        echo Deteniendo PostgreSQL portable ordenadamente...
        "%USERPROFILE%\pgsql\pgsql\bin\pg_ctl.exe" -D "%USERPROFILE%\pgsql\data" stop -m fast > nul 2>&1
    )
)

echo Servicios de Tienda Vecina detenidos de forma segura.
pause
