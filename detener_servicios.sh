#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Deteniendo procesos de Tienda Vecina registrados..."

stop_pid_file() {
    local pid_file="$1"
    local name="$2"
    if [ -f "$pid_file" ]; then
        local pid
        pid="$(cat "$pid_file" 2>/dev/null || true)"
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "Deteniendo $name (PID $pid)..."
            kill -TERM "$pid" 2>/dev/null || true
            for _ in 1 2 3 4 5; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
        fi
        rm -f "$pid_file"
    fi
}

stop_pid_file "$DIR/backend.pid" "Backend Gunicorn"
stop_pid_file "$DIR/frontend.pid" "Frontend Vite"

echo "Servicios propios detenidos de forma segura."
