#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "==================================================="
echo "Iniciando Tienda Vecina (PostgreSQL + Gunicorn + Frontend)"
echo "==================================================="

# Asegurar que PostgreSQL está activo
if command -v systemctl >/dev/null 2>&1; then
    if ! systemctl is-active --quiet postgresql; then
        echo "Iniciando servicio PostgreSQL..."
        sudo systemctl start postgresql
    fi
fi

echo "[1/2] Iniciando Backend Django via Gunicorn (127.0.0.1:8000)..."
cd "$DIR/backend"
PYTHON_BIN="./.venv/bin/python"
GUNICORN_BIN="./.venv/bin/gunicorn"
if [ ! -x "$GUNICORN_BIN" ]; then
    echo "Error: Gunicorn no encontrado en backend/.venv/bin/gunicorn. Ejecuta 'pip install -r requirements.txt'."
    exit 1
fi
nohup "$GUNICORN_BIN" config.wsgi:application --bind 127.0.0.1:8000 --workers 4 --timeout 60 > "$DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$DIR/backend.pid"

echo "[2/2] Iniciando Frontend Vue 3 + Vite (Puerto 5173)..."
cd "$DIR/frontend"
nohup npm run dev -- --host 127.0.0.1 --port 5173 > "$DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$DIR/frontend.pid"

echo ""
echo "==================================================="
echo "Servidores iniciados en segundo plano."
echo "Frontend:    http://127.0.0.1:5173"
echo "Backend API: http://127.0.0.1:8000/api/v1/"
echo "Logs en:     $DIR/backend.log y $DIR/frontend.log"
echo "==================================================="
