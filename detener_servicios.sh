#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Deteniendo procesos de Django y Vite/Node..."

if [ -f "$DIR/backend.pid" ]; then
    kill $(cat "$DIR/backend.pid") 2>/dev/null || true
    rm -f "$DIR/backend.pid"
fi

if [ -f "$DIR/frontend.pid" ]; then
    kill $(cat "$DIR/frontend.pid") 2>/dev/null || true
    rm -f "$DIR/frontend.pid"
fi

# Matar procesos remanentes en los puertos 8000 y 5173 si existen
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 5173/tcp 2>/dev/null || true

echo "Servidores detenidos."
