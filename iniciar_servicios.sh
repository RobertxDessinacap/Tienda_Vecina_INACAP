#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "==================================================="
echo "Iniciando Inacap E-Commerce (Backend + Frontend)"
echo "==================================================="

# Asegurar que PostgreSQL está activo
if ! systemctl is-active --quiet postgresql; then
    echo "Iniciando servicio PostgreSQL..."
    sudo systemctl start postgresql
fi

echo "[1/2] Iniciando Backend Django (Puerto 8000)..."
cd "$DIR/backend"
nohup ./venv/bin/python manage.py runserver 0.0.0.0:8000 > "$DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$DIR/backend.pid"

echo "[2/2] Iniciando Frontend Vue 3 + Vite (Puerto 5173)..."
cd "$DIR/frontend"
nohup npm run dev -- --host 0.0.0.0 --port 5173 > "$DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$DIR/frontend.pid"

echo ""
echo "==================================================="
echo "Servidores iniciados en segundo plano."
echo "Frontend:   http://localhost:5173"
echo "Backend API: http://127.0.0.1:8000/api/v1/"
echo "Logs en:    $DIR/backend.log y $DIR/frontend.log"
echo "==================================================="
